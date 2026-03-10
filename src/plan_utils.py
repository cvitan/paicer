"""Shared utilities for training plan processing."""

from datetime import datetime, timedelta
from typing import Dict


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


def calculate_week_dates(start_date: str, week: int, training_days: list[int]) -> str:
    """Calculate week date range string (Monday to Sunday).

    Returns format like: "Feb 23 - Mar 1" or "Feb 23 - 27"
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


def extract_swim_steps(garmin_data: dict) -> list:
    """Extract swim step descriptions for display.

    Returns a flat list where each item is either:
    - str: a step description
    - tuple: (repeat_count, [nested descriptions])

    Rest steps are excluded (only relevant to the watch).
    """
    if not garmin_data or "steps" not in garmin_data:
        return []

    result = []
    for step in garmin_data["steps"]:
        if step.get("stepType") == "rest":
            continue

        if "numberOfIterations" in step:
            reps = step["numberOfIterations"]
            nested = [
                s["description"]
                for s in step.get("steps", [])
                if s.get("stepType") != "rest" and s.get("description")
            ]
            if nested:
                result.append((reps, nested))
            continue

        desc = step.get("description")
        if desc:
            result.append(desc)

    return result


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
            required_days = set(
                w["day"]
                for w in week_data["workouts"]
                if not w.get("optional")
            )
            if len(required_days) > slots:
                errors.append(
                    f"Week {week_num} (phase {phase_num}) has "
                    f"{len(required_days)} non-optional workouts but only "
                    f"{slots} training days. Either mark some workouts as "
                    f"optional: true or add training days."
                )

    return errors


def load_plan(plan_file: str) -> Dict:
    """Load and return plan data from YAML file."""
    import yaml

    with open(plan_file) as f:
        return yaml.safe_load(f)
