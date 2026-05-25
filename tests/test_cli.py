import json
import pytest
import yaml
from click.testing import CliRunner
from unittest.mock import MagicMock, patch


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


def test_config_set_valid(config_home):
    from paicer.cli import cli
    from paicer.config import read_config
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "units", "imperial"])
    assert result.exit_code == 0
    assert read_config()["units"] == "imperial"


def test_config_set_plan(config_home, tmp_path):
    from paicer.cli import cli
    from paicer.config import read_config
    plan = tmp_path / "plan.yaml"
    plan.write_text("plan: {}")
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "plan", str(plan)])
    assert result.exit_code == 0
    assert read_config()["plan"] == str(plan)


def test_config_set_invalid_key(config_home):
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "bogus_key", "value"])
    assert result.exit_code != 0


def test_config_set_invalid_value(config_home):
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "units", "furlongs"])
    assert result.exit_code != 0


def test_config_show_empty(config_home):
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "No config file found" in result.output


def test_config_show_with_values(config_home):
    from paicer.cli import cli
    from paicer.config import write_config
    runner = CliRunner()
    write_config({"units": "metric", "swim_tracking": "drill", "garmin_email": "x@y.com"})
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert "units = metric" in result.output
    assert "swim_tracking = drill" in result.output
    assert "garmin_email" not in result.output


def test_config_set_plan_nonexistent(config_home):
    from paicer.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "plan", "/nonexistent/plan.yaml"])
    assert result.exit_code != 0


# --- review command fixtures and helpers ---

@pytest.fixture
def review_plan(tmp_path):
    plan = {
        "plan": {"name": "Test", "start_date": "2026-01-05", "training_days": [1, 3], "overview": "Test."},
        "phases": [{"phase": 1, "name": "Base", "description": "Base.", "weeks": [
            {"week": 1, "description": "Week 1.", "workouts": [
                {"day": 1, "name": "Easy Run", "type": "run", "description": "Easy"},
                {"day": 2, "name": "Tempo 5km", "type": "run", "description": "Tempo"},
            ]}
        ]}]
    }
    f = tmp_path / "plan.yaml"
    f.write_text(yaml.dump(plan))
    return f


MOCK_ACTIVITY = {
    "activityId": 1234,
    "activityName": "W1: Easy Run",
    "activityType": {"typeKey": "running"},
    "startTimeLocal": "2026-01-05 08:00:00",
    "distance": 8000.0,
    "duration": 2400.0,
    "averageSpeed": 3.2,
    "averageHR": 140,
    "maxHR": 155,
    "averagePower": None,
    "maxPower": None,
    "elevationGain": 50.0,
    "elevationLoss": 50.0,
    "aerobicTrainingEffect": 2.5,
}

MOCK_SPLITS = {"splits": [
    {"type": "INTERVAL_WARMUP", "distance": 500, "duration": 180,
     "averageSpeed": 2.8, "averageHR": 130, "maxHR": 135, "averagePower": None},
    {"type": "INTERVAL_ACTIVE", "distance": 7500, "duration": 2220,
     "averageSpeed": 3.38, "averageHR": 142, "maxHR": 158, "averagePower": None},
    {"type": "RWD_WALK", "distance": 100, "duration": 60,
     "averageSpeed": 1.5, "averageHR": 120, "maxHR": 125, "averagePower": None},
]}


def _garmin_mock():
    client = MagicMock()
    client.get_activities_by_date.return_value = [MOCK_ACTIVITY]
    client.get_activity_typed_splits.return_value = MOCK_SPLITS
    client.get_training_status.return_value = {}
    instance = MagicMock()
    instance.client = client
    instance.swim_tracking = "auto"
    return instance


def test_review_week_scope(config_home, review_plan):
    from paicer.cli import cli
    runner = CliRunner()
    with patch("paicer.integrations.garmin.GarminIntegration", return_value=_garmin_mock()):
        result = runner.invoke(cli, ["review", "w1", "--plan", str(review_plan)])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["week"] == 1
    assert len(data["activities"]) == 1
    assert data["activities"][0]["activityName"] == "W1: Easy Run"
    # RWD_WALK noise should be filtered out of intervals
    intervals = data["activities"][0]["intervals"]
    assert all(i["type"].startswith("INTERVAL_") for i in intervals)
    assert len(intervals) == 2


def test_review_day_scope_matched(config_home, review_plan):
    from paicer.cli import cli
    runner = CliRunner()
    with patch("paicer.integrations.garmin.GarminIntegration", return_value=_garmin_mock()):
        result = runner.invoke(cli, ["review", "w1d1", "--plan", str(review_plan)])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["week"] == 1
    assert data["day"] == 1
    assert data["planned"]["name"] == "Easy Run"
    assert data["activity"]["activityName"] == "W1: Easy Run"


def test_review_day_scope_no_match(config_home, review_plan):
    from paicer.cli import cli
    runner = CliRunner()
    with patch("paicer.integrations.garmin.GarminIntegration", return_value=_garmin_mock()):
        result = runner.invoke(cli, ["review", "w1d2", "--plan", str(review_plan)])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["day"] == 2
    assert data["planned"]["name"] == "Tempo 5km"
    assert data["activity"] is None  # no Garmin activity matched


def test_review_invalid_scope(config_home, review_plan):
    from paicer.cli import cli
    runner = CliRunner()
    with patch("paicer.integrations.garmin.GarminIntegration", return_value=_garmin_mock()):
        result = runner.invoke(cli, ["review", "xyz", "--plan", str(review_plan)])
    assert result.exit_code != 0
