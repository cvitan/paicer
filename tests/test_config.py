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
