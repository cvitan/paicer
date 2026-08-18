"""Strength training: step building, catalog validation, review parsing."""

import pytest


@pytest.fixture
def integration(monkeypatch, tmp_path):
    """A GarminIntegration with config isolated to a temp dir."""
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    from paicer.integrations.garmin import GarminIntegration
    return GarminIntegration()


STRENGTH_WORKOUT = {
    "name": "Upper Push",
    "type": "strength",
    "description": "Chest and shoulders",
    "garmin": {"steps": [
        {"numberOfIterations": 3, "stepType": "repeat", "childStepId": 1,
         "steps": [
             {"stepType": "interval", "endCondition": "reps",
              "endConditionValue": 8, "targetType": "no.target",
              "childStepId": 1, "category": "BENCH_PRESS",
              "exerciseName": "BARBELL_BENCH_PRESS"},
             {"stepType": "rest", "endCondition": "time",
              "endConditionValue": 90, "childStepId": 1},
         ]},
    ]},
}


def _flatten(steps):
    for s in steps:
        if s.get("type") == "RepeatGroupDTO":
            yield from _flatten(s["workoutSteps"])
        else:
            yield s


# --- step building ---------------------------------------------------------

def test_sport_type_is_strength_training(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    assert built["sportType"]["sportTypeId"] == 5
    assert built["sportType"]["sportTypeKey"] == "strength_training"


def test_reps_end_condition_id(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    work = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 3)
    assert work["endCondition"]["conditionTypeId"] == 10
    assert work["endConditionValue"] == 8


def test_exercise_identity_forwarded(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    work = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 3)
    assert work["category"] == "BENCH_PRESS"
    assert work["exerciseName"] == "BARBELL_BENCH_PRESS"


def test_work_step_uses_no_target(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    work = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 3)
    assert work["targetType"]["workoutTargetTypeId"] == 1


def test_rest_step_target_type_is_null(integration):
    """Connect emits null, not no.target, for strength rest steps."""
    built = integration.build_workout(STRENGTH_WORKOUT)
    rest = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 5)
    assert rest["targetType"] is None


def test_rest_step_needs_no_target_type_in_yaml(integration):
    """The builder applies the null rule, so YAML omits targetType."""
    workout = {"name": "x", "type": "strength", "garmin": {"steps": [
        {"stepType": "rest", "endCondition": "time", "endConditionValue": 60},
    ]}}
    built = integration.build_workout(workout)
    assert built["workoutSegments"][0]["workoutSteps"][0]["targetType"] is None


def test_rest_step_carries_no_exercise(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    rest = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 5)
    assert "category" not in rest
    assert "exerciseName" not in rest


def test_repeat_group_structure_preserved(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    top = built["workoutSegments"][0]["workoutSteps"][0]
    assert top["type"] == "RepeatGroupDTO"
    assert top["numberOfIterations"] == 3
    assert len(top["workoutSteps"]) == 2


def test_weight_omitted_by_default(integration):
    built = integration.build_workout(STRENGTH_WORKOUT)
    work = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 3)
    assert work["weightValue"] is None
    assert work["weightUnit"]["unitKey"] == "kilogram"


def test_weight_converted_to_grams(integration):
    """Garmin stores weight in grams; YAML is written in the user's unit."""
    workout = {"name": "x", "type": "strength", "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "reps", "endConditionValue": 5,
         "targetType": "no.target", "category": "SQUAT",
         "exerciseName": "BARBELL_BACK_SQUAT", "weightValue": 60},
    ]}}
    built = integration.build_workout(workout)
    step = built["workoutSegments"][0]["workoutSteps"][0]
    assert step["weightValue"] == 60000.0


def test_imperial_weight_unit(monkeypatch, tmp_path):
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    from paicer.config import write_config
    write_config({"units": "imperial"})
    from paicer.integrations.garmin import GarminIntegration
    built = GarminIntegration().build_workout(STRENGTH_WORKOUT)
    work = next(s for s in _flatten(built["workoutSegments"][0]["workoutSteps"])
                if s["stepType"]["stepTypeId"] == 3)
    assert work["weightUnit"]["unitKey"] == "pound"
    assert work["weightUnit"]["unitId"] == 9


