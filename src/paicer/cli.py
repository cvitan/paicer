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
@click.option("-o", "--output", type=click.Path(), default=None, help="Write to file instead of stdout")
@click.option("--plan", "plan_path", type=click.Path(exists=True), default=None, help="Path to plan YAML (overrides config)")
def render(html, fmt, output, plan_path):
    """Render training plan to Markdown or HTML."""
    from .config import get_plan_path, get_format, prompt_and_save_plan_path
    from .render import render_plan

    if plan_path is None:
        plan_path = get_plan_path()
    if plan_path is None:
        plan_path = prompt_and_save_plan_path()

    if fmt is None:
        fmt = get_format()

    result = render_plan(plan_path, html=html, paper_format=fmt)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


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


def main():
    cli()
