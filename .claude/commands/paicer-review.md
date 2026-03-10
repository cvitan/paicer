# Training Plan Weekly Review

Compare last week's Garmin activities against the plan and discuss adjustments.

## Steps

Read `UNITS` from `.env` (default: `metric`). Present all pace and distance values in the user's preferred system.

1. Read the plan YAML from the `PLAN` path in `.env` using your Read tool (do NOT write scripts to parse YAML).
2. Pull review data by running:
   ```
   uv run python src/review_data.py $PLAN          # most recently completed week
   uv run python src/review_data.py $PLAN 3        # specific week number
   ```
   where `$PLAN` is the plan path from `.env`. This outputs JSON with `planned` workouts and Garmin `activities` for the week.
3. Match activities by `activityName` against `W{week_num}: {name}` (the prefixed format used when uploading to Garmin). Do NOT match by date — users often do workouts on different days than scheduled.
4. For each matched workout, use the `intervals` array for analysis — NOT the overall activity averages.
   Each interval has `type` (INTERVAL_WARMUP, INTERVAL_ACTIVE, INTERVAL_RECOVERY, INTERVAL_COOLDOWN), `paceSecPerKm`, `averageHR`, `averagePower`, `distance`, `duration`.
   These match the structured workout steps shown in Garmin Connect's "Intervals" tab.
   - **Structured workouts (tempo, intervals):** Compare INTERVAL_ACTIVE entries against targets. The overall activity average is misleading because it includes warmup/cooldown.
   - **Easy runs:** May only have INTERVAL_ACTIVE or no intervals. Use overall average.
   - **Running with pace targets:** compare each INTERVAL_ACTIVE pace vs planned pace, note HR at that pace
   - **Running with HR targets:** compare INTERVAL_ACTIVE HR vs target zone
   - **Cycling with power targets:** compare INTERVAL_ACTIVE power vs target zone
   - **Swimming:** completion (did the session happen?)
   - **Distance:** actual vs planned
5. For unmatched plan workouts (no activity with that `name`):
   - Check if there are other activities that weren't matched to any plan workout
   - Present these to the user: "I couldn't find W2: Tempo Run, but I found 'Morning Run' on Thursday — is that the same workout?"
   - If user confirms, use that activity for comparison
   - If no candidate, note as missed
6. Flag mismatches:
   - HR too high at target pace — suggest slowing
   - HR too low at target pace — suggest speeding up
   - Missed workouts — note which ones
   - Significantly different distance — note deviation
7. Present findings conversationally and discuss adjustments.
8. If pace adjustments are agreed, update the YAML plan:
   - Modify `targetValueOne`/`targetValueTwo` on affected pace zone steps
   - Update workout descriptions to reflect new paces
9. Add a review entry to the plan YAML:
   ```yaml
   reviews:
     - week: N
       date: "YYYY-MM-DD"
       notes: "Summary of findings"
       adjustments:
         - "Description of each change made"
   ```
10. Validate: `make test`

## Pace Conversion

Laps include `paceSecPerKm` (seconds per km). Convert to min:sec: `5:25/km = 325 sec/km`.
Activity-level `averageSpeed` is m/s. Convert to min/km: `(1000 / speed) / 60`.
When `UNITS=imperial`: convert to min/mi by multiplying sec/km by 1.60934, then format as min:sec. Example: 325 sec/km = 523.0 sec/mi = 8:43/mi.