def test_other_sports_get_no_strength_fields(integration):
    """Running steps must not sprout weightUnit."""
    workout = {"name": "Easy", "type": "run", "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "distance",
         "endConditionValue": 5000, "targetType": "heart.rate.zone",
         "zoneNumber": 2},
    ]}}
    built = integration.build_workout(workout)
    assert "weightUnit" not in built["workoutSegments"][0]["workoutSteps"][0]


# --- catalog ---------------------------------------------------------------

def test_catalog_loads():
    from paicer.exercises import load_catalog
    catalog = load_catalog()
    assert len(catalog) == 51
    assert sum(len(v) for v in catalog.values()) == 1846


def test_known_pairs_validate():
    """Pairs taken from a real Garmin strength workout."""
    from paicer.exercises import validate
    for category, name in [
        ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
        ("BENCH_PRESS", "PARTIAL_LOCKOUT"),
        ("FLYE", "DUMBBELL_FLYE"),
        ("ROW", "REVERSE_GRIP_BARBELL_ROW"),
        ("SQUAT", "BARBELL_BACK_SQUAT"),
        ("SHOULDER_PRESS", "SMITH_MACHINE_OVERHEAD_PRESS"),
        ("CURL", "BARBELL_BICEPS_CURL"),
        ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    ]:
        assert validate(category, name) is None, f"{category}/{name}"


def test_unknown_exercise_suggests_near_match():
    from paicer.exercises import validate
    problem = validate("SQUAT", "BARBELL_BACK_SQUATS")
    assert problem is not None
    assert "BARBELL_BACK_SQUAT" in problem


def test_unknown_category_suggests_near_match():
    from paicer.exercises import validate
    problem = validate("SQUATT", "BARBELL_BACK_SQUAT")
    assert problem is not None
    assert "SQUAT" in problem


def test_right_name_wrong_category_is_caught():
    """Garmin accepts this silently and then ignores it on the watch."""
    from paicer.exercises import validate
    problem = validate("SQUAT", "BARBELL_BENCH_PRESS")
    assert problem is not None
    assert "BENCH_PRESS" in problem


def test_search_matches_substring():
    from paicer.exercises import search
    results = search("bench_press")
    assert ("BENCH_PRESS", "BARBELL_BENCH_PRESS") in results


def test_search_is_case_insensitive():
    from paicer.exercises import search
    assert search("Bench Press") == search("BENCH_PRESS")


def test_humanize():
    from paicer.exercises import humanize
    assert humanize("BARBELL_BENCH_PRESS") == "Barbell Bench Press"


# --- plan validation -------------------------------------------------------

def _plan_with(steps):
    return {"phases": [{"phase": 1, "weeks": [{"week": 3, "workouts": [
        {"day": 1, "type": "strength", "name": "Upper Push",
         "garmin": {"steps": steps}},
    ]}]}]}


def test_plan_validation_passes_for_valid_exercises():
    from paicer.plan_utils import validate_strength_exercises
    plan = _plan_with([
        {"stepType": "interval", "endCondition": "reps", "endConditionValue": 8,
         "targetType": "no.target", "category": "BENCH_PRESS",
         "exerciseName": "BARBELL_BENCH_PRESS"},
    ])
    assert validate_strength_exercises(plan) == []


def test_plan_validation_reports_bad_exercise_with_context():
    from paicer.plan_utils import validate_strength_exercises
    plan = _plan_with([
        {"stepType": "interval", "endCondition": "reps", "endConditionValue": 8,
         "targetType": "no.target", "category": "SQUAT",
         "exerciseName": "BARBELL_BACK_SQUATS"},
    ])
    errors = validate_strength_exercises(plan)
    assert len(errors) == 1
    assert "Week 3" in errors[0]
    assert "Upper Push" in errors[0]
    assert "BARBELL_BACK_SQUAT" in errors[0]


