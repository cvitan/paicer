import click
from . import __version__


@click.group()
def cli():
    """Paicer — training plan tool."""
    pass


@cli.command()
def version():
    """Show paicer version."""
    click.echo(f"paicer {__version__}")


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
    from .config import get_plan_path, get_units, prompt_and_save_plan_path
    from .render import render_plan

    if plan_path is None:
        plan_path = get_plan_path()
    if plan_path is None:
        plan_path = prompt_and_save_plan_path()

    if fmt is None:
        fmt = "letter" if get_units() == "imperial" else "a4"

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
