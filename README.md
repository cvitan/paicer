# p**ai**cer

A tool for creating structured training plans and sync workouts to devices. Currently supports Garmin Connect.

**From one YAML file:**
- Structured workouts (auto-scheduled to calendar via integration)
- Markdown document (digital reading)
- HTML document (printable, one week per page)

## Quick Start

```bash
# Install dependencies
uv sync

# Set Garmin credentials and plan
cp .env.example .env


# Generate documents
make markdown               # Generate Markdown
make html                   # Generate HTML (letter, default)
make html FORMAT=a4         # Generate HTML (A4)

# Upload workouts to Garmin
make workouts SCOPE=p1w1    # Upload Phase 1 Week 1
make workouts SCOPE=p1w1d1  # Upload Phase 1 Week 1 Day 1 only
make workouts SCOPE=all     # Upload everything (use with caution)
```

## Creating Your Own Plan

1. Copy an example: `cp plans/hm-tri-combo.yaml plans/my-plan.yaml`
2. Edit your plan (use Claude Code or any agent for help)
3. Set as default in `.env`: `PLAN=plans/my-plan.yaml`
4. Generate: `make markdown`
5. Upload: `make workouts SCOPE=p1w1`

See `plans/` for example plans. All generated files go to `output/` (gitignored).

## YAML Structure

### Required Fields

**Plan level:**
```yaml
plan:
  name: "Plan Name"
  start_date: "YYYY-MM-DD"  # Only date in entire file
  training_days: [1, 3, 5, 7]  # Mon, Wed, Fri, Sun (1=Mon, 7=Sun)
  overview: |
    Multi-line overview including:
    - Race information
    - Pacing philosophy
    - RPE scale definitions
```

**Phase level:**
```yaml
phases:
  - phase: 1  # Sequential number
    name: "Phase Name"
    # training_days: [1, 2, 3, 5, 7]  # Optional: override global
    description: |
      Multi-line description including:
      - Phase goals
      - Format (e.g., "4 runs/week + 2 bikes")
```

**Week level:**
```yaml
weeks:
  - week: 1  # Sequential number
    description: |
      Multi-line description including:
      - Weekly goal/focus
      - Volume (e.g., "~40km running")
    workouts:
      # workout list
```

**Workout level:**
```yaml
- day: 1  # 1-7 (Mon-Sun), sequential not tied to calendar
  type: "run"
  name: "Tempo Intervals"
  garmin_name: "W1D2: Tempo 3x8min"  # Format: W{week}D{day}
  description: "Full workout description with RPE, paces, coaching notes"
  distance: 8000  # Optional, for display in markdown
  garmin:  # Direct Garmin step structure
    steps:
      - stepType: "warmup"
        endCondition: "distance"
        endConditionValue: 2000
        # ... more fields (see Garmin Reference below)
```

### Key Design Principles

1. **Single date** - Only `start_date` in YAML, all else calculated
2. **Natural text** - Use multiline descriptions, not structured fields
3. **No redundancy** - If it can be calculated, don't store it
4. **Clear separation** - Plan structure vs Garmin workout structure

### Date Calculation

- `day` field is 1-7, NOT a weekday name
- Workouts don't have date fields
- Dates calculated: first Monday on or after `start_date` + (week-1)*7 + (day-1)
- To shift entire plan: change `start_date`

### Workout Step Patterns

**Key fields in each step:**
- `stepType` - Type: `"warmup"`, `"interval"`, `"recovery"`, `"cooldown"`, `"repeat"`
- `endCondition` - How it ends: `"distance"`, `"time"`, `"lap.button"`, `"iterations"`
- `targetType` - Performance target: `"no.target"`, `"heart.rate.zone"`, `"pace.zone"`

**When to use each step type:**
- Easy runs → Single `interval` step with `heart.rate.zone` target
- Tempo/intervals → `warmup` + `repeat` group + `cooldown`
- Strides → Easy `interval` + `repeat` group with lap button recovery
- Pool swims → `lap.button` cue card steps with `description` + `rest` between sections
- Open water swims → `skip_garmin: true` (no structured workouts on Garmin)

**Swim workouts (cue card pattern):**

Swim Garmin export is intentionally simple — structured swim workouts with auto-distance tracking and stroke detection tend to cause more trouble than benefit in the pool. Instead, each step shows what to do next on the watch as a cue card, and you press the lap button when ready to move on.

- Set `type: "swim"` — the script auto-sets `sportTypeId: 4`, `targetType: null`, `strokeType: none`
- Every step uses `endCondition: "lap.button"` with a `description` for the watch display
- Add `rest` steps (lap.button) between every section for recovery between sets
- Reusable sessions are YAML anchors in `swim_sessions:` at the top of the plan file
- Reference anchors with `garmin: *swim_s2_garmin` (YAML anchors must be defined before use)

**Optional workouts (skip Garmin upload):**
```yaml
- day: 5
  type: "bike"
  name: "Easy Ride (optional, 1-2x this week)"
  skip_garmin: true
  description: "45–60 min easy spin"
```

## Building Plans

### Gather Information

- Goal race(s) and dates
- Current fitness level and training history
- Available training days per week
- Preferred training methodology (Pfitzinger, Daniels, etc.)
- Pacing philosophy and intensity approach

### Common Training Methodologies

**Pfitzinger (Marathon/HM):** 4-6 runs/week, long run progression, tempo/threshold work, lactate threshold intervals.

**Daniels (Running):** Easy (RPE 4-5), Tempo (RPE 6-7), Interval (RPE 8-9), Repetition (RPE 9).

