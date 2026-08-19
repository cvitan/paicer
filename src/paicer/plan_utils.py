"""Shared utilities for training plan processing."""

from datetime import datetime, timedelta
from typing import Dict

SPORT_LABELS = {
    "run": "Run",
    "track": "Track",
    "bike": "Bike",
    "swim": "Swim",
    "strength": "Strength",
    "multisport": "Brick",
    "race": "Race",
}

SPORT_EMOJI = {
    "run": "🏃",
    "track": "🏃",
    "bike": "🚴",
    "swim": "🏊",
    "strength": "🏋️",
    "multisport": "🏃🚴",
    "race": "🏁",
}


def format_display_date(date_str: str) -> str:
    """Format YYYY-MM-DD as 'Mar 3' (no year, no zero-padding)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.strftime('%b')} {dt.day}"


def first_monday_on_or_after(start_date: str) -> datetime:
    """Find the first Monday on or after a date string (YYYY-MM-DD)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    days_until_monday = (7 - start.weekday()) % 7
    return start + timedelta(days=days_until_monday)


def calculate_workout_date(
    start_date: str, week: int, day: int, training_days: list[int]
) -> str:
    """Calculate workout date from plan start date, week, day, and training days.

    Args:
        start_date: Plan start date (YYYY-MM-DD)
        week: Week number (1-based)
        day: Day number (1-based index into training_days)
        training_days: List of weekday numbers [1-7] where 1=Mon, 7=Sun

    Returns:
        Workout date as YYYY-MM-DD string
    """
    if day < 1 or day > len(training_days):
        raise ValueError(
            f"Day {day} out of range for {len(training_days)} training days"
        )

    first_monday = first_monday_on_or_after(start_date)

    # Get the weekday for this day
    weekday = training_days[day - 1]  # day is 1-based, list is 0-based

    # Calculate: week start Monday + (weekday - 1) days
    week_start = first_monday + timedelta(weeks=(week - 1))
    workout_date = week_start + timedelta(days=(weekday - 1))

    return workout_date.strftime("%Y-%m-%d")


def calculate_week_dates(start_date: str, week: int) -> str:
    """Calculate week date range string (Monday to Sunday).

    Returns format like: "Feb 23 – Mar 1" or "Feb 23 – 27"
    """
    first_monday = first_monday_on_or_after(start_date)

    # Week runs Monday to Sunday
    week_start = first_monday + timedelta(weeks=(week - 1))
    week_end = week_start + timedelta(days=6)  # Sunday

    # Format: show month on end date if different from start
    start_str = f"{week_start.strftime('%b')} {week_start.day}"
    if week_start.month == week_end.month:
        return f"{start_str} – {week_end.day}"
    else:
        return f"{start_str} – {week_end.strftime('%b')} {week_end.day}"


def calculate_phase_dates(start_date: str, phase_weeks: list[Dict]) -> str:
    """Calculate phase date range from list of weeks.

    Returns format like: "Feb 23 – Mar 8"
    """
    if not phase_weeks:
        return ""

    first_week = phase_weeks[0]["week"]
    last_week = phase_weeks[-1]["week"]

    first_monday = first_monday_on_or_after(start_date)

    # Phase start = first week's Monday
    phase_start = first_monday + timedelta(weeks=(first_week - 1))
    # Phase end = last week's Sunday
    phase_end = first_monday + timedelta(weeks=last_week) - timedelta(days=1)

    start_str = f"{phase_start.strftime('%b')} {phase_start.day}"
    end_str = f"{phase_end.strftime('%b')} {phase_end.day}"
    return f"{start_str} – {end_str}"


def _swim_step_label(step: Dict) -> str | None:
    """Swim steps are cue cards — the description is the whole content."""
    return step.get("description")


