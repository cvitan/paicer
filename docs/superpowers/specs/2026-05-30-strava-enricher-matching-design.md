# Strava Enricher — Week-Based Session Matching Design

**Date:** 2026-05-30
**Status:** Approved
**Supersedes:** the "Sport + date matching" section of
`2026-05-30-strava-enricher-design.md` (exact-date lookup).

## Goal

Match a synced Strava activity to the *right* planned session even when it
wasn't done on its scheduled day. Today the worker matches strictly on
`YYYY-MM-DD:sport`, so a session moved to another day of the week mismatches or
goes unenriched, and multiple similar activities can collapse onto the same
planned session. Replace this with **per-training-week, per-sport assignment by
size (distance/duration) with deduplication**.

Core idea: *enrich an activity only if a planned session in the same training
week matches its sport and size (within a margin); never label two activities
with the same planned session.*

## Matching model

- An activity belongs to the **training week (Mon–Sun)** its `start_date_local`
  date falls in, computed from the plan's first Monday
  (`week = floor((date − firstMonday) / 7) + 1`). Dates before the first Monday
  or beyond the last planned week → no-op.
- Within that week, each completed **same-sport-family** activity is assigned to
  a **distinct** planned session of that family (one-to-one), choosing the
  smallest size error within a **±35% tolerance**.
- No eligible session within tolerance → the activity is left untouched
  (skip rather than mislabel).

Sport families (existing normalization): `run` ← Run/TrailRun/VirtualRun and
plan types run/track/race; `bike` ← Ride/VirtualRide; `swim` ← Swim.
Multisport is out of scope (unchanged).

## Per-session targets (distance AND duration)

Each planned session gets both a `targetDistance` (meters) and `targetDuration`
(seconds), so steady sessions match on distance and interval/time sessions
match on duration — and mixed sessions match on either.

**From `garmin.steps`** (preferred). Expand the step tree depth-first; a
`repeat` step (`numberOfIterations` + nested `steps`) expands its children N
times. For each leaf step with an `endConditionValue`:

- `endCondition: "distance"` (meters `v`): `distance += v`,
  `duration += v × paceSecPerMeter`.
- `endCondition: "time"` (seconds `v`): `duration += v`,
  `distance += v ÷ paceSecPerMeter`.
- Other end conditions (e.g. `lap.button`, no value) contribute nothing.

`paceSecPerMeter` is a per-sport easy-pace constant used only to estimate the
"missing" unit:

| Family | Pace | s/m |
|---|---|---|
| run | 6:00/km | 0.360 |
| bike | 30 km/h | 0.120 |
| swim | 2:00/100 m | 1.200 |

These are code constants in v1 (a `PACE_SEC_PER_METER` map), promotable to
config vars later. Worked example — "Tempo 3×8 min" (2 km warm-up; 3×[8 min +
2 min recovery]; 2 km cool-down) → `targetDistance ≈ 9 000 m`,
`targetDuration ≈ 3 240 s`. Both realistic; the ±35% margin absorbs the
estimate's slop. (The pace-zone values on interval steps could refine this
later but are not used in v1.)

**Fallbacks when steps yield no usable target** (sum is 0 — e.g. `skip_garmin`
sessions, or swim sessions built entirely from `lap.button` steps):

1. Parse the session **name** for a distance (`N km` / `N mi` / `N m`) or a
   duration (`N min`); fill the other unit via the sport pace. (Swim names like
   "Open Water 1000 m" and rides like "Hills 45 km" carry the distance.)
2. If neither distance nor duration can be derived, the session has **no size
   target** and participates only in the date fallback (below).

## Assignment algorithm

Inputs: the week's planned sessions of the family, and the week's completed
activities of the family (each `{id, distance, movingTime, startDateLocal}`).

1. **Size pass.** For every (activity, session-with-target) pair compute
   `errDist = |actDist − tgtDist| / tgtDist` and
   `errDur = |actDur − tgtDur| / tgtDur` (each only if that target is defined),
   and `err = min(errDist, errDur)`. Keep pairs with `err ≤ 0.35`. Sort by
   `(err, activity date, session date)` ascending and greedily assign
   one-to-one, skipping activities/sessions already used. (Greedy is optimal
   enough for the handful of same-sport sessions in a week and is deterministic.)
2. **Date fallback.** For sessions with **no** size target and still-unassigned
   activities, pair each remaining session to the nearest-date remaining
   activity in the week (greedy by absolute date distance).
3. Activities still unassigned → no match.

The result is a `Map<activityId, PlannedSession>`. The worker enriches only the
activity from the current webhook event, using its assignment (or no-ops).

**Idempotence / order:** each event recomputes the whole week's assignment and
updates only the current activity; it never re-labels others. In rare
out-of-order arrivals an earlier activity can keep its first label. Accepted.

## Worker flow (per `create` event)

After the existing secret-path and `owner_id` checks and `GET /activities/{id}`:

1. Compute the activity's training week; gather that week's same-family planned
   sessions. None → no-op.
2. **Fetch the week's activities**: `GET /athlete/activities?after=&before=`
   over a UTC range padded ±1 day around the week, `per_page=100`; filter to the
   sport family and to `start_date_local` dates within Mon–Sun. Include the
   current activity (dedup by id) in case it isn't listed yet.
3. Run the assignment; look up the current activity.
4. Matched → build description and `PUT` name + description (unchanged format
   for now). Unmatched → no-op.

## Code changes

- `src/strava.ts`: add `listActivities(accessToken, afterEpoch, beforeEpoch)`.
- `src/plan-matcher.ts`: garmin-step target extraction (repeat expansion + pace
  conversion), name-parse fallback, `weekForDate`, and `assignWeek`. Replace the
  `Map<date:sport, workout>` lookup with a per-(week, family) session index plus
  the assignment entry point.
- `src/types.ts`: add the `garmin.steps` shape (recursive: `stepType`,
  `endCondition`, `endConditionValue?`, `numberOfIterations?`, `steps?`).
- `src/index.ts`: orchestrate week lookup → fetch → assign → enrich.
- `src/description.ts`: unchanged in this spec.

## Testing (Vitest, Strava fetch injected — no network)

- **Target extraction:** single distance step; single time step; nested
  `repeat` expansion; mixed warm-up/intervals/cool-down (tempo → ~9 km/~54 min);
  `lap.button`-only and `skip_garmin` → name-parse fallback; name with km, mi,
  and min; session with no derivable target.
- **Assignment:** dedup (two similar runs map to two distinct sessions); a moved
  session matches by size not date; tolerance cutoff leaves a far-off activity
  unmatched; date fallback assigns a target-less session; more activities than
  sessions leaves extras unmatched; determinism on ties.
- **Week math:** date → week number; first-Monday boundary; out-of-range dates.
- **Pace conversion:** distance↔duration estimates per family.

## Scope

**In scope:** week-based size matching with dedup and tolerance, garmin-step
targets with easy-pace estimation, name-parse fallback, date fallback, the
Strava week fetch.

**Out of scope / deferred:**
- **Enrichment content/format changes** — the user has pending changes to what
  the name/description contain; handled in a separate spec after this lands.
- Multisport matching; time-of-day disambiguation; re-labeling previously
  enriched activities; using interval pace-zone values for exact distance;
  exposing pace/tolerance as config vars.
