---
name: plan-authoring
description: Use when creating, editing, or reviewing training plan YAML - covers structure rules, unit conventions, Garmin patterns, workout types, and periodization principles
---

# Plan Authoring

Reference for writing correct training plan YAML. Used by `/paicer:create-plan`, `/paicer:review-progress`, and ad-hoc plan edits.

## Unit System

Read `UNITS` from `.env` (default: `metric`). Use for all text fields (`name`, `description`) and YAML comments on Garmin values.

Garmin steps always use metric (meters, sec/km). Add comments in the user's system: `endConditionValue: 6437  # 4 mi`.

**Imperial conventions** — use clean round numbers, not conversions:
- Runs: 3, 4, 5, 6, 8, 10, 13, 16, 20 miles
- Bikes: 10, 15, 20, 25, 40 miles
- Paces: round to nearest :15 (7:30, 7:45, 8:00/mi)
- Swim: yards for US pools (200, 500, 1000 yds)
- Track: stays in meters (400m tracks are universal)

## YAML Structure Rules

- Single `start_date` — all dates calculated from it
- Day numbers = 1-based positions in `training_days`, not weekday names
- Days must be sequential within a week (1, 2, 3... no gaps except same-day pairs)
- Non-optional workouts must not exceed `training_days` slots
- Week/day numbers sequential within their parent
- `name`: descriptive with distance/workout info (e.g., "Easy 8km", "Tempo 3x8min"). Week prefix added at Garmin sync time.

## Workout Types

| Type | Garmin Sport | Notes |
|------|-------------|-------|
| `run` | running (1) | HR zone for easy, pace targets for tempo/intervals |
| `track` | running (1) | Reusable via YAML anchors |
| `bike` | cycling (2) | Power zone targets (if power meter) |
| `swim` | swimming (4) | Lap-button cue cards with `description` per step |
| `multisport` | multi_sport (10) | `garmin.legs`, each with `sport` + `steps` |
| `race` | — | Race day entry, typically `skip_garmin: true` |

## Flags

- **`optional: true`** — shows as "Optional:" in docs, doesn't count against training_days. If it has a `garmin:` section, uploads to library without scheduling. Doesn't override `skip_garmin`.
- **`skip_garmin: true`** — no Garmin upload at all.

## Garmin Step Patterns

Read `examples/reference-metric.yaml` (or `reference-imperial.yaml`) for working examples of every pattern. Read `docs/garmin-api.md` for complete API reference.

**Common patterns:**
- Easy run: single `interval` step + `heart.rate.zone` zone 2
- Tempo: `warmup` + `repeat` group (work + recovery) + `cooldown`
- Swim: `lap.button` + `description` per step, `rest` steps between sections
- Multisport: `garmin.legs` array, each leg has `sport` + `steps`
- Reusable sessions: YAML anchors in `swim_sessions:` / `track_sessions:` blocks

## Periodization Principles

- **Progressive overload:** +5-10% volume/week, recovery week every 3-4 weeks
- **Polarized intensity:** ~80% easy (RPE 4-5), ~20% hard (RPE 7-9), minimal grey zone
- **Specificity:** Training mirrors race demands as plan progresses
- **Taper:** 2-3 weeks before race, -30-50% volume, maintain intensity
- **Rest sequencing:** Rest day after long/hard sessions. Easy before hard, rest after hard/long.
- **Phase structure:** Base (aerobic) -> Build (race-specific) -> Peak (sharpening) -> Taper

## Pace Conversion

Garmin pace values are sec/km. Convert: `5:25/km = 325 sec/km`.

To min/mi: multiply sec/km by 1.60934. Example: 325 sec/km = 523 sec/mi = 8:43/mi.

## Validation

Always run `make test` after changes. It validates YAML syntax, Python, and plan structure (day ranges, training_days counts).
