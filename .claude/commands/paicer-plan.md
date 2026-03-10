# Create or Edit Training Plan

Help the user create a new training plan or modify an existing one.

## First-Time Setup

Before anything else, check if `.env` exists. If not, copy `.env.example` to `.env`.

## Unit System

Read `UNITS` from `.env` (default: `metric`). Use this for all text fields (`name`, `description`) and YAML comments on Garmin numeric values. When `UNITS=imperial`, use miles and min/mile. When `UNITS=metric` (or absent), use km and min/km.

Garmin steps always use metric values (meters, sec/km) regardless of UNITS setting. Add YAML comments in the user's preferred system (e.g., `endConditionValue: 6437  # 4 mi`).

## Creating a New Plan

Interview the user **one question at a time**. Wait for each answer before asking the next. Do not batch questions.

Ask in this order:

1. What are you training for? (race distance, goal date, first time?)
2. How is your current fitness? (recent training volume, longest recent run/ride, any recent races?)
3. How many days per week can you train, and which days?
4. What sports? (running only, triathlon, cycling?)
5. What equipment do you have? (Garmin watch model, power meter, pool access?)
6. What's your current easy pace? (Adapt to their sport — run pace, FTP for cycling, etc. Calculate race paces yourself from any race results they already gave you — don't ask them to do the math.)

If they have a Garmin watch: tell them to edit `.env` and uncomment the Garmin section with their credentials. Do NOT ask for their email or password directly.

## Plan Length and Start Date

After the interview, calculate the weeks available until race day. Then recommend a plan length and start date:

- Standard plan lengths: 8, 10, 12, 16, 20 weeks (pick the longest that fits)
- Minimum: 8 weeks for 5K/10K, 12 weeks for half marathon, 16 weeks for marathon/triathlon
- `start_date` should be a Monday, counting back from race day
- If there's more time than the plan needs, recommend starting later rather than padding

Present this to the user: "You have 13 weeks until race day. I'd recommend a 12-week plan starting on [date]. Want to start then, or would you prefer to start sooner with a 13-week plan?"

Do NOT silently pick a plan length — always confirm with the user.

## Building the Plan

Once you have all the info and the user has confirmed the plan length:

1. Read `examples/reference.yaml` for structural patterns
2. Create a new plan file in `plans/`
3. Design the phase structure (typically: Base → Build → Peak → Taper)
4. Build week-by-week with progressive volume increase
5. Add Garmin workout structures for each session, with YAML comments in the user's preferred unit system (e.g., `endConditionValue: 8047  # 5 mi`)
6. For reusable workouts (swim sessions, track sessions), create YAML anchors
7. Set `PLAN=plans/new-plan.yaml` in `.env`
8. Validate: `make test`
9. Generate preview: `make markdown`
10. Offer to sync first week to Garmin: `make workouts SCOPE=w1`
11. If they set up Garmin, let them know: after your first week of training, run `/paicer-review` to pull your Garmin data, compare against the plan, and adjust pacing.

## Modifying an Existing Plan

1. Read the current plan from the `PLAN` path in `.env`
2. Back up the current plan before making changes: `cp plans/my-plan.yaml plans/my-plan.backup.yaml`
3. Understand what the user wants to change
4. Make the edits, preserving:
   - Sequential week/day numbering
   - `name` format: descriptive name with distance/workout info (e.g., "Easy 8km", "Tempo 3x8min"). Week prefix is added automatically at Garmin sync time.
   - Consistent training_days across the phase
   - Mark truly optional workouts (easy rides, recovery jogs) with `optional: true`. These don't count against training_days slots and upload to Garmin without scheduling.
5. Validate: `make test`
6. If Garmin workouts changed, remind user to re-sync affected weeks

## Plan Design Principles

- **Progressive overload:** Increase volume 5-10% per week, recovery week every 3-4 weeks
- **Specificity:** Training should mirror race demands as the plan progresses
- **Polarized intensity:** ~80% easy (RPE 4-5), ~20% hard (RPE 7-9), minimal "grey zone" (RPE 6)
- **Quality over quantity:** Structured sessions (intervals, tempo) on fresh legs, easy runs truly easy
- **Taper:** 2-3 weeks before race, reduce volume 30-50% while maintaining intensity
- **Rest after hard days:** Always schedule a rest day after long runs and hard sessions. Don't put an easy run the day after a long run — the athlete needs recovery. When suggesting training days, think about the sequence: easy before hard, rest after hard/long.

Read `docs/garmin-api.md` for the complete Garmin API reference (step types, end conditions, target types, pace conversions).
