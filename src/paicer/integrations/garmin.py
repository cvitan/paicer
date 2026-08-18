"""Garmin Connect integration."""

import os
from garminconnect import Garmin as GarminAPI
from .base import WorkoutIntegration
from ..config import get_swim_tracking, get_units


SPORT_TYPES = {
    "run": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
    "track": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
    "bike": {"sportTypeId": 2, "sportTypeKey": "cycling", "displayOrder": 2},
    "swim": {"sportTypeId": 4, "sportTypeKey": "swimming", "displayOrder": 3},
    "strength": {
        "sportTypeId": 5,
        "sportTypeKey": "strength_training",
        "displayOrder": 5,
    },
    "multisport": {
        "sportTypeId": 10,
        "sportTypeKey": "multi_sport",
        "displayOrder": 4,
    },
}

# Garmin weight units. Factor is grams per unit — Garmin's weight base unit
# is grams. The pound entry is confirmed against a real Connect workout.
WEIGHT_UNITS = {
    "imperial": {"unitId": 9, "unitKey": "pound", "factor": 453.59237},
    "metric": {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0},
}

STROKE_TYPES = {
    "free": {"strokeTypeId": 6, "strokeTypeKey": "free", "displayOrder": 6},
    "any": {"strokeTypeId": 1, "strokeTypeKey": "any_stroke", "displayOrder": 1},
    "none": {"strokeTypeId": 0, "displayOrder": 0},
}

DRILL_TYPES = {
    "kick": {"drillTypeId": 1, "drillTypeKey": "kick"},
    "pull": {"drillTypeId": 2, "drillTypeKey": "pull"},
    "drill": {"drillTypeId": 3, "drillTypeKey": "drill"},
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
    "reps": 10,
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
        self.client = None
        self.tokenstore = os.path.expanduser("~/.garmin_tokens")
        self.swim_tracking = get_swim_tracking()
        self.units = get_units()

    def build_workout(self, workout_def: dict) -> dict:
        """Build Garmin workout JSON from YAML workout definition."""
        if workout_def.get("type") == "multisport":
            return self._build_multisport(workout_def)
        return self._build_single_sport(workout_def)

    def _build_single_sport(self, workout_def: dict) -> dict:
        """Build a single-sport Garmin workout."""
        garmin_steps = workout_def["garmin"]["steps"]
        sport = workout_def.get("type", "run")
        workout_steps, _ = self._convert_steps(garmin_steps, sport)

        sport_type = SPORT_TYPES.get(
            workout_def.get("type", "run"), SPORT_TYPES["run"]
        )
        return {
            "workoutName": workout_def["name"],
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

    def _build_multisport(self, workout_def: dict) -> dict:
        """Build a multisport Garmin workout with multiple legs."""
        legs = workout_def["garmin"]["legs"]
        segments = []
        global_step_order = 0

        for i, leg in enumerate(legs):
            sport = leg["sport"]
            sport_type = SPORT_TYPES.get(sport, SPORT_TYPES["run"])
            leg_steps, _ = self._convert_steps(
                leg["steps"], sport, step_offset=global_step_order,
            )
            global_step_order += len(leg_steps)

            segments.append({
                "segmentOrder": i + 1,
                "sportType": sport_type,
                "workoutSteps": leg_steps,
            })

        return {
            "workoutName": workout_def["name"],
            "description": workout_def.get("description", ""),
            "sportType": SPORT_TYPES["multisport"],
            "workoutSegments": segments,
            "isSessionTransitionEnabled": True,
        }

    def _convert_steps(
        self, steps_list, sport,
        parent_child_id=None, step_offset=0,
    ):
        """Convert YAML steps to Garmin JSON."""
        converted = []
        child_id_counter = parent_child_id or 0

        for i, step in enumerate(steps_list):
            step_order = step_offset + i + 1

            if "numberOfIterations" in step:
                child_id_counter += 1
                current_child_id = child_id_counter

                nested_steps, child_id_counter = self._convert_steps(
                    step["steps"], sport, child_id_counter
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
                exec_step = self._build_exec_step(step, step_order, sport)
                converted.append(exec_step)

        return converted, child_id_counter

    def _build_exec_step(self, step, step_order, sport):
        """Build a single executable step."""
        is_swim = sport == "swim"
        is_strength = sport == "strength"
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
            if self.swim_tracking == "drill":
                exec_step["drillType"] = DRILL_TYPES["drill"]
        elif is_strength and step.get("stepType") == "rest":
            # Connect emits null — not no.target — for strength rest steps.
            # Applied here so plan YAML omits targetType on rest steps.
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

        if is_strength:
            self._apply_strength_fields(exec_step, step)

        if "childStepId" in step:
            exec_step["childStepId"] = step["childStepId"]

        if step.get("endCondition") == "distance":
            exec_step["preferredEndConditionUnit"] = {
                "unitId": 2,
                "unitKey": "kilometer",
                "factor": 100000.0,
            }

        return exec_step

    def _apply_strength_fields(self, exec_step, step):
        """Attach exercise identity and prescribed load to a strength step.

        Applied to *every* strength step, rest included. That is
        deliberate and matches Connect: a rest step in a Garmin-authored
        strength workout carries `weightUnit` (and null `weightValue`)
        just like a work step — only `category`/`exerciseName` are absent,
        and those are omitted here because rest steps don't declare them.
        Verified by round-tripping an uploaded workout, 2026-08-18.
        """
        for field in ("category", "exerciseName"):
            if field in step:
                exec_step[field] = step[field]

        unit = WEIGHT_UNITS.get(self.units, WEIGHT_UNITS["metric"])
        exec_step["weightUnit"] = unit

        # Garmin's weight base unit is grams (the unit factor is grams per
        # unit), mirroring how distance is stored in metres with a separate
        # display unit. YAML weightValue is written in the user's own unit.
        if step.get("weightValue") is not None:
            exec_step["weightValue"] = round(
                step["weightValue"] * unit["factor"], 2
            )
        else:
            exec_step["weightValue"] = None

    def authenticate(self):
        import keyring
        import click
        from ..config import get_garmin_email, read_config, write_config

        email = get_garmin_email()
        if not email:
            email = click.prompt("Garmin email")
            cfg = read_config()
            cfg["garmin_email"] = email
            write_config(cfg)

        password = keyring.get_password("paicer", email)
        if not password:
            password = click.prompt(f"Garmin password for {email}", hide_input=True)
            keyring.set_password("paicer", email, password)

        self.client = GarminAPI(
            email, password,
            prompt_mfa=lambda: click.prompt("Garmin MFA code (check your email)"),
        )
        try:
            self.client.login(tokenstore=self.tokenstore)
        except FileNotFoundError:
            self.client.login()
            self.client.garth.dump(self.tokenstore)

    def upload_workout(self, workout_data: dict) -> str:
        """Upload workout to Garmin Connect."""
        result = self.client.upload_workout(workout_data)
        return str(result.get("workoutId"))

    def schedule_workout(self, workout_id: str, date: str):
        """Schedule workout to Garmin calendar."""
        url = f"/workout-service/schedule/{workout_id}"
        data = {"date": date}
        self.client.connectapi(url, method="POST", json=data)

    def delete_workout(self, workout_name: str) -> bool:
        """Delete Garmin workout by name."""
        try:
            workouts = self.client.get_workouts()
            for workout in workouts:
                if workout.get("workoutName") == workout_name:
                    workout_id = workout.get("workoutId")
                    url = f"/workout-service/workout/{workout_id}"
                    self.client.connectapi(url, method="DELETE")
                    return True
            return False
        except Exception:
            return False
