"""Step-line extraction for plan documents.

The swim cases here are characterization tests written against the original
`extract_swim_steps` before it was generalized to `extract_step_lines`.
They pin the exact rendered output so the generalization could not change
swim behaviour.
"""

import pytest


SWIM_GARMIN = {
    "steps": [
        {"stepType": "warmup", "endCondition": "lap.button",
         "targetType": "no.target", "description": "200m easy freestyle"},
        {"stepType": "rest", "endCondition": "lap.button",
         "targetType": "no.target"},
        {"stepType": "interval", "endCondition": "lap.button",
         "targetType": "no.target", "description": "4x50m catch-up drill"},
        {"stepType": "rest", "endCondition": "lap.button",
         "targetType": "no.target"},
        {"numberOfIterations": 4, "stepType": "repeat", "childStepId": 1,
         "steps": [
             {"stepType": "interval", "endCondition": "lap.button",
              "targetType": "no.target", "childStepId": 1,
              "description": "100m freestyle @ RPE 6"},
             {"stepType": "rest", "endCondition": "lap.button",
              "targetType": "no.target", "childStepId": 1},
         ]},
        {"stepType": "cooldown", "endCondition": "lap.button",
         "targetType": "no.target", "description": "100m easy"},
    ]
}

# Pinned before the refactor. Rest steps dropped, repeat groups collapsed
# to (iterations, [descriptions]).
SWIM_EXPECTED = [
    "200m easy freestyle",
    "4x50m catch-up drill",
    (4, ["100m freestyle @ RPE 6"]),
    "100m easy",
]


STRENGTH_GARMIN = {
    "steps": [
        {"numberOfIterations": 3, "stepType": "repeat", "childStepId": 1,
         "steps": [
             {"stepType": "interval", "endCondition": "reps",
              "endConditionValue": 8, "targetType": "no.target",
              "childStepId": 1, "category": "BENCH_PRESS",
              "exerciseName": "BARBELL_BENCH_PRESS"},
             {"stepType": "rest", "endCondition": "time",
              "endConditionValue": 90, "childStepId": 1},
             {"stepType": "interval", "endCondition": "reps",
              "endConditionValue": 10, "targetType": "no.target",
              "childStepId": 1, "category": "FLYE",
              "exerciseName": "DUMBBELL_FLYE"},
             {"stepType": "rest", "endCondition": "time",
              "endConditionValue": 90, "childStepId": 1},
         ]},
        {"stepType": "interval", "endCondition": "reps",
         "endConditionValue": 12, "targetType": "no.target",
         "category": "CURL", "exerciseName": "BARBELL_BICEPS_CURL"},
        {"stepType": "rest", "endCondition": "time", "endConditionValue": 60},
    ]
}


def test_swim_output_unchanged_by_refactor():
    from paicer.plan_utils import extract_step_lines
    workout = {"type": "swim", "garmin": SWIM_GARMIN}
    assert extract_step_lines(workout) == SWIM_EXPECTED


def test_legacy_extract_swim_steps_still_matches():
    """The old entry point is kept as a thin alias; guard it too."""
    from paicer.plan_utils import extract_swim_steps
    assert extract_swim_steps(SWIM_GARMIN) == SWIM_EXPECTED


def test_strength_lines_humanize_and_show_reps():
    from paicer.plan_utils import extract_step_lines
    workout = {"type": "strength", "garmin": STRENGTH_GARMIN}
    assert extract_step_lines(workout) == [
        (3, ["Barbell Bench Press — 8 reps", "Dumbbell Flye — 10 reps"]),
        "Barbell Biceps Curl — 12 reps",
    ]


def test_strength_skips_rest_steps():
    from paicer.plan_utils import extract_step_lines
    workout = {"type": "strength", "garmin": STRENGTH_GARMIN}
    lines = extract_step_lines(workout)
    flat = [x for item in lines
            for x in (item[1] if isinstance(item, tuple) else [item])]
    assert not any("rest" in line.lower() for line in flat)


def test_strength_time_based_step_uses_duration():
    """Planks and carries end on time, not reps."""
    from paicer.plan_utils import extract_step_lines
    workout = {"type": "strength", "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "time",
         "endConditionValue": 45, "targetType": "no.target",
         "category": "PLANK", "exerciseName": "PLANK"},
    ]}}
    assert extract_step_lines(workout) == ["Plank — 45s"]


def test_strength_step_with_description_prefers_it():
    """An explicit description overrides the generated label."""
    from paicer.plan_utils import extract_step_lines
    workout = {"type": "strength", "garmin": {"steps": [
        {"stepType": "interval", "endCondition": "reps",
         "endConditionValue": 5, "targetType": "no.target",
         "category": "SQUAT", "exerciseName": "BARBELL_BACK_SQUAT",
         "description": "5 reps @ RPE 8"},
    ]}}
    assert extract_step_lines(workout) == [
        "Barbell Back Squat — 5 reps @ RPE 8"
    ]


@pytest.mark.parametrize("sport", ["run", "bike", "track", "race"])
def test_other_sports_produce_no_lines(sport):
    from paicer.plan_utils import extract_step_lines
    workout = {"type": sport, "garmin": SWIM_GARMIN}
    assert extract_step_lines(workout) == []


def test_missing_garmin_section():
    from paicer.plan_utils import extract_step_lines
    assert extract_step_lines({"type": "strength"}) == []
