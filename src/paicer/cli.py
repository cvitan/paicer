import click
from . import __version__


VALID_KEYS = {
    "plan": (str, None),
    "units": (str, ["metric", "imperial"]),
    "format": (str, ["a4", "letter"]),
    "swim_tracking": (str, ["auto", "drill"]),
}


@click.group()
def cli():
    """Paicer — training plan tool."""
    pass


@cli.command()
def version():
    """Show paicer version."""
    click.echo(f"paicer {__version__}")


@cli.group()
def config():
    """View or update paicer configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value.

    Keys: plan, units (metric/imperial), format (a4/letter), swim_tracking (auto/drill)
    """
    from pathlib import Path
    from .config import read_config, write_config
    if key not in VALID_KEYS:
        raise click.BadParameter(f"Unknown key '{key}'. Valid keys: {', '.join(VALID_KEYS)}")
    _, allowed = VALID_KEYS[key]
    if allowed and value not in allowed:
        raise click.BadParameter(f"Invalid value '{value}' for '{key}'. Allowed: {', '.join(allowed)}")
    if key == "plan":
        p = Path(value).expanduser()
        if not p.exists() or p.is_dir():
            raise click.BadParameter(f"Not a valid file path: {value}")
        value = str(p.resolve())
    cfg = read_config()
    cfg[key] = value
    write_config(cfg)
    click.echo(f"{key} = {value}")


@config.command("show")
def config_show():
    """Show current configuration."""
    from .config import read_config, _config_path
    path = _config_path()
    if not path.exists():
        click.echo("No config file found.")
        return
    for k, v in read_config().items():
        if k in VALID_KEYS:
            click.echo(f"{k} = {v}")


@cli.command()
@click.option("--html", is_flag=True, help="Render as HTML instead of Markdown")
@click.option(
    "--format", "fmt",
    type=click.Choice(["a4", "letter"]),
    default=None,
    help="Paper format for HTML output (default: a4 for metric, letter for imperial)",
)
@click.option("-o", "--output", type=click.Path(), default=None, help="Output path (default: <plan_dir>/<plan_stem>.md/.html)")
@click.option("--plan", "plan_path", type=click.Path(exists=True), default=None, help="Path to plan YAML (overrides config)")
def render(html, fmt, output, plan_path):
    """Render training plan to Markdown or HTML. Writes next to the plan file by default; echoes the output path."""
    from .config import get_plan_path, get_format, prompt_and_save_plan_path
    from .render import render_plan

    if plan_path is None:
        plan_path = get_plan_path()
    if plan_path is None:
        plan_path = prompt_and_save_plan_path()

    if fmt is None:
        fmt = get_format()

    result = render_plan(plan_path, html=html, paper_format=fmt)

    if output is None:
        from pathlib import Path
        stem = Path(plan_path).stem
        ext = ".html" if html else ".md"
        output = str(Path(plan_path).parent / (stem + ext))

    with open(output, "w", encoding="utf-8") as f:
        f.write(result)
    click.echo(output)


@cli.command()
@click.argument("scope")
@click.option("--no-schedule", is_flag=True, help="Upload to library only, skip calendar scheduling")
@click.option("--plan", "plan_path", type=click.Path(exists=True), default=None, help="Path to plan YAML (overrides config)")
def sync(scope, no_schedule, plan_path):
    """Sync workouts to Garmin Connect.

    SCOPE: p1 (phase 1), w7 (week 7), w7d2 (week 7 day 2), or all
    """
    from .config import get_plan_path, prompt_and_save_plan_path
    from .sync import run_sync

    if plan_path is None:
        plan_path = get_plan_path()
    if plan_path is None:
        plan_path = prompt_and_save_plan_path()

    run_sync(plan_path, scope, no_schedule)


@cli.command()
@click.option("--search", "term", default=None, help="Find exercises matching a substring")
@click.option("--category", "category", default=None, help="List all exercises in one category")
def exercises(term, category):
    """Look up Garmin strength exercise names.

    Plan YAML needs exact category/exerciseName strings. With no options,
    lists every category and its exercise count.
    """
    from .exercises import categories, exercises_in, load_catalog, search

    if term and category:
        raise click.BadParameter("Use --search or --category, not both.")

    if term:
        results = search(term)
        if not results:
            raise click.ClickException(f"No exercises matching '{term}'.")
        for cat, name in results:
            click.echo(f"{cat}/{name}")
        return

    if category:
        names = exercises_in(category)
        if not names:
            from .exercises import _closest
            hint = _closest(category.upper(), categories())
            raise click.ClickException(f"Unknown category '{category}'{hint}")
        for name in names:
            click.echo(f"{category.upper()}/{name}")
        return

    catalog = load_catalog()
    for cat in categories():
        click.echo(f"{cat} ({len(catalog[cat])})")


