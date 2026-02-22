# Garmin Workout Structure Reference

Reference for Garmin Connect workout JSON structure. Use this when editing `garmin.steps` in plan YAML files.

## Sport Types

```yaml
sportType:
  sportTypeId: 1
  sportTypeKey: "running"
  displayOrder: 1
```

| sportTypeId | sportTypeKey | Sport |
|-------------|--------------|-------|
| 1 | running | Running |
| 2 | cycling | Cycling |
| 3 | swimming | Swimming |
| 4 | walking | Walking |
| 5 | multi_sport | Multi-sport |
| 6 | fitness_equipment | Fitness Equipment |
| 7 | hiking | Hiking |

## Step Types

In YAML, use the readable string name - it's automatically converted to the ID:

```yaml
stepType: "interval"
```

| String (use in YAML) | ID | Purpose |
|----------------------|----|---------|
| `"warmup"` | 1 | Warm-up phase |
| `"cooldown"` | 2 | Cool-down phase |
| `"interval"` | 3 | Work interval |
| `"recovery"` | 4 | Recovery interval |
| `"rest"` | 5 | Rest step |
| `"repeat"` | 6 | Repeat group (contains nested steps) |

## End Condition Types

In YAML, use the readable string name:

```yaml
endCondition: "distance"
endConditionValue: 8000  # 8km in meters
```

| String (use in YAML) | ID | Units | Description |
|----------------------|----|-------|-------------|
| `"lap.button"` | 1 | - | End on lap button press |
| `"time"` | 2 | seconds | End after time (e.g., 480 = 8min) |
| `"distance"` | 3 | meters | End after distance (e.g., 8000 = 8km) |
| `"calories"` | 4 | kcal | End after calories |
| `"power"` | 5 | watts | End at power |
| `"iterations"` | 7 | count | For repeat groups only |

**Special cases:**
- **Lap button:** Use `conditionTypeId: 1, conditionTypeKey: "lap.button"`, omit `endConditionValue`
- **Iterations:** Only for repeat groups, value = number of repeats

## Target Types

In YAML, use the readable string name:

```yaml
targetType: "speed.zone"
targetValueOne: 3.05  # min speed (m/s)
targetValueTwo: 3.11  # max speed (m/s)
```

| String (use in YAML) | ID | Values | Description |
|----------------------|----|---------|-------------|
| `"no.target"` | 1 | - | No target (run by feel) |
| `"power.zone"` | 2 | `targetValueOne/Two: watts` | Power range |
| `"cadence"` | 3 | `targetValueOne/Two: rpm` | Cadence range |
| `"heart.rate.zone"` | 4 | `targetValueOne: zone` | HR zone (1-5) |
| `"speed.zone"` | 5 | `targetValueOne/Two: m/s` | Speed/pace range |
| `"pace.zone"` | 6 | `targetValueOne/Two: ?` | Pace zone (alternative) |
| `"grade"` | 7 | `targetValueOne/Two: %` | Grade/incline |

### Heart Rate Zones

```yaml
targetType: "heart.rate.zone"
zoneNumber: 2
```

**Important:** Use `zoneNumber` field, not `targetValueOne` for HR zones.

**HR Zones:**
- Zone 1: Recovery (50-60% max HR)
- Zone 2: Easy/Aerobic (60-70% max HR)
- Zone 3: Tempo (70-80% max HR)
- Zone 4: Threshold (80-90% max HR)
- Zone 5: VO2max (90-100% max HR)

### Pace Targets

```yaml
targetType: "pace.zone"
targetValueOne: 310   # Minimum pace in seconds/km (5:10/km)
targetValueTwo: 340   # Maximum pace in seconds/km (5:40/km)
```

**Important:**
- Use `"pace.zone"` (ID 6), NOT `"speed.zone"` (ID 5)
- Values are in **seconds per kilometer**, not m/s
- Use ±15 seconds from target pace for range

**Conversion:**
- Pace min:sec/km → m/s using: `speed = 1000 / (pace_seconds)`
- Example: 5:25/km = 325 seconds → 1000/325 = 3.08 m/s
- Range: Use ±15 seconds from target
  - 5:10/km (310 sec) = 3.2258 m/s (faster)
  - 5:40/km (340 sec) = 2.9412 m/s (slower)

**Common pace conversions to m/s:**
| Pace (min:sec/km) | Seconds/km | m/s (exact) | ±15 sec range (m/s) |
|-------------------|------------|-------------|---------------------|
| 4:30 | 270 | 3.7037 | 3.9216 - 3.5088 |
| 5:00 | 300 | 3.3333 | 3.5088 - 3.1746 |
| 5:10 | 310 | 3.2258 | 3.3898 - 3.0769 |
| 5:25 | 325 | 3.0769 | 3.2258 - 2.9412 |
| 5:30 | 330 | 3.0303 | 3.1746 - 2.8986 |
| 6:00 | 360 | 2.7778 | 2.8986 - 2.6667 |
| 6:30 | 390 | 2.5641 | 2.6667 - 2.4691 |

## Complete Step Examples

### Simple Distance Step (e.g., Easy 8km)