**Triathlon:** Multi-sport progression, brick workouts (bike→run), swim/bike/run balance, pool swim cue cards, open water prep.

### RPE Scale

| RPE | Description |
|-----|-------------|
| 4-5 | Easy/conversational |
| 6-7 | Tempo/threshold |
| 8-9 | Hard intervals/race pace |

### Common Patterns

**Progressive volume:** Base → Build → Peak → Recovery/taper

**Quality session placement:** Tue intervals/tempo, Thu recovery, Sat/Sun long run

**Phase transitions:** Recovery week between phases, gradual intensity increase, taper before races

### Quality Checks

- Verify `start_date` is set
- Check week/day numbers are sequential
- Ensure `garmin_name` follows W{week}D{day} format
- Validate pace values are reasonable (e.g., 4:00-6:30/km)
- Check descriptions include RPE and coaching notes
- Test YAML with `make test`

## Example Sessions

### Easy Run (8km)

```yaml
- day: 1
  type: "run"
  name: "Easy"
  garmin_name: "W1D1: Easy 8km"
  distance: 8000
  description: "8km easy at RPE 4-5. Conversational pace."
  garmin:
    steps:
      - stepType: "interval"
        endCondition: "distance"
        endConditionValue: 8000
        targetType: "heart.rate.zone"
        zoneNumber: 2
```

### Tempo Intervals (3x8min @ pace)

See `plans/hm-tri-combo.yaml` Week 1 Day 2. Structure:
- Warmup step (2km, HR Zone 2)
- Repeat group (3 iterations)
  - Work interval (8min, pace target)
  - Recovery interval (2min, no target)
- Cooldown step (2km, HR Zone 2)

### Easy Run + Strides (7km + 4x20sec)

See `plans/hm-tri-combo.yaml` Week 1 Day 3. Structure:
- Easy interval (7km, HR Zone 2)
- Repeat group (4 iterations)
  - Stride interval (20sec, no target)
  - Recovery interval (lap button, no target)

### Pool Swim Session (YAML anchor reference)

```yaml
- day: 1
  type: "swim"
  name: "Swim: Session #2"
  garmin_name: "W7D1: Swim #2"
  garmin: *swim_s2_garmin
  description: "1.5 km. Drills/Intervals at RPE 5-7."
```

### Inline Easy Swim

```yaml
- day: 3
  type: "swim"
  name: "Swim: Easy"
  garmin_name: "W13D1: Easy Swim"
  garmin:
    steps:
      - stepType: "interval"
        endCondition: "lap.button"
        targetType: "no.target"
        description: "1.5 km easy freestyle @ RPE 4-5"
  description: "Easy 1.5 km at RPE 4-5."
```

### Open Water Swim (no Garmin)

```yaml
- day: 5
  type: "swim"
  name: "Swim: Open Water"
  skip_garmin: true
  description: "1.5 km. Practice sighting, wetsuit fitting."
```

For complete working examples, see `plans/hm-tri-combo.yaml` (22-week plan).

---

# Garmin Workout Reference

Technical reference for Garmin Connect workout JSON. Use when editing `garmin.steps` in YAML.

## Sport Types

| sportTypeId | sportTypeKey | Sport |
|-------------|--------------|-------|
| 1 | running | Running |
| 2 | cycling | Cycling |
| 4 | swimming | Pool Swimming (cue card pattern) |

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
targetValueOne: 310   # 5:10/km in seconds
targetValueTwo: 340   # 5:40/km in seconds
```

- Use `"pace.zone"` (ID 6), NOT `"speed.zone"` (ID 5)
- Values in **seconds per kilometer**
- Use ±15 seconds from target pace for range

**Common pace conversions:**
| Pace (min:sec/km) | Seconds/km | m/s | ±15 sec range (m/s) |
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

**Auto-added by script:** `strokeType`, `equipmentType`, `type` (ExecutableStepDTO/RepeatGroupDTO), `stepOrder`

## Unit Reference

| Type | Unit | Examples |
|------|------|----------|
| Distance | meters | 1km = 1000, 5km = 5000 |
| Time | seconds | 1min = 60, 8min = 480, 15min = 900 |
| Speed | m/s | `1000 / pace_seconds` |

Source: [python-garminconnect](https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/workout.py)

---

## Roadmap

### 1. Garmin Integration Enhancements

**Cycling workouts:**
- Power zones support
- FTP-based intervals
- Brick session structure (bike + run transition)

**Multi-sport workouts:**
- Triathlon race simulation
- Transition practice

### 2. Reviews Section

Add a reviews section to the YAML schema:
```yaml
reviews:
  - week: 4
    date: "2026-04-15"
    notes: "HR averaged 162 during easy runs (target <145). Suggest slowing easy pace to 6:15/km."
    adjustments:
      - field: "phases[0].weeks[3].workouts[0].description"
        change: "Easy pace adjusted from 6:00 to 6:15/km"
```

### 3. Agent Skill

Create a skill for interactive plan building and weekly reviews:
- Ask about fitness, training days, goals
- Suggest methodology (Pfitzinger, Daniels, etc.)
- Build YAML plan interactively
- Generate and upload workouts
- Weekly check-ins: pull data, compare to plan, suggest adjustments
- Pace adjustment based on race results
- Recovery week auto-insertion
- Taper week builder

### 4. Additional Formatters

- PDF (reportlab)
- iCal (.ics for Apple/Google Calendar)
- JSON (API consumption)
- CSV (spreadsheet import)

### 5. New Integrations

- Strava (workout library)
- Zwift (cycling workouts)