@cli.command()
@click.argument("scope", required=False, default=None, metavar="[SCOPE]")
@click.option("--plan", "plan_path", type=click.Path(exists=True), default=None, help="Path to plan YAML (overrides config)")
def review(scope, plan_path):
    """Fetch Garmin activity data for a plan week or individual workout.

    SCOPE examples: w3 (week 3), w3d2 (week 3 day 2).
    Defaults to the most recently completed week.
    Outputs JSON to stdout.
    """
    import json
    import re
    from .config import get_plan_path, prompt_and_save_plan_path
    from .review_data import (
        find_current_week, get_week_dates, get_planned_workouts,
        get_activity_intervals, get_activity_exercise_sets,
        extract_training_status,
    )
    from .config import get_units
    from .plan_utils import load_plan
    from .integrations.garmin import GarminIntegration

    if plan_path is None:
        plan_path = get_plan_path()
    if plan_path is None:
        plan_path = prompt_and_save_plan_path()

    plan_data = load_plan(plan_path)
    start_date = plan_data["plan"]["start_date"]

    week_num = None
    day_num = None
    if scope:
        m = re.fullmatch(r"w(\d+)(?:d(\d+))?", scope, re.IGNORECASE)
        if not m:
            raise click.BadParameter(f"Invalid scope '{scope}'. Use w3 or w3d2.")
        week_num = int(m.group(1))
        if week_num < 1:
            raise click.BadParameter(f"Week number must be >= 1, got {week_num}.")
        day_num = int(m.group(2)) if m.group(2) else None

    if week_num is None:
        week_num = find_current_week(start_date)

    week_start, week_end, search_start, search_end = get_week_dates(start_date, week_num)
    planned = get_planned_workouts(plan_data, week_num)

    try:
        garmin = GarminIntegration()
        garmin.authenticate()
        activities = garmin.client.get_activities_by_date(
            search_start.strftime("%Y-%m-%d"),
            search_end.strftime("%Y-%m-%d"),
        )
    except Exception as e:
        raise click.ClickException(f"Failed to fetch Garmin data: {e}")

    units = get_units()
    activity_data = []
    for a in activities:
        activity_id = a.get("activityId")
        activity_type = a.get("activityType", {}).get("typeKey", "unknown")
        entry = {
            "activityName": a.get("activityName"),
            "activityType": activity_type,
            "startTimeLocal": a.get("startTimeLocal"),
            "distance": a.get("distance"),
            "duration": a.get("duration"),
            "averageSpeed": a.get("averageSpeed"),
            "averageHR": a.get("averageHR"),
            "maxHR": a.get("maxHR"),
            "averagePower": a.get("averagePower"),
            "maxPower": a.get("maxPower"),
            "elevationGain": a.get("elevationGain"),
            "elevationLoss": a.get("elevationLoss"),
            "aerobicTrainingEffect": a.get("aerobicTrainingEffect"),
            "hrTimeInZones": {
                f"zone{i}": a.get(f"hrTimeInZone_{i}")
                for i in range(1, 6)
                if a.get(f"hrTimeInZone_{i}") is not None
            },
        }
        if activity_id:
            if activity_type == "strength_training":
                entry["exerciseSets"] = get_activity_exercise_sets(
                    garmin, activity_id, units,
                )
            else:
                entry["intervals"] = get_activity_intervals(
                    garmin, activity_id,
                )
        activity_data.append(entry)

    training_status = {}
    try:
        status = garmin.client.get_training_status(week_end.strftime("%Y-%m-%d"))
        training_status = extract_training_status(status)
    except Exception as e:
        click.echo(f"Warning: failed to fetch training status: {e}", err=True)

    output = {
        "week": week_num,
        "week_dates": {
            "start": week_start.strftime("%Y-%m-%d"),
            "end": week_end.strftime("%Y-%m-%d"),
        },
        "planned": planned,
        "activities": activity_data,
        "trainingStatus": training_status,
    }

    if day_num is not None:
        matching = [w for w in planned if w.get("day") == day_num]
        if not matching:
            raise click.BadParameter(f"No workout found for day {day_num} in week {week_num}.")
        target = matching[0]
        prefix = f"W{week_num}: {target['name']}"
        matched = next((a for a in activity_data if a.get("activityName") == prefix), None)
        output = {
            "week": week_num,
            "day": day_num,
            "planned": target,
            "activity": matched,
        }

    click.echo(json.dumps(output, indent=2))


def main():
    cli()
