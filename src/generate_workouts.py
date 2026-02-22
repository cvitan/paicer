#!/usr/bin/env python3
"""
Sync workouts from YAML plan to workout integration.

Usage:
    python generate_workouts.py plan.yaml <filter> [--no-schedule]

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
    """Parse filter like 'p1w1', 'p1w1d3', or 'all'."""
    import re

    if filter_str.lower() == "all":
        return None, None, None

    match = re.match(r"[pP](\d+)[wW](\d+)(?:[dD](\d+))?$", filter_str)
    if not match:
        raise ValueError(
            f"Invalid filter: {filter_str}. Use 'p1w1', 'p1w1d3', or 'all'"
        )

    phase = int(match.group(1))
    week = int(match.group(2))
    day = int(match.group(3)) if match.group(3) else None

    return phase, week, day


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_workouts.py plan.yaml <filter> [--no-schedule]")
        print("")
        print("Filter (required):")
        print("  p1w1      Phase 1 Week 1")
        print("  p1w1d3    Phase 1 Week 1 Day 3")
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

            # Validate: count required workouts
            required_workouts = [
                w
                for w in week_data["workouts"]
                if not w.get("skip_garmin") and w["type"] == "run"
            ]
            if len(required_workouts) > len(phase_training_days):
                print(
                    f"Error: Week {week_num} has {len(required_workouts)} workouts but only {len(phase_training_days)} training days"
                )
                sys.exit(1)

            for workout in week_data["workouts"]:
                if workout["type"] != "run" or workout.get("skip_garmin"):
                    continue

                day_num = workout["day"]

                if filter_day is not None and day_num != filter_day:
                    continue

                workout_date = calculate_workout_date(
                    start_date, week_num, day_num, phase_training_days
                )

                # Track week Monday (first training day of week)
                if week_monday is None and day_num == 1:
                    week_monday = workout_date

                # Print syncing message once
                if len(uploaded_names) == 0:
                    if filter_day:
                        print(f"Syncing {workout['garmin_name']}: {workout['name']}")
                    elif filter_week:
                        print(f"Syncing Phase {filter_phase} Week {filter_week}")
                    else:
                        print("Syncing all workouts...")

                try:
                    # Delete existing workout with same name
                    integration.delete_workout(workout["garmin_name"])

                    # Build workout directly from YAML steps
                    workout_json = integration.build_workout(workout)

                    # Upload workout
                    workout_id = integration.upload_workout(workout_json)

                    # Schedule workout (unless --no-schedule)
                    if not no_schedule:
                        integration.schedule_workout(workout_id, workout_date)

                    uploaded_dates.append(workout_date)
                    uploaded_names.append(workout["garmin_name"])

                except Exception as e:
                    print(f"Error: {e}")
                    sys.exit(1)

    # Result
    if not uploaded_dates:
        print("Error: No workouts found matching filter")
        sys.exit(1)

    # Format confirmation message
    if no_schedule:
        # Just uploaded, not scheduled
        if filter_day:
            print(f"✓ Uploaded to Garmin Connect")
        else:
            count = len(uploaded_names)
            print(f"✓ Uploaded {count} workout{'s' if count > 1 else ''} to Garmin Connect")
    else:
        # Uploaded and scheduled
        if filter_day:
            # Single workout: show title and date
            print(f"✓ Synced to Garmin Connect and scheduled for {uploaded_dates[0]}")
        elif filter_week:
            # Week: show Monday of week
            print(f"✓ Synced to Garmin Connect and scheduled for the week of {week_monday}")
        else:
            # All: just confirm
            print("✓ Synced to Garmin Connect")


if __name__ == "__main__":
    main()
