"""Markdown formatter."""

from typing import Dict
from ..plan_utils import (
    calculate_workout_date,
    calculate_week_dates,
    calculate_phase_dates,
    extract_step_lines,
    format_display_date,
    SPORT_LABELS,
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

        is_optional = workout.get("optional", False)

        # Skip non-optional workouts beyond training_days range
        if day_num and day_num > len(training_days) and not is_optional:
            return ""

        # Build day prefix (weekday + date, plus optional tag if applicable)
        prefix = ""
        if day_num and show_day_label:
            if day_num <= len(training_days):
                workout_date = calculate_workout_date(
                    start_date, week_num, day_num, training_days
                )
                display_date = format_display_date(workout_date)
                weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                day_name = weekday_names[training_days[day_num - 1] - 1]
                if is_optional:
                    prefix = f"{day_name} ({display_date}) — Optional: "
                else:
                    prefix = f"{day_name} ({display_date}): "
            elif is_optional:
                prefix = "Optional: "

        sport_label = SPORT_LABELS.get(workout.get("type", ""), "")
        sport_prefix = f"{sport_label} - " if sport_label else ""
        line = f"**{prefix}{sport_prefix}{name}**  \n{desc}\n"

        # Render race strategy prominently for race workouts
        strategy = workout.get("race_strategy")
        if strategy:
            line += "\n> **🎯 Race Strategy**\n"
            one_liner = strategy.get("one_liner")
            if one_liner:
                line += f"> **The rule:** {one_liner}\n"
            hr_cap = strategy.get("hr_cap")
            release = strategy.get("cap_release_km")
            if hr_cap is not None and release is not None:
                line += f"> HR cap **{hr_cap}** until km **{release}**, then lift and push.\n"
            target_time = strategy.get("target_time")
            target_pace = strategy.get("target_pace")
            if target_time or target_pace:
                bits = []
                if target_time:
                    bits.append(f"Target time: {target_time}")
                if target_pace:
                    bits.append(f"goal pace: {target_pace}")
                line += "> " + " · ".join(bits) + " (HR governs, not pace)\n"
            notes = strategy.get("notes")
            if notes:
                for n_line in notes.strip().splitlines():
                    line += f"> {n_line}\n"

        # Render per-step breakdown (swim cue cards, strength exercises)
        steps = extract_step_lines(workout)
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
                week_dates = calculate_week_dates(start_date, week_num)
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
