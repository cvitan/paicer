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
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1, 3], "overview": "Test overview."},
        "phases": [{"phase": 1, "name": "Base", "description": "Base phase.", "weeks": [{"week": 1, "description": "Week 1.", "workouts": [
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
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1, 3], "overview": "Test overview."},
        "phases": [{"phase": 1, "name": "Base", "description": "Base phase.", "weeks": [{"week": 1, "description": "Week 1.", "workouts": [
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
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1], "overview": "Test overview."},
        "phases": [{"phase": 1, "name": "Base", "description": "Base phase.", "weeks": [{"week": 1, "description": "Week 1.", "workouts": [
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