def test_plan_validation_descends_into_repeat_groups():
    from paicer.plan_utils import validate_strength_exercises
    plan = _plan_with([
        {"numberOfIterations": 3, "stepType": "repeat", "steps": [
            {"stepType": "interval", "endCondition": "reps",
             "endConditionValue": 8, "targetType": "no.target",
             "category": "SQUAT", "exerciseName": "NOT_A_REAL_LIFT"},
        ]},
    ])
    assert len(validate_strength_exercises(plan)) == 1


def test_plan_validation_ignores_rest_steps():
    from paicer.plan_utils import validate_strength_exercises
    plan = _plan_with([
        {"stepType": "rest", "endCondition": "time", "endConditionValue": 60},
    ])
    assert validate_strength_exercises(plan) == []


def test_plan_validation_requires_both_fields():
    from paicer.plan_utils import validate_strength_exercises
    plan = _plan_with([
        {"stepType": "interval", "endCondition": "reps", "endConditionValue": 8,
         "targetType": "no.target", "exerciseName": "BARBELL_BACK_SQUAT"},
    ])
    errors = validate_strength_exercises(plan)
    assert len(errors) == 1
    assert "category" in errors[0]


def test_plan_validation_skips_non_strength_workouts():
    from paicer.plan_utils import validate_strength_exercises
    plan = {"phases": [{"phase": 1, "weeks": [{"week": 1, "workouts": [
        {"day": 1, "type": "run", "name": "Easy", "garmin": {"steps": [
            {"stepType": "interval", "category": "NONSENSE"},
        ]}},
    ]}]}]}
    assert validate_strength_exercises(plan) == []


# --- review normalization --------------------------------------------------
# Fixture captured verbatim from a real Garmin response on 2026-08-18
# (activity logged specifically to pin this shape down).

REAL_SETS = {"activityId": 1, "exerciseSets": [
    # Warmup — a fumbled activity start. The only entry in the real
    # response with differing confidences, and all candidates are UNKNOWN,
    # so it is dropped regardless of which one is picked.
    {"exercises": [{"category": "UNKNOWN", "name": None, "probability": 99.6},
                   {"category": "UNKNOWN", "name": None, "probability": 0.0},
                   {"category": "UNKNOWN", "name": None, "probability": 0.0}],
     "duration": 6.3, "repetitionCount": 0, "weight": None,
     "setType": "ACTIVE", "wktStepIndex": 0, "messageIndex": 0},
    # A set the watch failed to count reps on, weight 0.0 not null.
    {"exercises": [{"category": "SQUAT", "name": "BARBELL_BACK_SQUAT",
                    "probability": 99.609375}] * 3,
     "duration": 22.7, "repetitionCount": 0, "weight": 0.0,
     "setType": "ACTIVE", "wktStepIndex": 1, "messageIndex": 1},
    {"exercises": [], "duration": 43.0, "repetitionCount": None,
     "weight": None, "setType": "REST", "wktStepIndex": 2, "messageIndex": 2},
    # A good set: 22687 g is exactly 50.0 lb.
    {"exercises": [{"category": "SQUAT", "name": "BARBELL_BACK_SQUAT",
                    "probability": 99.609375}] * 3,
     "duration": 19.9, "repetitionCount": 8, "weight": 22687.0,
     "setType": "ACTIVE", "wktStepIndex": 1, "messageIndex": 3},
    # Time-based exercise: reps is null, not zero.
    {"exercises": [{"category": "PLANK", "name": "PLANK",
                    "probability": 99.609375}] * 3,
     "duration": 2.1, "repetitionCount": None, "weight": None,
     "setType": "ACTIVE", "wktStepIndex": 12, "messageIndex": 25},
    # Trailing unclassified block after the workout ended.
    {"exercises": [{"category": "UNKNOWN", "name": None,
                    "probability": 98.8}],
     "duration": 11.4, "repetitionCount": None, "weight": None,
     "setType": "ACTIVE", "wktStepIndex": None, "messageIndex": 32},
]}


