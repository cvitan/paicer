# Guide for Claude: Building Training Plans with p**ai**cer

This guide helps Claude Code assist users in creating training plans using paicer.

## System Overview

This tool generates workout integration workouts and printable documents from a single YAML plan file.

**From one YAML file:**
- Structured workouts (auto-scheduled to calendar via integration)
- Markdown document (digital reading)
- HTML document (printable, one week per page)

## YAML Structure

### Required Fields

**Plan level:**
```yaml
plan:
  name: "Plan Name"
  start_date: "YYYY-MM-DD"  # Only date in entire file
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
  garmin:  # Direct workout integration step structure
    steps:
      - stepType: "warmup"
        endCondition: "distance"
        endConditionValue: 2000
        # ... more fields ...
```

### Key Design Principles

1. **Single date** - Only `start_date` in YAML, all else calculated
2. **Natural text** - Use multiline descriptions, not structured fields
3. **No redundancy** - If it can be calculated, don't store it
4. **Clear separation** - Plan structure vs workout integration workout structure

### Date Calculation

- `day` field is 1-7, NOT a weekday name
- Workouts don't have date fields
- Dates calculated: first Monday on or after `start_date` + (week-1)*7 + (day-1)
- To shift entire plan: change `start_date`

### workout integration Workout Structure

All workouts use the `garmin.steps` structure. See [integrations/garmin.md](integrations/garmin.md) for complete technical details.

**Key fields in each step:**
- `stepType` - Type: `"warmup"`, `"interval"`, `"recovery"`, `"cooldown"`, `"repeat"`
- `endCondition` - How it ends: `"distance"`, `"time"`, `"lap.button"`, `"iterations"`
- `targetType` - Performance target: `"no.target"`, `"heart.rate.zone"`, `"pace.zone"`

**When to use each step type:**
- Easy runs → Single `interval` step with `heart.rate.zone` target
- Tempo/intervals → `warmup` + `repeat` group + `cooldown`
- Strides → Easy `interval` + `repeat` group with lap button recovery

**Optional workouts (skip workout integration upload):**
```yaml
- day: 5
  type: "bike"
  name: "Easy Ride (optional, 1-2x this week)"
  skip_garmin: true
  description: "45–60 min easy spin"
```

## Helping Users Build Plans

### Step 1: Gather Information

Ask about:
- Goal race(s) and dates
- Current fitness level and training history
- Available training days per week
- Preferred training methodology (Pfitzinger, Daniels, etc.)
- Pacing philosophy and intensity approach

### Step 2: Design Plan Structure

Create phases based on:
- Time to race
- Training progression
- Periodization principles

### Step 3: Build YAML

Start with:
1. Plan overview (races, philosophy, RPE scale)
2. Phase structure (sequential phases)
3. Week-by-week progression
4. Individual workouts with workout integration structure

### Step 4: Workout Structure Selection

**When to use each step pattern:**
- Single interval step - Easy runs, long runs (with HR zone target)
- Warmup + repeat + cooldown - Quality sessions with specific paces/zones
- Easy interval + repeat (lap button) - Easy runs with strides/pickups

Reference [integrations/garmin.md](integrations/garmin.md) for complete step structure details.

### Step 5: Pacing Guidelines

**RPE scale standard:**
- RPE 4-5: Easy/conversational
- RPE 6-7: Tempo/threshold
- RPE 8-9: Hard intervals/race pace

Convert RPE to:
- Specific paces (e.g., 5:25/km) for `intervals`
- Heart rate zones for warmup/cooldown
- No target for easy runs

## Common Training Methodologies

### Pfitzinger (Marathon/HM)
- 4-6 runs per week
- Long run progression
- Tempo/threshold work
- Recovery runs
- Lactate threshold intervals

### Daniels (Running)
- Easy runs (RPE 4-5)
- Tempo runs (RPE 6-7)
- Interval work (RPE 8-9)
- Repetition work (RPE 9)

### Triathlon Plans
- Multi-sport progression
- Brick workouts (bike→run)
- Swim/bike/run balance
- Open water preparation

## Example Session Translations

For complete working examples with full workout integration step structure, see `plans/hm-tri-combo.yaml`.

### "Easy 8km run"
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

### "3 × 8min @ tempo with 2min recovery"

See full example in `plans/hm-tri-combo.yaml` Week 1 Day 2. Structure:
- Warmup step (2km, HR Zone 2)
- Repeat group (3 iterations)
  - Work interval (8min, pace target)
  - Recovery interval (2min, no target)
- Cooldown step (2km, HR Zone 2)

### "Easy 7km + 4 strides"

See full example in `plans/hm-tri-combo.yaml` Week 1 Day 3. Structure:
- Easy interval (7km, HR Zone 2)
- Repeat group (4 iterations)
  - Stride interval (20sec, no target)
  - Recovery interval (lap button, no target)

## Tips for Building Plans

1. **Start simple** - Get basic structure working, then add complexity
2. **Test generation** - Run `make markdown` frequently to check output
3. **One phase at a time** - Build Phase 1 completely before adding Phase 2
4. **Use examples** - Reference `plans/hm-tri-combo.yaml` for working workout integration step patterns
5. **Validate early** - Run `make test` to catch YAML errors
6. **Reference docs** - See [integrations/garmin.md](integrations/garmin.md) for all step types and targets

## Common Patterns

**Progressive volume:**
- Week 1: Base
- Week 2-4: Build
- Week 5: Peak
- Week 6: Recovery/taper

**Quality session placement:**
- Tuesday: Intervals/tempo
- Thursday: Recovery or easy
- Saturday/Sunday: Long run

**Phase transitions:**
- Recovery week between phases
- Gradual intensity increase
- Taper before races

## Output Formats

The system generates:
1. **workout integration workouts** - Structured, scheduled, synced to watch
2. **Markdown** - Full plan with dates
3. **HTML** - Printable, one week per page

All stay in sync from single YAML source.

## Building New Workout Patterns

All workouts use the `garmin.steps` structure - there's no need to add new "types".

To build a new workout pattern:
1. Study similar patterns in `plans/hm-tri-combo.yaml`
2. Reference [integrations/garmin.md](integrations/garmin.md) for step types and targets
3. Compose steps to achieve the desired structure
4. Test with `make workouts SCOPE=p1w1d1`

Example: "5 × 3min uphill at RPE 8"
- Use warmup + repeat + cooldown pattern
- Work interval: 3min time, no target (or grade target if supported)
- Recovery interval: lap button or time
- Reference Week 1 Day 2 in example plan for pattern

## Quality Checks

When helping users build plans:
- ✅ Verify `start_date` is set
- ✅ Check week/day numbers are sequential
- ✅ Ensure `garmin_name` follows W{week}D{day} format
- ✅ Validate pace values are reasonable (e.g., 4:00-6:30/km)
- ✅ Check descriptions include RPE and coaching notes
- ✅ Test YAML with `make test`

## Reference

See `plans/hm-tri-combo.yaml` for a complete, working example of a 21-week training plan.
