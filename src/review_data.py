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
    {"activityName": "W2: Easy 8km", "distance": 8123.4, "intervals": [
      {"type": "INTERVAL_ACTIVE", "paceSecPerKm": 321.0, "averageHR": 165, ...}
    ], ...}
  ]
}
"""

import json
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

from integrations.garmin import GarminIntegration
from plan_utils import first_monday_on_or_after, load_plan

load_dotenv()


def find_current_week(start_date, today=None):
    """Determine the most recently completed week number."""
    today = today or datetime.now()
    first_monday = first_monday_on_or_after(start_date)

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
    first_monday = first_monday_on_or_after(start_date)

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


def get_activity_intervals(garmin, activity_id):
    """Pull structured workout intervals for an activity.

    Uses typed splits which match the Garmin Connect "Intervals" tab.
    Only includes INTERVAL_* types (warmup, active, recovery, cooldown),
    filtering out RWD_* noise (walk/run/stand detection).
    """
    try:
        data = garmin.api.get_activity_typed_splits(activity_id)
    except Exception as e:
        print(f"Warning: failed to fetch intervals for activity {activity_id}: {e}",
              file=sys.stderr)
        return []

    intervals = []
    for split in data.get("splits", []):
        split_type = split.get("type", "")
        if not split_type.startswith("INTERVAL_"):
            continue

        speed = split.get("averageSpeed", 0)
        pace_sec_per_km = (1000 / speed) if speed > 0 else 0
        intervals.append({
            "type": split_type,
            "distance": split.get("distance"),
            "duration": split.get("duration"),
            "paceSecPerKm": round(pace_sec_per_km, 1),
            "averageHR": split.get("averageHR"),
            "maxHR": split.get("maxHR"),
            "averagePower": split.get("averagePower"),
        })
    return intervals


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/review_data.py <plan_file> [week]",
              file=sys.stderr)
        sys.exit(1)

    plan_file = sys.argv[1]
    plan_data = load_plan(plan_file)
    start_date = plan_data["plan"]["start_date"]

    if len(sys.argv) > 2:
        try:
            week_num = int(sys.argv[2])
        except ValueError:
            print(f"Error: '{sys.argv[2]}' is not a valid week number",
                  file=sys.stderr)
            sys.exit(1)
        if week_num < 1:
            print(f"Error: week must be >= 1, got {week_num}",
                  file=sys.stderr)
            sys.exit(1)
    else:
        week_num = find_current_week(start_date)

    week_start, week_end, search_start, search_end = get_week_dates(
        start_date, week_num,
    )

    # Get planned workouts
    planned = get_planned_workouts(plan_data, week_num)

    # Pull Garmin activities
    try:
        garmin = GarminIntegration()
        garmin.authenticate()
        activities = garmin.api.get_activities_by_date(
            search_start.strftime("%Y-%m-%d"),
            search_end.strftime("%Y-%m-%d"),
        )
    except Exception as exc:
        print(f"Error: failed to fetch activities from Garmin: {exc}",
              file=sys.stderr)
        sys.exit(1)

    # Extract relevant fields from each activity, including laps
    activity_data = []
    for a in activities:
        activity_id = a.get("activityId")
        entry = {
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
        }

        # Pull structured workout intervals (matches Garmin Connect's Intervals tab)
        if activity_id:
            entry["intervals"] = get_activity_intervals(
                garmin, activity_id,
            )

        activity_data.append(entry)

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
