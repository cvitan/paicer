# PyPI Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure paicer into a proper Python package installable via `pip install paicer`, with a `paicer` CLI command and automated PyPI publishing via GitHub Actions.

**Architecture:** Move `src/*.py` scripts into a `src/paicer/` package. Add a Click-based CLI entry point. Replace `.env` config with `~/.paicer/config` (TOML) and keyring for Garmin credentials. GitHub Actions publishes to PyPI on version tags using OIDC Trusted Publishers.

**Tech Stack:** Python 3.12+, Click 8, keyring 24, hatchling (build backend), pytest, PyPI Trusted Publishers (OIDC), GitHub Actions

---

## File Map

**Create:**
- `src/paicer/__init__.py` — package marker
- `src/paicer/cli.py` — Click entry point (`paicer render`, `paicer sync`, `paicer version`)
- `src/paicer/config.py` — `~/.paicer/config` read/write + credential prompting
- `tests/__init__.py` — test package marker
- `tests/test_config.py` — unit tests for config.py
- `tests/test_cli.py` — CLI integration tests using Click test runner
- `.github/workflows/publish.yml` — PyPI publish on `v*` tag

**Move + update imports:**
- `src/plan_utils.py` → `src/paicer/plan_utils.py` (no import changes needed — no internal imports)
- `src/formatters/` → `src/paicer/formatters/` (fix `from plan_utils` → `from ..plan_utils`)
- `src/render_plan.py` → `src/paicer/render.py` (fix imports, extract `render_plan()` fn)
- `src/integrations/` → `src/paicer/integrations/` (remove dotenv, add keyring in garmin.py)
- `src/generate_workouts.py` → `src/paicer/sync.py` (fix imports, extract `run_sync()` fn, remove dotenv)
- `src/review_data.py` → `src/paicer/review_data.py` (fix imports, remove dotenv)

**Modify:**
- `pyproject.toml` — add hatchling backend, click + keyring deps, remove python-dotenv, add entry point, add pytest dev dep
- `Makefile` — replace `python src/*.py` calls with `paicer` CLI commands

---

### Task 1: Update pyproject.toml and create package skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `src/paicer/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write a failing import test**

Create `tests/__init__.py` (empty) and `tests/test_package.py`:

```python
def test_package_importable():
    import paicer
    assert paicer.__version__
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd /path/to/paicer
uv run pytest tests/test_package.py -v
```

Expected: `ModuleNotFoundError: No module named 'paicer'`

- [ ] **Step 3: Rewrite pyproject.toml**

```toml
[project]
name = "paicer"
version = "0.1.0"
description = "Training plan tool: YAML to Garmin workouts and readable documents"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "click>=8.0",
    "garminconnect>=0.2.40,<0.3.0",
    "keyring>=24.0",
    "markdown>=3.10.2",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.15.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/paicer"]

[project.scripts]
paicer = "paicer.cli:main"
```

- [ ] **Step 4: Create `src/paicer/__init__.py`**

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("paicer")
except PackageNotFoundError:
    __version__ = "dev"
```

- [ ] **Step 5: Install and run the test**

```bash
uv sync
uv run pytest tests/test_package.py -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/paicer/__init__.py tests/__init__.py tests/test_package.py uv.lock
git commit -m "chore: add package skeleton and update pyproject.toml"
```

---

### Task 2: Write config.py + tests

**Files:**
- Create: `src/paicer/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:

```python
import os
import pytest
from pathlib import Path


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    return tmp_path


def test_read_config_missing_returns_empty(config_home):
    from paicer.config import read_config
    assert read_config() == {}


def test_write_and_read_config(config_home):
    from paicer.config import read_config, write_config
    write_config({"plan": "/tmp/plan.yaml", "units": "metric"})
    cfg = read_config()
    assert cfg["plan"] == "/tmp/plan.yaml"
    assert cfg["units"] == "metric"


def test_get_units_default(config_home):
    from paicer.config import get_units
    assert get_units() == "metric"


def test_get_units_from_config(config_home):
    from paicer.config import get_units, write_config
    write_config({"units": "imperial"})
    assert get_units() == "imperial"


def test_get_plan_path_from_config(config_home):
    from paicer.config import get_plan_path, write_config
    write_config({"plan": "/tmp/myplan.yaml"})
    assert get_plan_path() == "/tmp/myplan.yaml"


def test_get_garmin_email(config_home):
    from paicer.config import get_garmin_email, write_config
    write_config({"garmin_email": "tom@example.com"})
    assert get_garmin_email() == "tom@example.com"


def test_get_garmin_email_missing(config_home):
    from paicer.config import get_garmin_email
    assert get_garmin_email() is None
```

