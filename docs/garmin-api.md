# Garmin Workout API Reference

Technical reference for Garmin Connect workout JSON. Use when editing `garmin.steps` in plan YAML files.

## Sport Types

| sportTypeId | sportTypeKey | Sport |
|-------------|--------------|-------|
| 1 | running | Running (also used for track) |
| 2 | cycling | Cycling |
| 4 | swimming | Pool Swimming (cue card pattern) |
| 10 | multi_sport | Multisport/Brick (multiple legs) |

## Step Types

Use the string name in YAML — automatically converted to the ID:

| String (use in YAML) | ID | Purpose |
|----------------------|----|---------|
| `"warmup"` | 1 | Warm-up phase |
| `"cooldown"` | 2 | Cool-down phase |
| `"interval"` | 3 | Work interval |
| `"recovery"` | 4 | Recovery interval |
| `"rest"` | 5 | Rest step |
| `"repeat"` | 6 | Repeat group (contains nested steps) |

## End Condition Types

| String (use in YAML) | ID | Units | Description |
|----------------------|----|-------|-------------|
| `"lap.button"` | 1 | - | End on lap button press |
| `"time"` | 2 | seconds | End after time (e.g., 480 = 8min) |
| `"distance"` | 3 | meters | End after distance (e.g., 8000 = 8km) |
| `"calories"` | 4 | kcal | End after calories |
| `"power"` | 5 | watts | End at power |
| `"iterations"` | 7 | count | For repeat groups only |

**Special cases:**
- **Lap button:** Omit `endConditionValue`
- **Iterations:** Only for repeat groups, value = number of repeats

## Target Types

| String (use in YAML) | ID | Values | Description |
|----------------------|----|---------|-------------|
| `"no.target"` | 1 | - | No target (run by feel) |
| `"power.zone"` | 2 | `targetValueOne/Two: watts` | Power range |
| `"cadence"` | 3 | `targetValueOne/Two: rpm` | Cadence range |
| `"heart.rate.zone"` | 4 | `zoneNumber: 1-5` | HR zone |
| `"speed.zone"` | 5 | `targetValueOne/Two: m/s` | Speed/pace range |
| `"pace.zone"` | 6 | `targetValueOne/Two: sec/km` | Pace zone |
| `"grade"` | 7 | `targetValueOne/Two: %` | Grade/incline |

**Important:** Use `zoneNumber` field (not `targetValueOne`) for HR zones.

### Pace Targets

```yaml
targetType: "pace.zone"
targetValueOne: 310   # 5:10/km
targetValueTwo: 340   # 5:40/km
```

- Use `"pace.zone"` (ID 6), NOT `"speed.zone"` (ID 5)
- Values in **seconds per kilometer**
- Use +/-15 seconds from target pace for range

**Common pace conversions:**
| Pace (min:sec/km) | Seconds/km | m/s | +/-15 sec range (m/s) |
|-------------------|------------|-----|---------------------|
| 4:30 | 270 | 3.7037 | 3.9216 - 3.5088 |
| 5:00 | 300 | 3.3333 | 3.5088 - 3.1746 |
| 5:10 | 310 | 3.2258 | 3.3898 - 3.0769 |
| 5:25 | 325 | 3.0769 | 3.2258 - 2.9412 |
| 5:30 | 330 | 3.0303 | 3.1746 - 2.8986 |
| 6:00 | 360 | 2.7778 | 2.8986 - 2.6667 |
| 6:30 | 390 | 2.5641 | 2.6667 - 2.4691 |

## Step Examples

### Repeat Group

```yaml
- stepType: "repeat"
  numberOfIterations: 3
  childStepId: 1
  steps:
    - stepType: "interval"
      childStepId: 1  # Required inside repeat
    - stepType: "recovery"
      childStepId: 1
```

### Swim Rest Steps

Every swim workout needs rest steps between sections:

```yaml
- stepType: "warmup"
  endCondition: "lap.button"
  targetType: "no.target"
  description: "200m freestyle @ RPE 4-5"
- stepType: "rest"
  endCondition: "lap.button"
  targetType: "no.target"
- stepType: "interval"
  endCondition: "lap.button"
  targetType: "no.target"
  description: "200m drill"
- stepType: "rest"
  endCondition: "lap.button"
  targetType: "no.target"
- stepType: "cooldown"
  endCondition: "lap.button"
  targetType: "no.target"
  description: "100m easy"
```

Inside repeat groups, rest steps also need `childStepId: 1`.

## Required vs Optional Fields

**All steps require:** `stepType`, `endCondition`, `targetType` (swim steps auto-set to `null`)

**Optional:** `endConditionValue`, `targetValueOne`, `targetValueTwo`, `childStepId` (required inside repeats), `description` (watch display note)

**Auto-added by script:** `strokeType`, `equipmentType`, `drillType` (when `SWIM_TRACKING=drill`), `type` (ExecutableStepDTO/RepeatGroupDTO), `stepOrder`

## Swim Distance Tracking (`SWIM_TRACKING`)

Set in `.env`. Controls how pool swim segments track distance:

| Value | Behavior |
|-------|----------|
| `auto` (default) | Watch measures distance via stroke detection. Accurate with consistent form. |
| `drill` | Every segment is a drill. Press lap button → enter distance manually. Works regardless of stroke or form. |

When `drill` is set, the script adds `drillType: {drillTypeId: 3, drillTypeKey: "drill"}` to every swim step.

Available drill types (for future use): `kick` (1), `pull` (2), `drill` (3).

## Unit Reference

| Type | Unit | Examples |
|------|------|----------|
| Distance | meters | 1km = 1000, 5km = 5000 |
| Time | seconds | 1min = 60, 8min = 480, 15min = 900 |
| Speed | m/s | `1000 / pace_seconds` |

Source: [python-garminconnect](https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/workout.py)
