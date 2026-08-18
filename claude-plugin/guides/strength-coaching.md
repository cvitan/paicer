# Strength Coaching

Programming reference for strength sessions in paicer plans. Read this
whenever a plan includes `type: strength` workouts.

For YAML mechanics — step shape, `category`/`exerciseName`, the rest-step
rule — see [plan-authoring.md](plan-authoring.md) and
[docs/garmin-api.md](https://github.com/cvitan/paicer/blob/main/docs/garmin-api.md).
This guide covers what to program, not how to encode it.

## Never guess exercise names

Plan YAML needs exact enum strings. Choose the movement from your own
training knowledge, then resolve the string:

```
paicer exercises --search bench      # substring search
paicer exercises --category SQUAT    # everything in one category
paicer exercises                     # 51 categories with counts
```

A wrong name uploads without error and shows as a generic exercise on the
watch. `paicer render` catches it first, but looking it up is cheaper than
fixing it. Names are rarely what you'd guess — the overhead press is
`SHOULDER_PRESS/BARBELL_SHOULDER_PRESS`, not `BARBELL_OVERHEAD_PRESS`, and
exercises are often filed under surprising categories.

## Start with two questions

Programming is meaningless without these, so ask both before writing
anything:

**Goal** — determines sets, reps, rest, and progression:

| Goal | Reps | Sets | Rest | Load (RPE) | Progression |
|------|------|------|------|-----------|-------------|
| Strength | 3–6 | 3–5 | 2–5 min | 8–9 | Add load when top of rep range hit on all sets |
| Hypertrophy | 8–12 | 3–4 | 60–90 s | 7–8 | Add reps to top of range, then add load and reset |
| Endurance support | 6–10 | 2–3 | 60–90 s | 6–7 | Hold load; add reps sparingly. Volume stays low by design |
| Power | 3–5 | 3–5 | 2–3 min | 6–7 (speed, not grind) | Add load only when bar speed holds |

**Equipment** — determines what you can actually prescribe:

| Tier | Available | Squat pattern | Hinge | Push | Pull |
|------|-----------|--------------|-------|------|------|
| Full gym | Barbell, rack, machines, cables | `BARBELL_BACK_SQUAT` | `BARBELL_DEADLIFT` | `BARBELL_BENCH_PRESS` | `BARBELL_ROW`, `PULL_UP` |
| Home weights | Dumbbells/kettlebells, bench | `GOBLET_SQUAT` | `DUMBBELL_DEADLIFT` | `DUMBBELL_BENCH_PRESS` | `DUMBBELL_ROW` |
| Bodyweight | Nothing, or a bar | `AIR_SQUAT` | `SINGLE_LEG_HIP_RAISE` | `PUSH_UP` | `PULL_UP`, `INVERTED_ROW` |

Categories for the bodyweight row: `AIR_SQUAT` is under `SQUAT`,
`SINGLE_LEG_HIP_RAISE` under `HIP_RAISE`, `PUSH_UP` under `PUSH_UP`,
`INVERTED_ROW` under `ROW`.

Verify any name from this table with `paicer exercises --search` before
writing it — the table is a starting point, not a substitute for lookup.
Plausible-sounding names are frequently wrong: there is no
`BODYWEIGHT_SQUAT` (it's `AIR_SQUAT`) and no `SINGLE_LEG_DEADLIFT` under
`DEADLIFT` (that one lives under `SUSPENSION`).

## Splits

Pick by days per week, not by preference:

| Days | Split | Structure |
|------|-------|-----------|
| 1 | Full body | Every session hits squat, hinge, push, pull |
| 2 | Full body, or upper/lower | Full body is the safer default at 2 days |
| 3 | Full body, or push/pull/legs | PPL only if the athlete has real training history |
| 4 | Upper/lower | Two of each per week |
| 5+ | PPL or body-part | Only for dedicated strength blocks, not alongside race training |

Every session should cover a **squat**, a **hinge**, a **push**, and a
**pull** unless the split deliberately isolates. Add core and unilateral
work as accessories.

## Session shape

1. **Warmup** — 5 min, `stepType: warmup`, no exercise fields, time-based
2. **Compound lifts first** — heaviest and most technical while fresh
3. **Accessories** — isolation, unilateral, core
4. **Supersets** — pair non-competing movements (push with pull) in a
   repeat group to save time

Rest steps go *between* exercises inside the repeat group. Rest length is
the load prescription's other half — 90 s for hypertrophy, 3 min for
strength.

## Interacting with endurance training

This is the part a general lifting reference will not tell you, and it
matters more than exercise selection when the plan also contains running,
cycling, or swimming.

**Placement:**

- **Never the day before** a long run or a quality session. Legs are the
  problem, so lower-body work is the constraint; an upper-body day is more
  forgiving.
- **Best placed same-day after an easy run**, several hours later, or on
  its own day.
- **Rest day after** heavy lower-body work, same as after a hard run.
- Upper-body-only sessions can sit almost anywhere.

**Volume across phases:**

| Phase | Strength emphasis |
|-------|------------------|
| Base | Highest — 2–3 sessions/week, real progression. This is when to build |
| Build | Maintain — 1–2 sessions/week, hold load, stop chasing PRs |
| Peak | Reduce — 1 session/week, lighter, keep the movement pattern |
| Taper | 1 short session early in the week, well below working load, or drop it. Never introduce a new exercise during taper |

**When the goal is general strength or hypertrophy and the plan also has
races**, the athlete has to choose which one is primary and say so. Running
hard endurance training and a genuine hypertrophy block at once produces
mediocre results in both. Flag this rather than quietly programming both at
full volume — but if the athlete has decided the lifting is primary, program
it that way and scale the endurance work instead.

**Injury history** overrides everything above. Existing knee, back, or
shoulder issues should narrow exercise selection before any other
consideration.

## Load prescription

Default to **RPE in the step `description`** rather than absolute weight:

```yaml
description: "8 reps @ RPE 7"
```

Absolute loads go stale as the athlete gets stronger, and a plan written in
August is wrong by October. RPE stays correct. This mirrors the cycling
convention of prescribing zone + RPE rather than watts.

`weightValue` is supported for cases where a prescribed load is genuinely
wanted — a percentage-based strength block with known 1RMs. It is written
in the athlete's own unit and converted on upload.

## Progression across weeks

Progress **one variable at a time**, and only when the previous week's
prescription was actually completed:

1. Reps, up to the top of the range
2. Then load, resetting reps to the bottom of the range
3. Then sets, rarely, and only in a dedicated strength block

Recovery weeks cut strength volume alongside endurance volume — typically
by dropping a set from each exercise rather than removing the session.

**Stalling** — the same load and reps for two or three consecutive weeks —
means recovery, not programming, is the limiter. Look at endurance load
before adding more work.
