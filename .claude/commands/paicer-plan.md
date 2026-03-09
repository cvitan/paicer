# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

## First-Time Setup

Before anything else, check if `.env` exists. If not:

1. Copy `.env.example` to `.env`
2. Ask the user: "Do you have a Garmin watch and want workouts synced to it?"
   - If yes: ask for their Garmin email and password, update `.env`
   - If no: leave the Garmin credentials as placeholders (they can still generate Markdown/HTML)
3. Create the `plans/` directory if it doesn't exist: `mkdir -p plans`

## Creating a New Plan

Interview the user to gather:

1. **Race details:** What race? Distance? Date? Is this your first?
2. **Current fitness:** Recent training volume, longest recent run/ride, any recent races?
3. **Schedule:** How many days per week? Which days? Morning or evening?
4. **Sports:** Running only? Triathlon (swim/bike/run)? Cycling?
5. **Equipment:** Power meter? Pool access? Garmin watch model?
6. **Pacing:** Current easy pace? Recent race times? Known HR zones or FTP?

Then:

1. Read `examples/reference.yaml` — it demonstrates every YAML pattern (run, bike, swim, track, multisport, anchors, repeat groups, skip_garmin) in a minimal 2-week plan
2. Create a new plan file in `plans/`
3. Design the phase structure (typically: Base → Build → Peak → Taper)
4. Build week-by-week with progressive volume increase
5. Add Garmin workout structures for each session
6. For reusable workouts (swim sessions, track sessions), create YAML anchors
7. Set `PLAN=plans/new-plan.yaml` in `.env`
8. Validate: `make test`
9. Generate preview: `make markdown`
10. Offer to sync first week to Garmin: `make workouts SCOPE=w1`

## Modifying an Existing Plan

1. Read the current plan from the `PLAN` path in `.env`
2. Back up the current plan before making changes: `cp plans/my-plan.yaml plans/my-plan.backup.yaml`
3. Understand what the user wants to change
4. Make the edits, preserving:
   - Sequential week/day numbering
   - `garmin_name` format: `W{week}: Description` (no day number)
   - Consistent training_days across the phase
5. Validate: `make test`
6. If Garmin workouts changed, remind user to re-sync affected weeks

## Plan Design Principles

- **Progressive overload:** Increase volume 5-10% per week, recovery week every 3-4 weeks
- **Specificity:** Training should mirror race demands as the plan progresses
- **Polarized intensity:** ~80% easy (RPE 4-5), ~20% hard (RPE 7-9), minimal "grey zone" (RPE 6)
- **Quality over quantity:** Structured sessions (intervals, tempo) on fresh legs, easy runs truly easy
- **Taper:** 2-3 weeks before race, reduce volume 30-50% while maintaining intensity

Read `docs/garmin-api.md` for the complete Garmin API reference (step types, end conditions, target types, pace conversions).
