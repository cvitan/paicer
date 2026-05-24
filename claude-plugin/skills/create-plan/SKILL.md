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

1. Do you use metric or imperial? (km/miles)
2. What are you training for? (race distance, goal date, first time?)
3. Current fitness? (recent volume, longest recent run/ride, recent races?)
4. How many days per week, and which days?
5. What sports? (running only, triathlon, cycling?)
6. Equipment? (Garmin watch model, power meter, pool access?)
7. Current easy pace? (Adapt to their sport. Calculate race paces from any race results — don't ask them to do the math.)

If the plan includes swimming, ask about pool tracking before building the plan (see Swim Tracking below).

Do NOT ask for Garmin credentials directly — the sync command handles that interactively.

## Swim Tracking

Ask this only if the plan includes pool swimming:

> "For pool swims, your watch can track distance two ways:
> - **Auto** — the watch counts strokes and measures distance automatically. Works well if you have a consistent stroke.
> - **Drill** — you tap the watch after each segment and enter the distance manually. More reliable if you're newer to swimming or do a lot of drills.
> Which would you prefer?"

Save the preference: `paicer config set swim_tracking auto` (or `drill`).

## Plan Length and Start Date

Calculate weeks until race day, then recommend:

- Standard lengths: 8, 10, 12, 16, 20 weeks (pick longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 for half marathon, 16 for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- More time than needed? Start later, don't pad.

Present: "You have N weeks until race day. I'd recommend an X-week plan starting [date]." Always confirm with the user.

## Building the Plan

1. Invoke `paicer:plan-authoring` — it has bundled reference examples. Read `examples/reference-metric.yaml` or `examples/reference-imperial.yaml` from that skill's base directory.
2. Create plan file at a path the user chooses (suggest `~/Documents/paicer/my-plan.yaml`)
3. Design phase structure (Base -> Build -> Peak -> Taper)
4. Build week-by-week with progressive volume
5. Add Garmin structures with YAML comments in user's unit system
6. Create YAML anchors for reusable sessions (swim, track)
7. Preview: `paicer render --plan <path>` (fails loudly if YAML is invalid)
8. Save config so future commands need no flags:
   ```
   paicer config set plan <absolute_path>
   paicer config set units <metric_or_imperial>
   ```
   Tell the user: "I've saved your plan path and unit preference — you can run `paicer sync w1` without any flags from now on."
9. Explain what they can do with the plan:
   - **Markdown:** `paicer render` — readable text version of the full plan
   - **HTML:** `paicer render --html` — print-ready, one week per page. Good for putting on the fridge or taking to a race. Ask: "For printing, do you want A4 or US Letter paper?" Then save: `paicer config set format a4` (or `letter`).
   - **Garmin sync:** uploads structured workouts to Garmin Connect so they appear on the watch with step-by-step targets. See below.
10. If they have a Garmin watch, explain Garmin sync (see below) and offer: `paicer sync w1`
11. Suggest `/paicer:review-progress` after the first week of training

## Garmin Sync

**Important: run `paicer sync` in a terminal outside Claude Code** — it requires interactive input for credentials and MFA.

On first run, paicer will prompt for:
- **Garmin email and password** — stored securely in your system keychain (Keychain Access on Mac, Credential Manager on Windows). You won't be asked again on subsequent syncs.
- **MFA code** — Garmin sends a one-time code to your email. Enter it when prompted.

After that, syncing is silent. Workouts appear in Garmin Connect under "Workouts" and can be pushed to the watch from there or scheduled directly.

Sync scope examples:
```
paicer sync w1      # week 1
paicer sync w1d2    # week 1, day 2 only
paicer sync p2      # entire phase 2
```

## Modifying an Existing Plan

1. Read plan path from `~/.paicer/config` (key: `plan` in TOML format)
2. Back up: `cp <plan_path> <plan_path>.backup`
3. Make edits, preserving sequential numbering and naming conventions
4. Preview: `paicer render` to confirm the YAML is valid
5. If Garmin workouts changed, remind user to re-sync affected weeks