- [ ] **Step 2: Run to confirm all fail**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all `FAILED` with `ModuleNotFoundError`

- [ ] **Step 3: Create `src/paicer/config.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all 7 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/paicer/config.py tests/test_config.py
git commit -m "feat: add config module for ~/.paicer/config management"
```

---

### Task 3: Move plan_utils and formatters, fix imports

**Files:**
- Move: `src/plan_utils.py` → `src/paicer/plan_utils.py`
- Move: `src/formatters/` → `src/paicer/formatters/`
- Modify: `src/paicer/formatters/markdown.py` (fix imports)
- Modify: `src/paicer/formatters/html.py` (fix imports)

- [ ] **Step 1: Move files**

```bash
git mv src/plan_utils.py src/paicer/plan_utils.py
git mv src/formatters src/paicer/formatters
```

- [ ] **Step 2: Fix imports in `src/paicer/formatters/markdown.py`**

Find the import block at the top of the file:
```python
from plan_utils import (
```
Change to:
```python
from ..plan_utils import (
```

- [ ] **Step 3: Fix imports in `src/paicer/formatters/html.py`**

Find the import block at the top of the file:
```python
from plan_utils import (
```
Change to:
```python
from ..plan_utils import (
```

- [ ] **Step 4: Verify imports resolve**

```bash
uv run python -c "from paicer.formatters.markdown import MarkdownFormatter; print('ok')"
uv run python -c "from paicer.formatters.html import HTMLFormatter; print('ok')"
```

Expected: both print `ok`

- [ ] **Step 5: Commit**

```bash
git add src/paicer/plan_utils.py src/paicer/formatters/
git commit -m "refactor: move plan_utils and formatters into paicer package"
```

---

### Task 4: Move render.py and extract render_plan function

**Files:**
- Move: `src/render_plan.py` → `src/paicer/render.py`

- [ ] **Step 1: Move the file**

```bash
git mv src/render_plan.py src/paicer/render.py
```

- [ ] **Step 2: Rewrite `src/paicer/render.py`**

Replace the entire file with:

```python
import sys
from .plan_utils import load_plan, validate_training_days
from .formatters.markdown import MarkdownFormatter
from .formatters.html import HTMLFormatter


def render_plan(plan_file: str, html: bool = False, paper_format: str = "a4") -> str:
    """Load plan and render to string. Raises SystemExit on validation errors."""
    data = load_plan(plan_file)
    errors = validate_training_days(data)
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if html:
        return HTMLFormatter(paper_format).render(data)
    return MarkdownFormatter().render(data)
```

- [ ] **Step 3: Verify import**

```bash
uv run python -c "from paicer.render import render_plan; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/paicer/render.py
git commit -m "refactor: move render_plan into paicer package"
```

---

### Task 5: Move integrations and update Garmin auth to use keyring

**Files:**
- Move: `src/integrations/` → `src/paicer/integrations/`
- Modify: `src/paicer/integrations/garmin.py` (remove dotenv, add keyring)

- [ ] **Step 1: Move integrations directory**

```bash
git mv src/integrations src/paicer/integrations
```

- [ ] **Step 2: Update imports in `src/paicer/integrations/garmin.py`**

Remove these lines near the top:
```python
from dotenv import load_dotenv
```
and:
```python
load_dotenv()
```

- [ ] **Step 3: Replace the `authenticate` method in `src/paicer/integrations/garmin.py`**

Find the existing `authenticate` method (it reads `GARMIN_EMAIL` and `GARMIN_PASSWORD` from env). Replace it with:

```python
def authenticate(self):
    import keyring
    import click
    from ..config import get_garmin_email, read_config, write_config

    email = get_garmin_email()
    if not email:
        email = click.prompt("Garmin email")
        cfg = read_config()
        cfg["garmin_email"] = email
        write_config(cfg)

    password = keyring.get_password("paicer", email)
    if not password:
        password = click.prompt(f"Garmin password for {email}", hide_input=True)
        keyring.set_password("paicer", email, password)

    self.client = GarminAPI(email, password)
    self.client.login()
```

