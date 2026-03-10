#!/usr/bin/env python3
"""
Sync workouts from YAML plan to workout integration.

Usage:
    python generate_workouts.py plan.yaml <filter> [--no-schedule]

Filter: p1 | w7 | w7d2 | all
Integration is set via WORKOUT_INTEGRATION in .env (default: garmin)
"""

import os
import sys
from dotenv import load_dotenv
from plan_utils import calculate_workout_date, load_plan

# Load .env file
load_dotenv()


def get_integration(name: str):
    """Get integration instance by name."""
    if name == "garmin":
        from integrations.garmin import GarminIntegration
        return GarminIntegration()

    raise ValueError(f"Integration '{name}' not found")


def parse_filter(filter_str: str) -> tuple[int | None, int | None, int | None]:
    """Parse filter like 'p1', 'w7', 'w7d2', or 'all'."""
    import re

    if filter_str.lower() == "all":
        return None, None, None

    # Phase only: p1, p2
    match = re.match(r"[pP](\d+)$", filter_str)
    if match:
        return int(match.group(1)), None, None

    # Week (with optional day): w7, w7d2
    match = re.match(r"[wW](\d+)(?:[dD](\d+))?$", filter_str)
    if match:
        week = int(match.group(1))
        day = int(match.group(2)) if match.group(2) else None
        return None, week, day

    raise ValueError(
        f"Invalid filter: {filter_str}. Use 'p1', 'w7', 'w7d2', or 'all'"
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_workouts.py plan.yaml <filter> [--no-schedule]")
        print("")
        print("Filter (required):")
        print("  p1        All workouts in phase 1")
        print("  w7        All workouts in week 7")
        print("  w7d2      Week 7 day 2 only")
        print("  all       All weeks")
        print("")
        print("Options:")
        print("  --no-schedule    Upload to library only (don't schedule to calendar)")
        sys.exit(1)

    plan_file = sys.argv[1]
    filter_str = sys.argv[2]
    no_schedule = "--no-schedule" in sys.argv

    # Parse filter
    try:
        filter_phase, filter_week, filter_day = parse_filter(filter_str)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Load plan
    data = load_plan(plan_file)
    start_date = data["plan"]["start_date"]
    global_training_days = data["plan"].get("training_days", [1, 2, 3, 4, 5, 6, 7])

    # Initialize integration
    integration_name = os.getenv("WORKOUT_INTEGRATION", "garmin").lower()

    try:
        integration = get_integration(integration_name)
        integration.authenticate()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # Track uploaded workouts and their dates
    uploaded_dates = []
    uploaded_names = []
    skipped_workouts = []
    week_monday = None

    # Process each phase
    for phase in data["phases"]:
        phase_num = phase["phase"]

        if filter_phase is not None and phase_num != filter_phase:
            continue

        # Get training days for this phase
        phase_training_days = phase.get("training_days", global_training_days)

        for week_data in phase["weeks"]:
            week_num = week_data["week"]

            if filter_week is not None and week_num != filter_week:
                continue

            # Validate: non-optional Garmin workouts don't exceed training days
            garmin_days = set(
                w["day"]
                for w in week_data["workouts"]
                if not w.get("skip_garmin") and "garmin" in w
                and not w.get("optional")
            )
            if len(garmin_days) > len(phase_training_days):
                print(
                    f"Error: Week {week_num} has {len(garmin_days)} Garmin days but only {len(phase_training_days)} training days"
                )
                sys.exit(1)

            for workout in week_data["workouts"]:
                day_num = workout["day"]

                if filter_day is not None and day_num != filter_day:
                    continue

                if workout.get("skip_garmin") or "garmin" not in workout:
                    skipped_workouts.append(workout)
                    continue

                garmin_name = f"W{week_num}: {workout['name']}"
                is_optional = workout.get("optional", False)

                # Optional workouts may have day beyond training_days
                workout_date = None
                if not is_optional or day_num <= len(phase_training_days):
                    workout_date = calculate_workout_date(
                        start_date, week_num, day_num, phase_training_days
                    )

                # Track week Monday (first training day of week)
                if week_monday is None and day_num == 1 and workout_date:
                    week_monday = workout_date

                # Print syncing message once
                if len(uploaded_names) == 0:
                    if filter_day:
                        print(f"Syncing {garmin_name}")
                    elif filter_week:
                        print(f"Syncing Week {filter_week}")
                    elif filter_phase:
                        print(f"Syncing Phase {filter_phase}")
                    else:
                        print("Syncing all workouts...")

                try:
                    # Delete existing workout with same name
                    integration.delete_workout(garmin_name)

                    # Build workout directly from YAML steps
                    garmin_workout = {**workout, "name": garmin_name}
                    workout_json = integration.build_workout(garmin_workout)

                    # Upload workout
                    workout_id = integration.upload_workout(workout_json)

                    # Schedule workout (unless --no-schedule or optional)
                    if not no_schedule and not is_optional and workout_date:
                        integration.schedule_workout(workout_id, workout_date)

                    if workout_date and not is_optional:
                        uploaded_dates.append(workout_date)
                    uploaded_names.append(garmin_name)

                except Exception as e:
                    print(f"Error: {e}")
                    sys.exit(1)

    # Result
    if not uploaded_names:
        if skipped_workouts:
            for w in skipped_workouts:
                print(f"Skipped: {w['name']} (session set to skip Garmin sync)")
            sys.exit(0)
        print("Error: No workouts found matching filter")
        sys.exit(1)

    # Format confirmation message
    count = len(uploaded_names)
    if no_schedule:
        if filter_day:
            print("✓ Uploaded to Garmin Connect")
        else:
            print(f"✓ Uploaded {count} workout{'s' if count > 1 else ''} to Garmin Connect")
    else:
        if filter_day and uploaded_dates:
            print(f"✓ Synced to Garmin Connect and scheduled for {uploaded_dates[0]}")
        elif filter_day:
            print("✓ Uploaded to Garmin Connect")
        elif filter_week or filter_phase:
            print(f"✓ Synced {count} workout{'s' if count > 1 else ''} to Garmin Connect")
        else:
            print("✓ Synced to Garmin Connect")


if __name__ == "__main__":
    main()
