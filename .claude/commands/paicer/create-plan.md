# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

**Invoke the `plan-authoring` skill** for YAML structure, unit conventions, Garmin patterns, and periodization principles.

## First-Time Setup

Check if `.env` exists. If not, copy `.env.example` to `.env`.

## Creating a New Plan

Interview the user **one question at a time**. Wait for each answer before asking the next.

1. What are you training for? (race distance, goal date, first time?)
2. Current fitness? (recent volume, longest recent run/ride, recent races?)
3. How many days per week, and which days?
4. What sports? (running only, triathlon, cycling?)
5. Equipment? (Garmin watch model, power meter, pool access?)
6. Current easy pace? (Adapt to their sport. Calculate race paces from any race results — don't ask them to do the math.)

If they have a Garmin watch: tell them to edit `.env` and uncomment the Garmin section. Do NOT ask for credentials directly.

## Plan Length and Start Date

Calculate weeks until race day, then recommend:

- Standard lengths: 8, 10, 12, 16, 20 weeks (pick longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 for half marathon, 16 for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- More time than needed? Start later, don't pad.

Present: "You have N weeks until race day. I'd recommend an X-week plan starting [date]." Always confirm with the user.

## Building the Plan

1. Read the appropriate reference plan: `examples/reference-metric.yaml` or `examples/reference-imperial.yaml`
2. Create plan file in `plans/`
3. Design phase structure (Base -> Build -> Peak -> Taper)
4. Build week-by-week with progressive volume
5. Add Garmin structures with YAML comments in user's unit system
6. Create YAML anchors for reusable sessions (swim, track)
7. Set `PLAN=plans/new-plan.yaml` in `.env`
8. Validate: `make test`
9. Preview: `make markdown`
10. Offer first week sync: `make workouts SCOPE=w1`
11. If Garmin set up: suggest `/paicer:review-progress` after first week of training

## Modifying an Existing Plan

1. Read plan from `PLAN` path in `.env`
2. Back up: `cp plans/my-plan.yaml plans/my-plan.backup.yaml`
3. Make edits, preserving sequential numbering and naming conventions
4. Validate: `make test`
5. If Garmin workouts changed, remind user to re-sync affected weeks
