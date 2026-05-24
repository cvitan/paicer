import os
import re
from .plan_utils import calculate_workout_date, load_plan, validate_training_days


def parse_filter(filter_str: str) -> tuple[int | None, int | None, int | None]:
    """Parse filter like 'p1', 'w7', 'w7d2', or 'all'."""
    if filter_str.lower() == "all":
        return None, None, None

    match = re.match(r"[pP](\d+)$", filter_str)
    if match:
        return int(match.group(1)), None, None

    match = re.match(r"[wW](\d+)(?:[dD](\d+))?$", filter_str)
    if match:
        week = int(match.group(1))
        day = int(match.group(2)) if match.group(2) else None
        return None, week, day

    raise ValueError(
        f"Invalid filter: {filter_str}. Use 'p1', 'w7', 'w7d2', or 'all'"
    )


def _get_integration(name: str):
    if name == "garmin":
        from .integrations.garmin import GarminIntegration
        return GarminIntegration()
    raise ValueError(f"Integration '{name}' not found")


def run_sync(plan_file: str, filter_str: str, no_schedule: bool = False) -> None:
    """Sync workouts from plan to the configured integration."""
    filter_phase, filter_week, filter_day = parse_filter(filter_str)

    data = load_plan(plan_file)
    errors = validate_training_days(data)
    if errors:
        for e in errors:
            print(f"Error: {e}")
        raise SystemExit(1)

    start_date = data["plan"]["start_date"]
    global_training_days = data["plan"].get("training_days", [1, 2, 3, 4, 5, 6, 7])

    integration_name = os.getenv("WORKOUT_INTEGRATION", "garmin").lower()
    integration = _get_integration(integration_name)
    integration.authenticate()

    uploaded_dates = []
    uploaded_names = []
    skipped_workouts = []

    for phase in data["phases"]:
        phase_num = phase["phase"]
        if filter_phase is not None and phase_num != filter_phase:
            continue

        phase_training_days = phase.get("training_days", global_training_days)

        for week_data in phase["weeks"]:
            week_num = week_data["week"]
            if filter_week is not None and week_num != filter_week:
                continue

            for workout in week_data["workouts"]:
                day_num = workout["day"]
                if filter_day is not None and day_num != filter_day:
                    continue

                if workout.get("skip_garmin") or "garmin" not in workout:
                    skipped_workouts.append(workout)
                    continue

                garmin_name = f"W{week_num}: {workout['name']}"
                is_optional = workout.get("optional", False)

                workout_date = None
                if not is_optional or day_num <= len(phase_training_days):
                    workout_date = calculate_workout_date(
                        start_date, week_num, day_num, phase_training_days
                    )

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
                    integration.delete_workout(garmin_name)
                    garmin_workout = {**workout, "name": garmin_name}
                    workout_json = integration.build_workout(garmin_workout)
                    workout_id = integration.upload_workout(workout_json)

                    if not no_schedule and not is_optional and workout_date:
                        integration.schedule_workout(workout_id, workout_date)
                except Exception as e:
                    print(f"Error: {e}")
                    raise SystemExit(1)

                if workout_date and not is_optional:
                    uploaded_dates.append(workout_date)
                uploaded_names.append(garmin_name)

    if not uploaded_names:
        if skipped_workouts:
            for w in skipped_workouts:
                print(f"Skipped: {w['name']} (session set to skip Garmin sync)")
            return
        print("Error: No workouts found matching filter")
        raise SystemExit(1)

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
