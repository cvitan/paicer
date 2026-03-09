# Weekly Review

Compare last week's Garmin activities against the plan and discuss adjustments.

## Steps

1. Read the plan YAML from the `PLAN` path in `.env` using your Read tool (do NOT write scripts to parse YAML).
2. Pull review data by running:
   ```
   make review-data              # most recently completed week
   make review-data SCOPE=3      # specific week number
   ```
   This outputs JSON with `planned` workouts and Garmin `activities` for the week.
3. Match activities by `activityName` against the plan's `garmin_name` values. Do NOT match by date — users often do workouts on different days than scheduled.
4. For each matched workout, compare:
   - **Running with pace targets:** actual pace vs planned pace, actual HR at that pace
   - **Running with HR targets:** actual HR zone vs target zone
   - **Cycling with power targets:** actual power zone vs target zone
   - **Swimming:** completion (did the session happen?)
   - **Distance:** actual vs planned
5. For unmatched plan workouts (no activity with that `garmin_name`):
   - Check if there are other activities that weren't matched to any plan workout
   - Present these to the user: "I couldn't find W2D3: Tempo Run, but I found 'Morning Run' on Thursday — is that the same workout?"
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

Activity `averageSpeed` is m/s. Convert to min/km: `(1000 / speed) / 60`.
