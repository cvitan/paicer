"""HTML formatter."""

from typing import Dict
from plan_utils import (
    calculate_workout_date,
    calculate_week_dates,
    calculate_phase_dates,
    extract_swim_steps,
)
from .base import DocumentFormatter


class HTMLFormatter(DocumentFormatter):
    """Renders training plan as printable HTML."""

    def __init__(self, paper_format: str = "letter"):
        """Initialize with paper format.

        Args:
            paper_format: 'letter' or 'a4'
        """
        self.paper_format = paper_format

        # Paper size settings
        if paper_format == "a4":
            self.page_size = "A4"
            self.page_width = "21cm"
            self.margin = "1.5cm"
        else:  # letter
            self.page_size = "letter"
            self.page_width = "8.5in"
            self.margin = "0.5in"

    def render(self, plan_data: dict) -> str:
        """Generate HTML from plan data."""
        plan = plan_data["plan"]
        phases = plan_data["phases"]
        start_date = plan["start_date"]
        global_training_days = plan.get("training_days", [1, 2, 3, 4, 5, 6, 7])

        html = []

        # HTML header with CSS
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append(
            "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        )
        html.append(f"  <title>{plan['name']}</title>")
        html.append("  <style>")
        html.append(
            f"""
    @media print {{
      .week-page {{ page-break-after: always; page-break-inside: avoid; }}
      .overview-page {{ page-break-after: always; }}
      body {{ max-width: 100%; padding: {self.margin}; }}
      @page {{ size: {self.page_size}; margin: {self.margin}; }}
    }}
    body {{
      font-family: Helvetica, Arial, sans-serif;
      line-height: 1.5;
      max-width: {self.page_width};
      margin: 0 auto;
      padding: {self.margin};
      color: #1a1a2e;
      background: white;
    }}
    h1 {{ color: #c0392b; font-size: 20px; border-bottom: 2px solid #c0392b; padding-bottom: 8px; margin-top: 0; }}
    h2 {{ color: #2c3e50; font-size: 16px; margin-top: 25px; margin-bottom: 10px; }}
    .plan-title {{ font-size: 22px; color: #1a1a2e; font-weight: bold; margin-bottom: 5px; }}
    .subtitle {{ font-size: 11px; color: #666666; margin-bottom: 15px; }}
    .phase-header {{ background-color: #eef2f7; padding: 10px 15px; margin: 0 0 0 0; border-left: 4px solid #c0392b; }}
    .phase-title {{ font-size: 16px; color: #c0392b; font-weight: bold; margin: 0 0 3px 0; }}
    .phase-description {{ font-size: 10px; color: #1a1a2e; margin: 2px 0; }}
    .week-page {{ margin-bottom: 40px; }}
    .week-header {{ background-color: #f8f9fa; padding: 8px 12px; margin: 6px 0 5px 0; border-left: 3px solid #2c3e50; }}
    .week-title {{ font-size: 16px; color: #2c3e50; font-weight: bold; margin: 0 0 3px 0; }}
    .week-description {{ font-size: 10px; color: #1a1a2e; margin: 2px 0; }}
    .workout-table {{ width: 100%; border-collapse: collapse; margin: 5px 0; font-size: 11px; }}
    .workout-table th {{ background-color: #2c3e50; color: white; padding: 6px; text-align: left; font-size: 11px; }}
    .workout-table td {{ border: 1px solid #cccccc; padding: 8px; vertical-align: top; }}
    .workout-table tr.row-shaded {{ background-color: #eef2f7; }}
    .workout-day {{ font-weight: bold; color: #1a1a2e; font-size: 11px; }}
    .workout-name {{ font-weight: bold; color: #1a1a2e; margin-bottom: 5px; }}
    .workout-desc {{ font-size: 11px; color: #1a1a2e; line-height: 1.4; }}
    .swim-steps {{ margin: 4px 0 0 0; padding-left: 18px; font-size: 10px; color: #2c3e50; }}
    .swim-steps li {{ margin: 1px 0; }}
    .swim-steps ul {{ padding-left: 14px; margin: 1px 0; list-style-type: disc; }}
    .overview-page {{ margin-bottom: 40px; }}
    .overview-section {{ margin: 15px 0; }}
    .overview-section p {{ font-size: 10px; margin: 5px 0; }}
    .overview-section table {{ border-collapse: collapse; margin: 10px 0; }}
    .overview-section th {{ border: 1px solid #ddd; padding: 8px; background: #2c3e50; color: white; font-size: 10px; }}
    .overview-section td {{ border: 1px solid #ddd; padding: 8px; font-size: 10px; }}
    """
        )
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")

        # Overview page
        html.append("  <div class='overview-page'>")
        html.append(f"    <div class='plan-title'>{plan['name']}</div>")
        html.append(
            f"    <div class='subtitle'>Plan Start: {start_date} • Training Days: {', '.join([['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d - 1] for d in global_training_days])}</div>"
        )
        html.append("    <hr>")

        # Overview content - convert markdown to HTML
        html.append("    <div class='overview-section' style='font-size: 10px;'>")
        import markdown as md

        # Ensure blank line before markdown tables (required by parser)
        # Only insert before the first | row, not between table rows
        import re
        overview_text = re.sub(
            r'([^\n|])\n(\|)', r'\1\n\n\2', plan["overview"],
        )
        overview_html = md.markdown(overview_text, extensions=["tables"])

        # Add custom styling to tables
        overview_html = overview_html.replace(
            "<table>",
            "<table style='border-collapse: collapse; margin: 10px 0;'>"
        )
        overview_html = overview_html.replace(
            "<th>",
            "<th style='border: 1px solid #ddd; padding: 8px; background: #2c3e50; color: white; font-size: 10px;'>"
        )
        overview_html = overview_html.replace(
            "<td>",
            "<td style='border: 1px solid #ddd; padding: 8px; font-size: 10px;'>"
        )

        html.append(f"      {overview_html}")
        html.append("    </div>")
        html.append("  </div>")

        # Phases
        for phase in phases:
            phase_training_days = phase.get("training_days", global_training_days)
            phase_dates = calculate_phase_dates(start_date, phase["weeks"])

            # Weeks (one per page)
            for week in phase["weeks"]:
                week_num = week["week"]
                week_dates = calculate_week_dates(
                    start_date, week_num, phase_training_days
                )

                html.append("  <div class='week-page'>")

                # Phase context
                html.append("    <div class='phase-header'>")
                html.append(
                    f"      <div class='phase-title'>Phase {phase['phase']}: {phase['name']} | {phase_dates}</div>"
                )
                for line in phase["description"].strip().split("\n"):
                    if line.strip():
                        html.append(
                            f"      <div class='phase-description'>{line}</div>"
                        )
                html.append("    </div>")

                # Week header
                html.append("    <div class='week-header'>")
                html.append(
                    f"      <div class='week-title'>Week {week_num}: {week_dates}</div>"
                )
                for line in week["description"].strip().split("\n"):
                    if line.strip():
                        html.append(f"      <div class='week-description'>{line}</div>")
                html.append("    </div>")

                # Workouts table
                html.append("    <table class='workout-table'>")
                html.append("      <tr>")
                html.append("        <th style='width: 30px;'>✓</th>")
                html.append("        <th style='width: 120px;'>Workout</th>")
                html.append("        <th>Details</th>")
                html.append("      </tr>")

                weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                prev_day = None
                row_group = 0

                for workout in week["workouts"]:
                    day_num = workout.get("day")
                    is_optional = workout.get("optional", False)

                    # Skip non-optional workouts beyond training_days range
                    if day_num and day_num > len(phase_training_days) and not is_optional:
                        continue

                    # Track day groups for alternating colors
                    same_day = day_num is not None and day_num == prev_day
                    if not same_day:
                        row_group += 1
                    row_class = " class='row-shaded'" if row_group % 2 == 0 else ""

                    name = workout["name"]
                    desc = workout["description"]
                    workout_title = name

                    html.append(f"      <tr{row_class}>")
                    html.append("        <td></td>")
                    if day_num and not same_day:
                        if is_optional:
                            html.append(
                                f"        <td><div class='workout-name'>Optional</div><div class='workout-day'>{workout_title}</div></td>"
                            )
                        else:
                            workout_date = calculate_workout_date(
                                start_date, week_num, day_num, phase_training_days
                            )
                            day_label = weekday_names[phase_training_days[day_num - 1] - 1]
                            html.append(
                                f"        <td><div class='workout-name'>{day_label} ({workout_date})</div><div class='workout-day'>{workout_title}</div></td>"
                            )
                    else:
                        html.append(
                            f"        <td><div class='workout-day'>{workout_title}</div></td>"
                        )
                    # Build description cell content
                    desc_html = desc
                    if workout.get("type") == "swim":
                        steps = extract_swim_steps(workout.get("garmin"))
                        if steps:
                            desc_html += "<ol class='swim-steps'>"
                            for item in steps:
                                if isinstance(item, tuple):
                                    reps, nested = item
                                    desc_html += f"<li>{reps}x:<ul>"
                                    for n in nested:
                                        desc_html += f"<li>{n}</li>"
                                    desc_html += "</ul></li>"
                                else:
                                    desc_html += f"<li>{item}</li>"
                            desc_html += "</ol>"
                    html.append(f"        <td class='workout-desc'>{desc_html}</td>")
                    html.append("      </tr>")
                    prev_day = day_num

                html.append("    </table>")
                html.append("  </div>")

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)
