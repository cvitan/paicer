"""Shared utilities for training plan processing."""

from datetime import datetime, timedelta
from typing import Dict


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

    start = datetime.strptime(start_date, "%Y-%m-%d")

    # Find first Monday on or after start date
    days_until_monday = (7 - start.weekday()) % 7
    if days_until_monday == 0 and start.weekday() != 0:
        days_until_monday = 7
    first_monday = start + timedelta(days=days_until_monday)

    # Get the weekday for this day
    weekday = training_days[day - 1]  # day is 1-based, list is 0-based

    # Calculate: week start Monday + (weekday - 1) days
    week_start = first_monday + timedelta(weeks=(week - 1))
    workout_date = week_start + timedelta(days=(weekday - 1))

    return workout_date.strftime("%Y-%m-%d")


def calculate_week_dates(start_date: str, week: int, training_days: list[int]) -> str:
    """Calculate week date range string (Monday to Sunday).

    Returns format like: "Feb 23 - Mar 01" or "Feb 23 - 27"
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")

    # Find first Monday
    days_until_monday = (7 - start.weekday()) % 7
    if days_until_monday == 0 and start.weekday() != 0:
        days_until_monday = 7
    first_monday = start + timedelta(days=days_until_monday)

    # Week runs Monday to Sunday
    week_start = first_monday + timedelta(weeks=(week - 1))
    week_end = week_start + timedelta(days=6)  # Sunday

    # Format: show month on end date if different from start
    if week_start.month == week_end.month:
        return f"{week_start.strftime('%b %d')} - {week_end.strftime('%d')}"
    else:
        return f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"


def calculate_phase_dates(start_date: str, phase_weeks: list[Dict]) -> str:
    """Calculate phase date range from list of weeks.

    Returns format like: "Feb 23 – Mar 08"
    """
    if not phase_weeks:
        return ""

    first_week = phase_weeks[0]["week"]
    last_week = phase_weeks[-1]["week"]

    start = datetime.strptime(start_date, "%Y-%m-%d")

    # Find first Monday
    days_until_monday = (7 - start.weekday()) % 7
    if days_until_monday == 0 and start.weekday() != 0:
        days_until_monday = 7
    first_monday = start + timedelta(days=days_until_monday)

    # Phase start = first week's Monday
    phase_start = first_monday + timedelta(weeks=(first_week - 1))
    # Phase end = last week's Sunday
    phase_end = first_monday + timedelta(weeks=last_week) - timedelta(days=1)

    return f"{phase_start.strftime('%b %d')} – {phase_end.strftime('%b %d')}"


def load_plan(plan_file: str) -> Dict:
    """Load and return plan data from YAML file."""
    import yaml

    with open(plan_file) as f:
        return yaml.safe_load(f)