```yaml
- stepType: "interval"
  endCondition: "distance"
  endConditionValue: 8000  # 8km
  targetType: "no.target"
```

### Warmup with Distance

```yaml
- stepType: "warmup"
  endCondition: "distance"
  endConditionValue: 2000  # 2km
  targetType: "heart.rate.zone"
  zoneNumber: 2
```

### Interval with Time + Pace Target

```yaml
- stepType: "interval"
  endCondition: "time"
  endConditionValue: 480  # 8 minutes (in seconds)
  targetType: "pace.zone"
  targetValueOne: 3.2258  # 5:10/km in m/s (faster)
  targetValueTwo: 2.9412  # 5:40/km in m/s (slower)
  childStepId: 1  # Required when inside repeat group
```

### Recovery Step

```yaml
- stepType: "recovery"
  endCondition: "time"
  endConditionValue: 120  # 2 minutes
  targetType: "no.target"
  childStepId: 1
```

### Lap Button Recovery

```yaml
- stepType: "recovery"
  endCondition: "lap.button"
  targetType: "no.target"
  childStepId: 1
```

Note: No `endConditionValue` for lap button!

### Repeat Group

```yaml
- stepType: "repeat"
  numberOfIterations: 3  # Repeat 3 times
  childStepId: 1  # Required
  steps:
    # Nested steps here (work + recovery)
    - stepType: "interval"
      # ... work interval ...
      childStepId: 1  # Required for steps inside repeat
    - stepType: "recovery"
      # ... recovery ...
      childStepId: 1
```

**Important:**
- Repeat groups need `childStepId`
- Steps inside repeats need `childStepId` (usually same as parent)
- `numberOfIterations` = how many times to repeat

## Common Workout Patterns

### Easy Run (8km)

```yaml
garmin:
  steps:
    - stepType: "interval"
      endCondition: "distance"
      endConditionValue: 8000
      targetType: "heart.rate.zone"
      zoneNumber: 2
```

### Tempo Intervals (2km WU + 3×8min @ pace + 2km CD)

```yaml
garmin:
  steps:
    # Warmup
    - stepType: "warmup"
      endCondition: "distance"
      endConditionValue: 2000
      targetType: "heart.rate.zone"
      zoneNumber: 2

    # Main set
    - stepType: "repeat"
      numberOfIterations: 3
      childStepId: 1
      steps:
        - stepType: "interval"
          endCondition: "time"
          endConditionValue: 480
          targetType: "pace.zone"
          targetValueOne: 3.2258  # 5:10/km (faster)
          targetValueTwo: 2.9412  # 5:40/km (slower)
          childStepId: 1

        - stepType: "recovery"
          endCondition: "time"
          endConditionValue: 120
          targetType: "no.target"
          childStepId: 1

    # Cooldown
    - stepType: "cooldown"
      endCondition: "distance"
      endConditionValue: 2000
      targetType: "heart.rate.zone"
      zoneNumber: 2
```

### Strides (7km + 4×20sec with lap button)

```yaml
garmin:
  steps:
    # Easy portion
    - stepType: "interval"
      endCondition: "distance"
      endConditionValue: 7000
      targetType: "heart.rate.zone"
      zoneNumber: 2

    # Strides
    - stepType: "repeat"
      numberOfIterations: 4
      childStepId: 1
      steps:
        - stepType: "interval"
          endCondition: "time"
          endConditionValue: 20
          targetType: "no.target"
          childStepId: 1

        - stepType: "recovery"
          endCondition: "lap.button"
          targetType: "no.target"
          childStepId: 1
```

## Required vs Optional Fields

### All Steps Require

- `stepType` - Type of step
- `endCondition` - How step ends
- `targetType` - Performance target

### Optional Fields

- `endConditionValue` - Value for condition (not needed for lap button)
- `targetValueOne` - Min target value
- `targetValueTwo` - Max target value (for ranges)
- `childStepId` - Required for steps inside repeat groups

### Auto-Added by Script

These are added automatically - don't include in YAML:
- `strokeType: {strokeTypeId: 0, displayOrder: 0}`
- `equipmentType: {equipmentTypeId: 0, displayOrder: 0}`
- `type: "ExecutableStepDTO"` or `"RepeatGroupDTO"`
- `stepOrder` - Calculated from position in list

## Tips

**Distance values:**
- Always in meters
- 1km = 1000m
- 5km = 5000m

**Time values:**
- Always in seconds
- 1 minute = 60s
- 8 minutes = 480s
- 15 minutes = 900s

**Speed values:**
- Always in meters/second (m/s)
- Use pace calculator: `speed = 1000 / (pace_min_km * 60)`
- Garmin needs min/max for ranges: `targetValueOne` (slower), `targetValueTwo` (faster)

**HR Zones:**
- Use single value in `targetValueOne`
- Common: Zone 2 (easy), Zone 3-4 (tempo/threshold), Zone 5 (hard)

**childStepId:**
- Required for repeat groups
- Required for all steps inside repeat groups
- Usually just set to 1
- Increment if you have nested repeats

## Source

Values from [python-garminconnect workout.py](https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/workout.py)
