---
name: create-plan
description: Create or edit a paicer training plan YAML — interviews user, builds plan, syncs to Garmin
---

# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

## Setup Check

Say to the user:
> "Let's get your training plan set up! First I'll check that the paicer CLI is installed — it's a small tool that handles plan rendering and Garmin sync."

Then run: `paicer version`
- If the command is not found:
  - Run: `which uv`
  - If uv is available: run `uv tool install paicer`
  - Otherwise: run `pip install paicer` (note: installs into the active Python environment — if `paicer` is still not found after this, the user may need to activate their environment or check their PATH)
- Confirm `paicer version` runs without error before continuing.

## Creating a New Plan

The user starts with no config file. Two preferences are saved during the interview via `paicer config set` (which creates the config file on first use): `units` after Q2, and `swim_tracking` after the swim tracking question. Everything else is context for building the plan — not persisted.

Ask each question **exactly as written** below, one at a time. Wait for the answer before asking the next. Do not rephrase the fixed wording — but do substitute bracketed placeholders (e.g. `[km / mile]`, `[run/ride/swim]`) based on their sport and units.

**Q1:**
> "What sports will this plan cover? Paicer supports running, cycling, swimming, triathlon (a combination of all three), and strength training — which can be added alongside any of them, or trained on its own."

**Q2:**
> "Do you think in kilometres or miles?"

Immediately run: `paicer config set units metric` (or `imperial`).

**Q3:**
> "What are you training for, and when's the race?"

If they don't mention whether it's their first time at this distance, follow up:
> "Is this your first time racing this distance?"

**Q4:**
> "How old are you?"

**Q5:**
> "What does your training look like right now — how many hours or [km/miles] a week are you doing, and what's the longest [run/ride/swim] you've done recently?"

Adapt the bracketed parts to their sport and units.

**Q6:**
> "Any injuries or physical limitations I should know about before we build your plan?"

**Q7:**
> "How many days a week can you train, and which days work best for you?"

**Conditional — ask only if relevant based on Q1, before Q8:**

If swimming is included: ask the Swim Tracking question (see Swim Tracking section) and save the preference before continuing.

If cycling is included:
> "Do you train with a power meter on the bike?"

If strength is included: ask the Strength Training questions (see the
Strength Training section) before continuing.

**Q8 — easy pace or power (adapt wording to sport and units):**
- Running: > "What's your current easy running pace per [km / mile]?"
- Cycling: > "What's your current easy power in watts? If you don't have a power meter, what heart rate zone feels comfortable on the bike?"
- Triathlon: ask the running version, then the cycling version, one at a time.

Calculate race paces from any race results they share — don't ask them to do the math.

**Q9 — always last:**
> "Do you have a Garmin watch, and if so what model?"

Do NOT ask for Garmin credentials directly — the sync command handles that interactively.

## Swim Tracking

Ask this only if the plan includes pool swimming:

> "For pool swims, your watch can track distance two ways:
> - **Auto** — the watch counts strokes and measures distance automatically. Works well if you have a consistent stroke.
> - **Drill** — you tap the watch after each segment and enter the distance manually. More reliable if you're newer to swimming or do a lot of drills.
> Which would you prefer?"

Save the preference: `paicer config set swim_tracking auto` (or `drill`).

## Strength Training

Ask these only if the plan includes strength. Both answers are required —
goal determines sets/reps/rest, equipment determines which exercises can be
prescribed at all. Ask one at a time.

**S1:**
> "What are you after with the lifting — general strength, muscle growth, or
> supporting your endurance training and staying injury-free?"

**S2:**
> "What do you have access to? A full gym with barbells and machines, some
> dumbbells or kettlebells at home, or just bodyweight?"

**S3:**
> "How much lifting have you done before — are you comfortable with barbell
> movements like squats and deadlifts, or starting fresh?"

**S4:**
> "How many days a week do you want to lift?"

These are context for building the plan, not persisted to config.

Before programming anything, read
`../../guides/strength-coaching.md` relative to this skill's base
directory. Resolve every exercise name with `paicer exercises --search
<term>` — plan YAML needs exact enum strings, and plausible-sounding
guesses are usually wrong.

If the athlete wants a serious strength or hypertrophy block *and* has a
race in the plan, say plainly that both at full volume compromises each
other, and ask which is primary. Then program accordingly — scale the
other one, don't quietly do both.

## Plan Length and Start Date

Calculate weeks until race day, then recommend:

- Standard lengths: 8, 10, 12, 16, 20 weeks (pick longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 for half marathon, 16 for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- More time than needed? Start later, don't pad.

Present: "You have N weeks until race day. I'd recommend an X-week plan starting [date]." Always confirm with the user.

## Building the Plan

1. Read the plan-authoring guide at `../../guides/plan-authoring.md` relative to this skill's base directory. Read the relevant reference example from `../../guides/examples/reference-metric.yaml` or `../../guides/examples/reference-imperial.yaml`.
2. Create plan file at a path the user chooses (suggest `~/Documents/paicer/my-plan.yaml`)
3. Design phase structure (Base -> Build -> Peak -> Taper)
4. Build week-by-week with progressive volume
5. Add Garmin structures with YAML comments in user's unit system
6. Create YAML anchors for reusable sessions (swim, track, strength)
7. Say to the user:
   > "Let me do a quick validation to make sure the YAML is valid."

   Then run: `paicer render --plan <path>` (fails loudly if YAML is invalid — fix any errors before continuing)
8. Save the plan path: `paicer config set plan <absolute_path>`
   Tell the user: "I've saved your plan path — you can run `paicer sync w1` without any flags from now on."
9. Explain what they can do with the plan:
   - **Markdown:** `paicer render` — prints to stdout. Use `-o` to save to a file: `paicer render -o my-plan.md`
   - **HTML:** `paicer render --html -o my-plan.html` — print-ready, one week per page. Good for putting on the fridge or taking to a race. Defaults to A4 for metric users, Letter for imperial. (Override with `paicer config set format a4` or `letter`.)
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