- [ ] **Step 4: Verify import**

```bash
uv run python -c "from paicer.integrations.garmin import GarminIntegration; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add src/paicer/integrations/
git commit -m "refactor: move integrations into paicer package, switch Garmin auth to keyring"
```

---

### Task 6: Move sync.py and review_data.py, fix imports

**Files:**
- Move: `src/generate_workouts.py` → `src/paicer/sync.py`
- Move: `src/review_data.py` → `src/paicer/review_data.py`

- [ ] **Step 1: Move files**

```bash
git mv src/generate_workouts.py src/paicer/sync.py
git mv src/review_data.py src/paicer/review_data.py
```

- [ ] **Step 2: Rewrite `src/paicer/sync.py`**

Replace the entire file with (preserving the core logic, just updating imports and extracting a callable function):

```python
import os
import re
from .plan_utils import calculate_workout_date, load_plan, validate_training_days


def parse_filter(filter_str: str) -> tuple[int | None, int | None, int | None]:
    """Parse filter like 'p1', 'w7', 'w7d2', or 'all'."""
    if filter_str.lower() == "all":
        return None, None, None

    match = re.match(r"[pP](\d+)$", filter_str)
    if match:
        return int(match.group(1)), None, None

    match = re.match(r"[wW](\d+)(?:[dD](\d+))?$", filter_str)
    if match:
        week = int(match.group(1))
        day = int(match.group(2)) if match.group(2) else None
        return None, week, day

    raise ValueError(
        f"Invalid filter: {filter_str}. Use 'p1', 'w7', 'w7d2', or 'all'"
    )


def _get_integration(name: str):
    if name == "garmin":
        from .integrations.garmin import GarminIntegration
        return GarminIntegration()
    raise ValueError(f"Integration '{name}' not found")


def run_sync(plan_file: str, filter_str: str, no_schedule: bool = False) -> None:
    """Sync workouts from plan to the configured integration."""
    filter_phase, filter_week, filter_day = parse_filter(filter_str)

    data = load_plan(plan_file)
    errors = validate_training_days(data)
    if errors:
        for e in errors:
            print(f"Error: {e}")
        raise SystemExit(1)

    start_date = data["plan"]["start_date"]
    global_training_days = data["plan"].get("training_days", [1, 2, 3, 4, 5, 6, 7])

    integration_name = os.getenv("WORKOUT_INTEGRATION", "garmin").lower()
    integration = _get_integration(integration_name)
    integration.authenticate()

    uploaded_dates = []
    uploaded_names = []
    skipped_workouts = []

    for phase in data["phases"]:
        phase_num = phase["phase"]
        if filter_phase is not None and phase_num != filter_phase:
            continue

        phase_training_days = phase.get("training_days", global_training_days)

        for week_data in phase["weeks"]:
            week_num = week_data["week"]
            if filter_week is not None and week_num != filter_week:
                continue

            for workout in week_data["workouts"]:
                day_num = workout["day"]
                if filter_day is not None and day_num != filter_day:
                    continue

                if workout.get("skip_garmin") or "garmin" not in workout:
                    skipped_workouts.append(workout)
                    continue

                garmin_name = f"W{week_num}: {workout['name']}"
                is_optional = workout.get("optional", False)

                workout_date = None
                if not is_optional or day_num <= len(phase_training_days):
                    workout_date = calculate_workout_date(
                        start_date, week_num, day_num, phase_training_days
                    )

                if len(uploaded_names) == 0:
                    if filter_day:
                        print(f"Syncing {garmin_name}")
                    elif filter_week:
                        print(f"Syncing Week {filter_week}")
                    elif filter_phase:
                        print(f"Syncing Phase {filter_phase}")
                    else:
                        print("Syncing all workouts...")

                try:
                    integration.delete_workout(garmin_name)
                    garmin_workout = {**workout, "name": garmin_name}
                    workout_json = integration.build_workout(garmin_workout)
                    workout_id = integration.upload_workout(workout_json)

                    if not no_schedule and not is_optional and workout_date:
                        integration.schedule_workout(workout_id, workout_date)
                except Exception as e:
                    print(f"Error: {e}")
                    raise SystemExit(1)

                if workout_date and not is_optional:
                    uploaded_dates.append(workout_date)
                uploaded_names.append(garmin_name)

    if not uploaded_names:
        if skipped_workouts:
            for w in skipped_workouts:
                print(f"Skipped: {w['name']} (session set to skip Garmin sync)")
            return
        print("Error: No workouts found matching filter")
        raise SystemExit(1)

    count = len(uploaded_names)
    if no_schedule:
        if filter_day:
            print("✓ Uploaded to Garmin Connect")
        else:
            print(f"✓ Uploaded {count} workout{'s' if count > 1 else ''} to Garmin Connect")
    else:
        if filter_day and uploaded_dates:
            print(f"✓ Synced to Garmin Connect and scheduled for {uploaded_dates[0]}")
        elif filter_day:
            print("✓ Uploaded to Garmin Connect")
        elif filter_week or filter_phase:
            print(f"✓ Synced {count} workout{'s' if count > 1 else ''} to Garmin Connect")
        else:
            print("✓ Synced to Garmin Connect")
```

