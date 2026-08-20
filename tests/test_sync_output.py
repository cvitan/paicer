"""Sync CLI output — what the user sees on stdout."""

import pytest
import yaml
from unittest.mock import MagicMock, patch


def _plan(workouts):
    return {
        "plan": {"name": "T", "start_date": "2026-01-05", "overview": "x",
                 "training_days": [1, 2, 3]},
        "phases": [{"phase": 1, "name": "P", "description": "d",
                    "weeks": [{"week": 5, "description": "d",
                               "workouts": workouts}]}],
    }


RUN = {
    "day": 3, "type": "run", "name": "Marathon Pace 3x1.5 mi",
    "description": "d",
    "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "distance",
         "endConditionValue": 5000, "targetType": "heart.rate.zone",
         "zoneNumber": 2},
    ]},
}

LIFT = {
    "day": 3, "type": "strength", "name": "Upper A 3x8", "description": "d",
    "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "reps",
         "endConditionValue": 8, "targetType": "no.target",
         "category": "BENCH_PRESS", "exerciseName": "BARBELL_BENCH_PRESS"},
    ]},
}


@pytest.fixture
def run_sync(tmp_path, monkeypatch):
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))

    def _go(workouts, scope, no_schedule=False):
        path = tmp_path / "p.yaml"
        path.write_text(yaml.safe_dump(_plan(workouts)))
        from paicer.sync import run_sync as rs
        integration = MagicMock()
        integration.upload_workout.return_value = "123"
        with patch("paicer.sync._get_integration", return_value=integration):
            rs(str(path), scope, no_schedule)
    return _go


def test_day_with_two_sessions_names_both(run_sync, capsys):
    """A run and a lift on the same day must both be listed."""
    run_sync([RUN, LIFT], "w5d3")
    out = capsys.readouterr().out
    assert "Syncing W5: Marathon Pace 3x1.5 mi" in out
    assert "Syncing W5: Upper A 3x8" in out


def test_day_with_two_sessions_reports_count(run_sync, capsys):
    run_sync([RUN, LIFT], "w5d3")
    out = capsys.readouterr().out
    assert "✓ Synced 2 workouts to Garmin Connect and scheduled for" in out


def test_single_session_day_output_unchanged(run_sync, capsys):
    """The common case must read exactly as it did before."""
    run_sync([RUN], "w5d3")
    out = capsys.readouterr().out
    assert "Syncing W5: Marathon Pace 3x1.5 mi" in out
    assert "✓ Synced to Garmin Connect and scheduled for" in out
    assert "1 workout" not in out


def test_no_schedule_day_with_two_sessions(run_sync, capsys):
    run_sync([RUN, LIFT], "w5d3", no_schedule=True)
    out = capsys.readouterr().out
    assert out.count("Syncing W5:") == 2
    assert "✓ Uploaded 2 workouts to Garmin Connect" in out


def test_week_scope_still_prints_one_header(run_sync, capsys):
    """Wider scopes keep the single header plus a count."""
    run_sync([RUN, LIFT], "w5")
    out = capsys.readouterr().out
    assert out.count("Syncing Week 5") == 1
    assert "Syncing W5: Upper A 3x8" not in out
    assert "✓ Synced 2 workouts to Garmin Connect" in out