def test_real_response_drops_rest_and_unknown_blocks():
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "imperial")
    assert len(out) == 3
    assert all(r["exerciseName"] for r in out)
    assert not any(r["category"] == "UNKNOWN" for r in out)


def test_real_response_weight_grams_to_pounds():
    """22687 g is exactly 50 lb — confirms Garmin's base unit is grams."""
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "imperial")
    good = next(r for r in out if r["reps"] == 8)
    assert good["weight"] == 50.0
    assert good["weightUnit"] == "lb"


def test_real_response_weight_grams_to_kg():
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "metric")
    good = next(r for r in out if r["reps"] == 8)
    assert good["weight"] == 22.7
    assert good["weightUnit"] == "kg"


def test_zero_weight_reads_as_none():
    """weight 0.0 means nothing recorded, not zero kilograms."""
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "imperial")
    uncounted = next(r for r in out if r["reps"] == 0)
    assert uncounted["weight"] is None


def test_wkt_step_index_preserved():
    """Links a logged set back to the planned workout step."""
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "imperial")
    assert [r["wktStepIndex"] for r in out] == [1, 1, 12]


def test_time_based_exercise_has_null_reps():
    from paicer.review_data import normalize_exercise_sets
    out = normalize_exercise_sets(REAL_SETS, "imperial")
    plank = next(r for r in out if r["exerciseName"] == "PLANK")
    assert plank["reps"] is None
    assert plank["duration"] == 2.1


def test_highest_confidence_candidate_wins():
    """Defensive, not observed: in the one real response captured, every
    working set had identical candidates and the highest confidence was
    already first. Nothing documents that Garmin sorts the array, so the
    parser picks by probability rather than relying on order."""
    from paicer.review_data import normalize_exercise_sets
    data = {"exerciseSets": [{
        "setType": "ACTIVE", "repetitionCount": 5, "weight": None,
        "exercises": [
            {"category": "SQUAT", "name": "AIR_SQUAT", "probability": 12.0},
            {"category": "SQUAT", "name": "BARBELL_BACK_SQUAT",
             "probability": 88.0},
        ]}]}
    out = normalize_exercise_sets(data)
    assert out[0]["exerciseName"] == "BARBELL_BACK_SQUAT"
    assert out[0]["confidence"] == 88.0


def test_normalize_tolerates_bare_list():
    from paicer.review_data import normalize_exercise_sets
    data = [{"setType": "ACTIVE", "repetitionCount": 10,
             "exercises": [{"category": "PLANK", "name": "PLANK",
                            "probability": 99.0}]}]
    assert normalize_exercise_sets(data)[0]["reps"] == 10


def test_normalize_tolerates_garbage():
    from paicer.review_data import normalize_exercise_sets
    assert normalize_exercise_sets(None) == []
    assert normalize_exercise_sets("nonsense") == []
    assert normalize_exercise_sets({}) == []
    assert normalize_exercise_sets({"exerciseSets": [None, 5]}) == []


# --- CLI -------------------------------------------------------------------

def test_exercises_lists_categories():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(cli, ["exercises"])
    assert result.exit_code == 0
    assert "SQUAT (" in result.output
    assert len(result.output.strip().splitlines()) == 51


def test_exercises_search():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(cli, ["exercises", "--search", "bench_press"])
    assert result.exit_code == 0
    assert "BENCH_PRESS/BARBELL_BENCH_PRESS" in result.output


def test_exercises_search_no_match_errors():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(cli, ["exercises", "--search", "zzzznope"])
    assert result.exit_code != 0


def test_exercises_category():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(cli, ["exercises", "--category", "squat"])
    assert result.exit_code == 0
    assert "SQUAT/BARBELL_BACK_SQUAT" in result.output


def test_exercises_unknown_category_suggests():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(cli, ["exercises", "--category", "SQUATT"])
    assert result.exit_code != 0
    assert "SQUAT" in result.output