- [ ] **Step 3: Fix imports in `src/paicer/review_data.py`**

At the top of the file, find:
```python
from dotenv import load_dotenv

from integrations.garmin import GarminIntegration
from plan_utils import first_monday_on_or_after, load_plan
```
Replace with:
```python
from .integrations.garmin import GarminIntegration
from .plan_utils import first_monday_on_or_after, load_plan
```
Also remove any `load_dotenv()` call in the file body.

- [ ] **Step 4: Verify imports**

```bash
uv run python -c "from paicer.sync import run_sync, parse_filter; print('ok')"
uv run python -c "from paicer.review_data import *; print('ok')"
```

Expected: both print `ok`

- [ ] **Step 5: Commit**

```bash
git add src/paicer/sync.py src/paicer/review_data.py
git commit -m "refactor: move sync and review_data into paicer package"
```

---

### Task 7: Write CLI entry point + tests

**Files:**
- Create: `src/paicer/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
import pytest
from click.testing import CliRunner


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    return tmp_path


def test_version():
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "paicer" in result.output


def test_render_no_plan_configured(config_home):
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["render"], input="/nonexistent/path.yaml\n")
    # Should prompt for plan path; path doesn't exist so exits non-zero
    assert result.exit_code != 0


def test_render_with_plan_flag(config_home, tmp_path):
    from paicer.cli import cli
    import yaml

    plan = {
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1, 3]},
        "phases": [{"phase": 1, "weeks": [{"week": 1, "workouts": [
            {"day": 1, "name": "Easy run", "type": "run", "description": "Easy"},
        ]}]}]
    }
    plan_file = tmp_path / "plan.yaml"
    plan_file.write_text(yaml.dump(plan))

    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--plan", str(plan_file)])
    assert result.exit_code == 0
    assert "Easy run" in result.output


def test_render_html_with_plan_flag(config_home, tmp_path):
    from paicer.cli import cli
    import yaml

    plan = {
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1, 3]},
        "phases": [{"phase": 1, "weeks": [{"week": 1, "workouts": [
            {"day": 1, "name": "Easy run", "type": "run", "description": "Easy"},
        ]}]}]
    }
    plan_file = tmp_path / "plan.yaml"
    plan_file.write_text(yaml.dump(plan))

    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--html", "--plan", str(plan_file)])
    assert result.exit_code == 0
    assert "<html" in result.output.lower()


def test_render_output_flag(config_home, tmp_path):
    from paicer.cli import cli
    import yaml

    plan = {
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1]},
        "phases": [{"phase": 1, "weeks": [{"week": 1, "workouts": [
            {"day": 1, "name": "Run", "type": "run", "description": "Easy"},
        ]}]}]
    }
    plan_file = tmp_path / "plan.yaml"
    plan_file.write_text(yaml.dump(plan))
    out_file = tmp_path / "out.md"

    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--plan", str(plan_file), "-o", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    assert "Run" in out_file.read_text()


def test_sync_missing_scope():
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["sync"])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run to confirm all fail**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all `FAILED` with `ModuleNotFoundError` or import errors

- [ ] **Step 3: Create `src/paicer/cli.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests pass (including test_package, test_config, test_cli)

