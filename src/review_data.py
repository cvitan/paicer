"""Pull Garmin activity data for a plan week and output as JSON.

Usage: python src/review_data.py <plan_file> [week_number]

If week_number is omitted, uses the most recently completed week.

Output JSON structure:
{
  "week": 2,
  "week_dates": {"start": "2026-01-12", "end": "2026-01-18"},
  "planned": [
    {"garmin_name": "W2D1: Easy 8km", "type": "run", "distance": 8000, ...}
  ],
  "activities": [
    {"activityName": "W2D1: Easy 8km", "distance": 8123.4, ...}
  ]
}
"""

import json
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

from integrations.garmin import GarminIntegration
from plan_utils import load_plan

load_dotenv()


def find_current_week(start_date, today=None):
    """Determine the most recently completed week number."""
    today = today or datetime.now()
    start = datetime.strptime(start_date, "%Y-%m-%d")

    days_until_monday = (7 - start.weekday()) % 7
    if days_until_monday == 0 and start.weekday() != 0:
        days_until_monday = 7
    first_monday = start + timedelta(days=days_until_monday)

    days_elapsed = (today - first_monday).days
    if days_elapsed < 0:
        return 1
    current_week = days_elapsed // 7 + 1

    # If today is Mon-Sat, the most recently *completed* week
    # is the previous one (current week is still in progress)
    weekday = today.weekday()  # 0=Mon, 6=Sun
    if weekday < 6:
        current_week -= 1

    return max(current_week, 1)


def get_week_dates(start_date, week_num):
    """Get Monday-Sunday date range for a week, padded +/- 2 days."""
    start = datetime.strptime(start_date, "%Y-%m-%d")

    days_until_monday = (7 - start.weekday()) % 7
    if days_until_monday == 0 and start.weekday() != 0:
        days_until_monday = 7
    first_monday = start + timedelta(days=days_until_monday)

    week_start = first_monday + timedelta(weeks=(week_num - 1))
    week_end = week_start + timedelta(days=6)

    # Pad range to catch workouts done on different days
    search_start = week_start - timedelta(days=2)
    search_end = week_end + timedelta(days=2)

    return week_start, week_end, search_start, search_end


def get_planned_workouts(plan_data, week_num):
    """Extract planned workouts for a given week."""
    workouts = []
    for phase in plan_data["phases"]:
        for week in phase["weeks"]:
            if week["week"] == week_num:
                for w in week["workouts"]:
                    workouts.append({
                        "garmin_name": w.get("garmin_name"),
                        "name": w["name"],
                        "type": w.get("type", "run"),
                        "distance": w.get("distance"),
                        "description": w.get("description", ""),
                        "skip_garmin": w.get("skip_garmin", False),
                    })
    return workouts


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/review_data.py <plan_file> [week]",
              file=sys.stderr)
        sys.exit(1)

    plan_file = sys.argv[1]
    plan_data = load_plan(plan_file)
    start_date = plan_data["plan"]["start_date"]

    week_num = (
        int(sys.argv[2])
        if len(sys.argv) > 2
        else find_current_week(start_date)
    )

    week_start, week_end, search_start, search_end = get_week_dates(
        start_date, week_num,
    )

    # Get planned workouts
    planned = get_planned_workouts(plan_data, week_num)

    # Pull Garmin activities
    garmin = GarminIntegration()
    garmin.authenticate()
    activities = garmin.api.get_activities_by_date(
        search_start.strftime("%Y-%m-%d"),
        search_end.strftime("%Y-%m-%d"),
    )

    # Extract relevant fields from each activity
    activity_data = []
    for a in activities:
        activity_data.append({
            "activityName": a.get("activityName"),
            "activityType": a.get("activityType", {}).get(
                "typeKey", "unknown",
            ),
            "startTimeLocal": a.get("startTimeLocal"),
            "distance": a.get("distance"),
            "duration": a.get("duration"),
            "averageSpeed": a.get("averageSpeed"),
            "averageHR": a.get("averageHR"),
            "maxHR": a.get("maxHR"),
            "averagePower": a.get("averagePower"),
            "maxPower": a.get("maxPower"),
        })

    output = {
        "week": week_num,
        "week_dates": {
            "start": week_start.strftime("%Y-%m-%d"),
            "end": week_end.strftime("%Y-%m-%d"),
        },
        "planned": planned,
        "activities": activity_data,
    }

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