def test_exercises_rejects_both_flags():
    from click.testing import CliRunner
    from paicer.cli import cli
    result = CliRunner().invoke(
        cli, ["exercises", "--search", "a", "--category", "SQUAT"]
    )
    assert result.exit_code != 0


# --- render integration ----------------------------------------------------

def test_render_rejects_invalid_exercise(tmp_path, monkeypatch):
    """A bad exercise name must fail the render, not upload silently."""
    import yaml
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    from paicer.render import render_plan

    plan = {
        "plan": {"name": "T", "start_date": "2026-01-05", "overview": "x",
                 "training_days": [1]},
        "phases": [{"phase": 1, "name": "Base", "description": "d",
                    "weeks": [{"week": 1, "description": "d", "workouts": [
                        {"day": 1, "type": "strength", "name": "Lift",
                         "description": "d", "garmin": {"steps": [
                             {"stepType": "interval", "endCondition": "reps",
                              "endConditionValue": 8, "targetType": "no.target",
                              "category": "SQUAT",
                              "exerciseName": "NOT_A_REAL_LIFT"},
                         ]}},
                    ]}]}],
    }
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(plan))

    with pytest.raises(SystemExit):
        render_plan(str(path))


# --- example plan ----------------------------------------------------------

def test_example_strength_plan_is_valid(monkeypatch, tmp_path):
    """examples/strength-8week.yaml must stay valid as the catalog changes."""
    import yaml
    from pathlib import Path
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    from paicer.plan_utils import (
        validate_strength_exercises, validate_training_days,
    )

    path = Path(__file__).parent.parent / "examples" / "strength-8week.yaml"
    plan = yaml.safe_load(path.read_text())
    assert validate_training_days(plan) == []
    assert validate_strength_exercises(plan) == []


def test_example_strength_plan_builds_garmin_json(monkeypatch, tmp_path):
    """Every workout must produce uploadable JSON with aligned childStepIds."""
    import yaml
    from pathlib import Path
    monkeypatch.setenv("PAICER_HOME", str(tmp_path))
    from paicer.integrations.garmin import GarminIntegration

    path = Path(__file__).parent.parent / "examples" / "strength-8week.yaml"
    plan = yaml.safe_load(path.read_text())
    integration = GarminIntegration()

    count = 0
    for phase in plan["phases"]:
        for week in phase["weeks"]:
            for workout in week["workouts"]:
                built = integration.build_workout(workout)
                count += 1
                _assert_steps_sane(built["workoutSegments"][0]["workoutSteps"])

    assert count == 48


def _assert_steps_sane(steps, parent_child_id=None):
    for step in steps:
        if step.get("type") == "RepeatGroupDTO":
            for child in step["workoutSteps"]:
                assert child.get("childStepId") == step["childStepId"], (
                    "nested step childStepId must match its repeat group"
                )
            _assert_steps_sane(step["workoutSteps"], step["childStepId"])
        elif step["stepType"]["stepTypeId"] == 5 and "category" not in step:
            assert step["targetType"] is None


def test_no_strength_workout_has_a_warmup_step():
    """The watch prompts for reps and weight on every non-rest step, so a
    warmup with no exercise becomes a phantom set the athlete must edit
    past before saving. Garmin's own strength workouts have none.
    Confirmed on-watch 2026-08-18."""
    import yaml
    from pathlib import Path
    root = Path(__file__).parent.parent
    plans = [
        "examples/strength-8week.yaml",
        "examples/reference-metric.yaml",
        "examples/reference-imperial.yaml",
        "claude-plugin/guides/examples/reference-metric.yaml",
        "claude-plugin/guides/examples/reference-imperial.yaml",
    ]
    checked = 0
    for rel in plans:
        plan = yaml.safe_load((root / rel).read_text())
        for phase in plan["phases"]:
            for week in phase["weeks"]:
                for workout in week["workouts"]:
                    if workout.get("type") != "strength":
                        continue
                    checked += 1
                    for step in workout["garmin"]["steps"]:
                        assert step.get("stepType") != "warmup", (
                            f"{rel} '{workout['name']}' has a warmup step"
                        )
    assert checked == 40
