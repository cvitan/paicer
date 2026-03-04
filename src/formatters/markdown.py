"""Markdown formatter."""

from typing import Dict
from plan_utils import (
    calculate_workout_date,
    calculate_week_dates,
    calculate_phase_dates,
    extract_swim_steps,
)
from .base import DocumentFormatter


class MarkdownFormatter(DocumentFormatter):
    """Renders training plan as Markdown."""

    def format_workout(
        self,
        workout: Dict,
        start_date: str,
        week_num: int,
        training_days: list[int],
        show_day_label: bool = True,
    ) -> str:
        """Format a single workout as markdown."""
        day_num = workout.get("day")
        name = workout["name"]
        desc = workout["description"]

        # Skip workouts beyond training_days range
        if day_num and day_num > len(training_days):
            return ""

        # Build day prefix (weekday + date) when applicable
        prefix = ""
        if day_num and show_day_label:
            workout_date = calculate_workout_date(
                start_date, week_num, day_num, training_days
            )
            weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_name = weekday_names[training_days[day_num - 1] - 1]
            prefix = f"{day_name} ({workout_date}): "

        distance = workout.get("distance")
        if distance:
            distance_km = distance / 1000
            line = f"**{prefix}{name}** — {distance_km}km  \n{desc}\n"
        else:
            line = f"**{prefix}{name}**  \n{desc}\n"

        # Render swim session steps
        if workout.get("type") == "swim":
            steps = extract_swim_steps(workout.get("garmin"))
            if steps:
                line += "\n"
                for item in steps:
                    if isinstance(item, tuple):
                        reps, nested = item
                        line += f"- {reps}x:\n"
                        for n in nested:
                            line += f"  - {n}\n"
                    else:
                        line += f"- {item}\n"

        return line

    def render(self, plan_data: dict) -> str:
        """Generate markdown from plan data."""
        plan = plan_data["plan"]
        phases = plan_data["phases"]
        start_date = plan["start_date"]
        global_training_days = plan.get("training_days", [1, 2, 3, 4, 5, 6, 7])

        md = []

        # Title
        md.append(f"# {plan['name']}")
        md.append("")
        md.append(
            f"**Plan Start Date:** {start_date} _(workouts begin first Monday on or after this date)_"
        )
        md.append("")

        # Show training days
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days_str = ", ".join([day_names[d - 1] for d in global_training_days])
        md.append(f"**Training Days:** {days_str}")
        md.append("")

        # Overview
        md.append(plan["overview"])
        md.append("")

        # Phases
        for phase in phases:
            phase_training_days = phase.get("training_days", global_training_days)
            phase_dates = calculate_phase_dates(start_date, phase["weeks"])
            md.append("---")
            md.append("")
            md.append(f"# Phase {phase['phase']}: {phase['name']}")
            md.append(f"**{phase_dates}**")
            md.append("")
            md.append(phase["description"])
            md.append("")

            # Weeks
            for week in phase["weeks"]:
                week_num = week["week"]
                week_dates = calculate_week_dates(
                    start_date, week_num, phase_training_days
                )
                md.append(f"## Week {week_num}: {week_dates}")
                md.append("")
                md.append(week["description"])
                md.append("")
                md.append("### Workouts")
                md.append("")

                prev_day = None
                for workout in week["workouts"]:
                    day_num = workout.get("day")
                    same_day = day_num is not None and day_num == prev_day
                    formatted = self.format_workout(
                        workout, start_date, week_num, phase_training_days,
                        show_day_label=not same_day,
                    )
                    if formatted:
                        md.append(formatted)
                        md.append("")
                    prev_day = day_num

        return "\n".join(md)