def _format_duration(seconds) -> str:
    """45 -> '45s', 90 -> '1:30'."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}:{seconds % 60:02d}"


def _strength_step_label(step: Dict) -> str | None:
    """Build 'Barbell Bench Press — 8 reps' from an exercise step.

    An explicit description replaces the generated quantity, so a plan can
    say '5 reps @ RPE 8' and keep the load cue.
    """
    from .exercises import humanize

    name = step.get("exerciseName")
    if not name:
        return step.get("description")

    label = humanize(name)
    detail = step.get("description")
    if not detail:
        value = step.get("endConditionValue")
        if value is None:
            return label
        if step.get("endCondition") == "time":
            detail = _format_duration(value)
        else:
            detail = f"{int(value)} reps"

    return f"{label} — {detail}"


_STEP_LABELS = {
    "swim": _swim_step_label,
    "strength": _strength_step_label,
}


def extract_step_lines(workout: Dict) -> list:
    """Extract per-step display lines for a workout.

    Returns a flat list where each item is either:
    - str: a step line
    - tuple: (repeat_count, [nested lines])

    Rest steps are excluded (only relevant to the watch). Sports with no
    per-step display (run, bike, track, race) return an empty list — their
    content lives in the workout description.
    """
    label_for = _STEP_LABELS.get(workout.get("type"))
    if label_for is None:
        return []

    garmin_data = workout.get("garmin")
    if not garmin_data or "steps" not in garmin_data:
        return []

    result = []
    for step in garmin_data["steps"]:
        if step.get("stepType") == "rest":
            continue

        if "numberOfIterations" in step:
            reps = step["numberOfIterations"]
            nested = []
            for s in step.get("steps", []):
                if s.get("stepType") == "rest":
                    continue
                label = label_for(s)
                if label:
                    nested.append(label)
            if nested:
                result.append((reps, nested))
            continue

        label = label_for(step)
        if label:
            result.append(label)

    return result


def extract_swim_steps(garmin_data: dict) -> list:
    """Deprecated alias for extract_step_lines on a swim workout."""
    return extract_step_lines({"type": "swim", "garmin": garmin_data})


def validate_training_days(plan_data: Dict) -> list[str]:
    """Check that non-optional workouts don't exceed training_days per week.

    Returns list of error messages (empty if valid).
    """
    global_training_days = plan_data["plan"].get(
        "training_days", [1, 2, 3, 4, 5, 6, 7]
    )
    errors = []

    for phase in plan_data["phases"]:
        phase_num = phase["phase"]
        phase_training_days = phase.get("training_days", global_training_days)
        slots = len(phase_training_days)

        for week_data in phase["weeks"]:
            week_num = week_data["week"]
            required_days = set()
            for workout in week_data["workouts"]:
                if workout.get("optional"):
                    continue
                day = workout.get("day")
                if day is None or not isinstance(day, int):
                    errors.append(
                        f"Week {week_num} (phase {phase_num}): "
                        f"non-optional workout missing valid 'day' value."
                    )
                    continue
                if day < 1 or day > slots:
                    errors.append(
                        f"Week {week_num} (phase {phase_num}): "
                        f"workout on day {day}, but only {slots} training "
                        f"days configured (day must be 1–{slots})."
                    )
                    continue
                required_days.add(day)
            if len(required_days) > slots:
                errors.append(
                    f"Week {week_num} (phase {phase_num}) has "
                    f"{len(required_days)} non-optional workouts but only "
                    f"{slots} training days. Either mark some workouts as "
                    f"optional: true or add training days."
                )

    return errors


def _iter_steps(steps):
    """Yield every executable step, flattening repeat groups."""
    for step in steps or []:
        if "numberOfIterations" in step:
            yield from _iter_steps(step.get("steps", []))
        else:
            yield step


def validate_strength_exercises(plan_data: Dict) -> list[str]:
    """Check every strength step names a real Garmin exercise.

    Two failure modes, both silent without this check:

    - A bad category/exercise pair uploads without complaint and then
      shows as a generic exercise on the watch.
    - A non-rest step with *no* exercise becomes a phantom set: the watch
      prompts for reps and weight on every non-rest step, so the athlete
      has to edit past an empty entry before saving. This is why strength
      workouts carry no warmup step.

    Runs at render time as well as sync time.

    Returns list of error messages (empty if valid).
    """
    from .exercises import validate

    errors = []
    for phase in plan_data.get("phases", []):
        for week_data in phase.get("weeks", []):
            week_num = week_data.get("week")
            for workout in week_data.get("workouts", []):
                if workout.get("type") != "strength":
                    continue
                garmin = workout.get("garmin") or {}
                for step in _iter_steps(garmin.get("steps")):
                    if step.get("stepType") == "rest":
                        continue
                    category = step.get("category")
                    name = step.get("exerciseName")
                    if not category or not name:
                        errors.append(
                            f"Week {week_num} \"{workout.get('name')}\": "
                            f"{step.get('stepType')} step needs both "
                            f"category and exerciseName — a strength step "
                            f"without an exercise becomes an empty set on "
                            f"the watch."
                        )
                        continue
                    problem = validate(category, name)
                    if problem:
                        errors.append(
                            f"Week {week_num} \"{workout.get('name')}\": "
                            f"{problem}"
                        )
    return errors


def load_plan(plan_file: str) -> Dict:
    """Load and return plan data from YAML file."""
    import yaml

    with open(plan_file) as f:
        return yaml.safe_load(f)
