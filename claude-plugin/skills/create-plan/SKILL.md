---
name: create-plan
description: Create or edit a paicer training plan YAML — interviews user, builds plan, syncs to Garmin
---

# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

**Invoke the `paicer:plan-authoring` skill** for YAML structure, unit conventions, Garmin patterns, and periodization principles.

## Setup Check

Before anything else, verify paicer is installed:

- Run: `paicer version`
- If the command is not found:
  - Run: `which uv`
  - If uv is available: run `uv tool install paicer`
  - Otherwise: run `pip install paicer` (note: installs into the active Python environment — if `paicer` is still not found after this, the user may need to activate their environment or check their PATH)
- Confirm `paicer version` runs without error before continuing.

## Creating a New Plan

Interview the user **one question at a time**. Wait for each answer before asking the next.

1. What are you training for? (race distance, goal date, first time?)
2. Current fitness? (recent volume, longest recent run/ride, recent races?)
3. How many days per week, and which days?
4. What sports? (running only, triathlon, cycling?)
5. Equipment? (Garmin watch model, power meter, pool access?)
6. Current easy pace? (Adapt to their sport. Calculate race paces from any race results — don't ask them to do the math.)

If they have a Garmin watch: tell them to run `paicer sync w1` after the plan is ready — it will prompt for Garmin credentials on first use. Do NOT ask for credentials directly.

## Plan Length and Start Date

Calculate weeks until race day, then recommend:

- Standard lengths: 8, 10, 12, 16, 20 weeks (pick longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 for half marathon, 16 for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- More time than needed? Start later, don't pad.

Present: "You have N weeks until race day. I'd recommend an X-week plan starting [date]." Always confirm with the user.

## Building the Plan

1. Read the appropriate reference plan from the `examples/` directory alongside this skill's `plan-authoring` skill (`examples/reference-metric.yaml` or `examples/reference-imperial.yaml`)
2. Create plan file at a path the user chooses (e.g. `~/paicer-plans/my-plan.yaml`)
3. Design phase structure (Base -> Build -> Peak -> Taper)
4. Build week-by-week with progressive volume
5. Add Garmin structures with YAML comments in user's unit system
6. Create YAML anchors for reusable sessions (swim, track)
7. Preview: `paicer render --plan <path>` (saves plan path to `~/.paicer/config`, fails loudly if YAML is invalid)
8. Offer first week sync: `paicer sync w1`
9. If Garmin set up: suggest `/paicer:review-progress` after first week of training

## Modifying an Existing Plan

1. Read plan path from `~/.paicer/config` (key: `plan`)
2. Back up: `cp my-plan.yaml my-plan.backup.yaml`
3. Make edits, preserving sequential numbering and naming conventions
4. Preview: `paicer render` to confirm the YAML is valid
5. If Garmin workouts changed, remind user to re-sync affected weeks
