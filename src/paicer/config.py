import os
import tomllib
from pathlib import Path


def _config_path() -> Path:
    home = os.environ.get("PAICER_HOME")
    base = Path(home) if home else Path.home() / ".paicer"
    return base / "config"


def read_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def write_config(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{k} = "{v}"' for k, v in data.items()]
    path.write_text("\n".join(lines) + "\n")


def get_plan_path() -> str | None:
    return read_config().get("plan")


def get_units() -> str:
    return read_config().get("units", "metric")


def get_garmin_email() -> str | None:
    return read_config().get("garmin_email")


def prompt_and_save_plan_path() -> str:
    import click
    plan = click.prompt("Path to your plan YAML file")
    cfg = read_config()
    cfg["plan"] = plan
    write_config(cfg)
    return plan
