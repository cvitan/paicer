# Paicer

Training plan tool: YAML plan → Garmin workouts + Markdown/HTML documents.

## Architecture

```
src/
  render_plan.py        — YAML → Markdown/HTML (entry point)
  generate_workouts.py  — YAML → Garmin workouts with filtering
  plan_utils.py         — Date calculation, YAML loading, swim step extraction
  formatters/           — Base class + MarkdownFormatter + HTMLFormatter
  integrations/         — Base class + GarminIntegration
plans/                  — YAML training plans
output/                 — Generated files (gitignored)
docs/                   — Garmin API reference, other docs
```

## Commands

```bash
make markdown                  # Generate Markdown
make html                      # Generate HTML (letter)
make html FORMAT=a4            # Generate HTML (A4)
make workouts SCOPE=w7         # Sync week 7 to Garmin
make workouts SCOPE=w7d2       # Sync week 7 day 2
make workouts SCOPE=p2         # Sync phase 2
make workouts SCOPE=all        # Sync everything
make test                      # Validate YAML + Python
```

Plan path is set in `.env` as `PLAN=plans/your-plan.yaml`.

## YAML Plan Structure

Single `start_date` — all workout dates calculated from it. Day numbers are positions in the `training_days` list (1-based), not weekday names.

```yaml
plan:
  name: "Plan Name"
  start_date: "YYYY-MM-DD"
  training_days: [1, 3, 5, 7]    # Mon, Wed, Fri, Sun
  overview: |
    Race info, pacing philosophy, RPE definitions

phases:
  - phase: 1
    name: "Base Building"
    # training_days: [1, 2, 3, 5, 7]  # Optional override
    description: |
      Phase goals and weekly structure
    weeks:
      - week: 1
        description: |
          Weekly focus and volume
        workouts:
          - day: 1
            type: "run"           # run | track | bike | swim | multisport
            name: "Easy Run"
            garmin_name: "W1D1: Easy 8km"
            distance: 8000        # Optional, meters
            description: "8 km easy at RPE 4-5."
            garmin:
              steps: [...]

# Added by /review after comparing Garmin data to plan
reviews:
  - week: 1
    date: "YYYY-MM-DD"
    notes: |
      Summary of actual vs planned performance.
    adjustments:
      - "Description of each change made"
```

## Workout Types

| Type | Garmin Sport | Notes |
|------|-------------|-------|
| `run` | running (1) | HR zone targets for easy runs, pace targets for tempo/intervals |
| `track` | running (1) | Track sessions — reusable via YAML anchors |
| `bike` | cycling (2) | Power zone targets (if rider has power meter) |
| `swim` | swimming (4) | Lap-button cue cards with `description` per step |
| `multisport` | multi_sport (10) | Multiple `garmin.legs`, each with own sport + steps |

## Garmin Step Patterns

See `docs/garmin-api.md` for the complete API reference (step types, end conditions, target types, pace conversions, unit reference).

**Common patterns:**
- Easy run: single `interval` step + `heart.rate.zone` zone 2
- Tempo: `warmup` → `repeat` group (work + recovery) → `cooldown`
- Swim: `lap.button` + `description` per step, `rest` steps between sections
- Multisport: `garmin.legs` array, each leg has `sport` + `steps`

**Reusable sessions:** Define YAML anchors in `swim_sessions:` or `track_sessions:` blocks at the top of the plan file. Reference with `garmin: *anchor_name`.

**Skip Garmin:** Set `skip_garmin: true` on workouts that don't need structured Garmin data.

**Swim cue card pattern:** Swim workouts use `lap.button` end conditions with a `description` field on each step — the watch displays what to do, and you press lap to advance. No auto-distance tracking. Add `rest` steps between sections. Type `swim` auto-sets `sportTypeId: 4`, `targetType: null`, `strokeType: none`.

**Multisport/brick workouts:** Use `type: "multisport"` with `garmin.legs` (not `garmin.steps`). Each leg has a `sport` and `steps` list. Uses `sportTypeId: 10`. Step orders are globally unique across all legs (handled automatically). `isSessionTransitionEnabled: true` is set automatically. Requires a multisport-capable watch.

## Editing Plans

When editing a plan:
1. Read the existing plan to understand structure, phases, training days
2. Keep `garmin_name` format as `W{week}D{day}: Description`
3. Week and day numbers must be sequential within their parent
4. Validate after changes: `make test`
5. Generate to verify: `make markdown`

## Creating New Plans

Interview the user:
1. Goal race(s) and dates
2. Current fitness level and recent training
3. Available training days per week
4. Sport(s): running only, triathlon, cycling, etc.
5. Equipment: power meter, swim pool access, etc.

Read `plans/reference.yaml` first — it demonstrates every pattern (run, bike, swim, track, multisport, anchors, repeat groups, skip_garmin) in a minimal 2-week plan. Use as structural reference when building new plans.

Use progressive periodization: Base → Build → Peak → Taper. Include recovery weeks.

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

### Quality Checks

- Verify `start_date` is set
- Check week/day numbers are sequential
- Ensure `garmin_name` follows W{week}D{day} format
- Validate pace values are reasonable (e.g., 4:00-6:30/km)
- Check descriptions include RPE and coaching notes
- Test YAML with `make test`