- [ ] **Step 6: Commit**

```bash
git add src/paicer/cli.py tests/test_cli.py
git commit -m "feat: add Click CLI entry point with render, sync, and version commands"
```

---

### Task 8: Update Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Replace `Makefile` content**

```makefile
.PHONY: install test workouts markdown html all clean

-include .env
export

UNITS ?= metric
FORMAT ?= $(if $(filter imperial,$(UNITS)),letter,a4)
SCHEDULE ?= 1

define check_plan
	@if [ -z "$(PLAN)" ]; then \
		echo "No plan set. Set PLAN in .env or run: paicer config"; \
		exit 1; \
	fi
	@if [ ! -f "$(PLAN)" ]; then \
		echo "Plan file not found: $(PLAN)"; \
		exit 1; \
	fi
endef

install:
	uv sync

test:
	$(check_plan)
	@echo "Running tests..."
	@uv run pytest -v
	@echo "Validating plan..."
	@uv run paicer render --plan $(PLAN) > /dev/null
	@echo "✅ Plan valid"

workouts:
	$(check_plan)
	@uv run paicer sync $(SCOPE) --plan $(PLAN) $(if $(filter 0,$(SCHEDULE)),--no-schedule)

markdown:
	$(check_plan)
	@mkdir -p output
	@uv run paicer render --plan $(PLAN) > output/training_plan.md
	@echo "Created output/training_plan.md"

html:
	$(check_plan)
	@mkdir -p output
	@uv run paicer render --html --format=$(FORMAT) --plan $(PLAN) > output/training_plan.html
	@echo "Created output/training_plan.html ($(FORMAT))"

all: markdown html

clean:
	trash output/
	trash __pycache__
```

- [ ] **Step 2: Verify make markdown still works (if you have a plan in .env)**

```bash
make markdown
```

Expected: `Created output/training_plan.md`

If no plan in `.env`, skip this step.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: update Makefile to use paicer CLI commands"
```

---

### Task 9: GitHub Actions publish workflow

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create `.github/workflows/` directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/publish.yml`**

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install hatchling build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: add PyPI publish workflow on version tags"
```

---

### Task 10: PyPI Trusted Publisher setup (manual, one-time)

This task is done in the browser, not in code.

- [ ] **Step 1: Create PyPI account** at https://pypi.org if you don't have one

- [ ] **Step 2: Create the project on PyPI**
  - Go to https://pypi.org/manage/account/publishing/
  - Click "Add a new pending publisher"
  - Fill in:
    - PyPI project name: `paicer`
    - GitHub owner: `<your-github-username>`
    - Repository name: `paicer`
    - Workflow filename: `publish.yml`
    - Environment name: `pypi`

- [ ] **Step 3: Create the `pypi` environment in GitHub**
  - Go to your repo → Settings → Environments → New environment
  - Name it `pypi`
  - No secrets needed — OIDC handles auth

- [ ] **Step 4: Test the pipeline**

  Bump version in `pyproject.toml` to `0.1.0` (or whatever is appropriate), then:

  ```bash
  git add pyproject.toml
  git commit -m "chore: release v0.1.0"
  git tag v0.1.0
  git push && git push --tags
  ```

  Watch the Actions tab — the publish job should succeed and `paicer` should appear on PyPI within a minute.

---

### Task 11: Delete old source files

After all tasks pass and the CLI works end-to-end, remove the now-empty `src/` root scripts (they were moved in Tasks 3-6, so they should already be gone via `git mv`). Verify nothing is left:

- [ ] **Step 1: Check src/ for leftover files**

```bash
ls src/
```

Expected: only `src/paicer/` directory. If any old `.py` files remain (from a failed `git mv`), delete them:

```bash
git rm src/render_plan.py src/generate_workouts.py src/plan_utils.py src/review_data.py 2>/dev/null || true
git commit -m "chore: remove old src root scripts (moved to paicer package)"
```

- [ ] **Step 2: Final test run**

```bash
uv run pytest -v
uv run paicer version
uv run paicer render --help
uv run paicer sync --help
```

Expected: all tests pass, all commands show correct output/help text.
