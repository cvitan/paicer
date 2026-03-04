"""Garmin Connect integration."""

import os
from dotenv import load_dotenv
from garminconnect import Garmin as GarminAPI
from .base import WorkoutIntegration

load_dotenv()


SPORT_TYPES = {
    "run": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
    "bike": {"sportTypeId": 2, "sportTypeKey": "cycling", "displayOrder": 2},
    "swim": {"sportTypeId": 4, "sportTypeKey": "swimming", "displayOrder": 3},
}

STROKE_TYPES = {
    "free": {"strokeTypeId": 6, "strokeTypeKey": "free", "displayOrder": 6},
    "any": {"strokeTypeId": 1, "strokeTypeKey": "any_stroke", "displayOrder": 1},
    "none": {"strokeTypeId": 0, "displayOrder": 0},
}

# Garmin API constants (actual values, library constants are wrong!)
STEP_TYPES = {
    "warmup": 1,
    "cooldown": 2,
    "interval": 3,
    "recovery": 4,
    "rest": 5,
    "repeat": 6,
}

CONDITION_TYPES = {
    "lap.button": 1,
    "time": 2,
    "distance": 3,
    "calories": 4,
    "power": 5,
    "iterations": 7,
}

TARGET_TYPES = {
    "no.target": 1,
    "power.zone": 2,
    "cadence": 3,
    "heart.rate.zone": 4,
    "speed.zone": 5,
    "pace.zone": 6,
    "grade": 7,
}


def resolve_step_type(value):
    """Convert step type to ID dict."""
    if isinstance(value, dict):
        return value
    return {"stepTypeId": STEP_TYPES.get(value, value)}


def resolve_condition_type(value):
    """Convert condition type to ID dict."""
    if isinstance(value, dict):
        return value
    return {"conditionTypeId": CONDITION_TYPES.get(value, value)}


def resolve_target_type(value):
    """Convert target type to ID dict."""
    if isinstance(value, dict):
        return value
    return {"workoutTargetTypeId": TARGET_TYPES.get(value, value)}


class GarminIntegration(WorkoutIntegration):
    """Garmin Connect workout integration."""

    def __init__(self):
        self.api = None
        self.tokenstore = os.path.expanduser("~/.garmin_tokens")

    def build_workout(self, workout_def: dict) -> dict:
        """Build Garmin workout JSON from YAML workout definition."""
        garmin_steps = workout_def["garmin"]["steps"]
        is_swim = workout_def.get("type") == "swim"

        # Convert YAML steps to Garmin JSON
        def convert_steps(steps_list, parent_child_id=None):
            converted = []
            child_id_counter = parent_child_id or 0

            for i, step in enumerate(steps_list):
                step_order = i + 1

                # Handle repeat groups
                if "numberOfIterations" in step:
                    child_id_counter += 1
                    current_child_id = child_id_counter

                    nested_steps, child_id_counter = convert_steps(
                        step["steps"], child_id_counter
                    )

                    repeat_step = {
                        "type": "RepeatGroupDTO",
                        "stepOrder": step_order,
                        "stepType": resolve_step_type(step["stepType"]),
                        "childStepId": current_child_id,
                        "numberOfIterations": step["numberOfIterations"],
                        "workoutSteps": nested_steps,
                        "smartRepeat": False,
                    }
                    converted.append(repeat_step)
                else:
                    exec_step = build_exec_step(step, step_order)
                    converted.append(exec_step)

            return converted, child_id_counter

        def build_exec_step(step, step_order):
            """Build a single executable step."""
            exec_step = {
                "type": "ExecutableStepDTO",
                "stepOrder": step_order,
                "stepType": resolve_step_type(step["stepType"]),
                "endCondition": resolve_condition_type(step["endCondition"]),
            }

            if "endConditionValue" in step:
                exec_step["endConditionValue"] = step["endConditionValue"]

            if "description" in step:
                exec_step["description"] = step["description"]

            exec_step["strokeType"] = STROKE_TYPES["none"]

            exec_step["equipmentType"] = {"equipmentTypeId": 0, "displayOrder": 0}

            if is_swim:
                exec_step["targetType"] = None
            else:
                exec_step["targetType"] = resolve_target_type(
                    step["targetType"]
                )
                if "targetValueOne" in step:
                    exec_step["targetValueOne"] = step["targetValueOne"]
                if "targetValueTwo" in step:
                    exec_step["targetValueTwo"] = step["targetValueTwo"]
                if "zoneNumber" in step:
                    exec_step["zoneNumber"] = step["zoneNumber"]

            if "childStepId" in step:
                exec_step["childStepId"] = step["childStepId"]

            if step.get("endCondition") == "distance":
                exec_step["preferredEndConditionUnit"] = {
                    "unitId": 2,
                    "unitKey": "kilometer",
                    "factor": 100000.0,
                }

            return exec_step

        workout_steps, _ = convert_steps(garmin_steps)

        sport_type = SPORT_TYPES.get(
            workout_def.get("type", "run"), SPORT_TYPES["run"]
        )
        workout = {
            "workoutName": workout_def["garmin_name"],
            "description": workout_def.get("description", ""),
            "sportType": sport_type,
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": sport_type,
                    "workoutSteps": workout_steps,
                }
            ],
        }

        return workout

    def authenticate(self):
        """Authenticate with Garmin Connect."""
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        if not email or not password:
            raise ValueError("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env file")

        try:
            self.api = GarminAPI(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )

            # Try to load existing tokens
            try:
                self.api.login(tokenstore=self.tokenstore)
            except Exception:
                # No tokens or expired - do fresh login
                result1, result2 = self.api.login()

                if result1 == "needs_mfa":
                    print("MFA required - check your email")
                    mfa_code = input("Enter MFA code: ").strip()
                    self.api.resume_login(result2, mfa_code)

                # Save tokens for next time
                self.api.garth.dump(self.tokenstore)

        except Exception as e:
            raise RuntimeError(f"Login failed: {e}")

    def upload_workout(self, workout_data: dict) -> str:
        """Upload workout to Garmin Connect."""
        result = self.api.upload_workout(workout_data)
        return str(result.get("workoutId"))

    def schedule_workout(self, workout_id: str, date: str):
        """Schedule workout to Garmin calendar."""
        url = f"/workout-service/schedule/{workout_id}"
        data = {"date": date}
        self.api.connectapi(url, method="POST", json=data)

    def delete_workout(self, workout_name: str) -> bool:
        """Delete Garmin workout by name."""
        try:
            workouts = self.api.get_workouts()
            for workout in workouts:
                if workout.get("workoutName") == workout_name:
                    workout_id = workout.get("workoutId")
                    url = f"/workout-service/workout/{workout_id}"
                    self.api.connectapi(url, method="DELETE")
                    return True
            return False
        except Exception:
            return False
