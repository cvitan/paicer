# Weekly Review

Pull last week's completed activities from Garmin and compare against the plan.

## Steps

1. Read the plan YAML from the `PLAN` path in `.env`
2. Determine the current week number based on today's date and the plan's `start_date`
3. If user specified a week, use that instead. Otherwise review the most recently completed week.
4. Pull completed activities from Garmin for that week's date range using:
   ```python
   from garminconnect import Garmin
   api.get_activities_by_date(start_date, end_date)
   ```
5. Match each completed activity against the planned workouts for that week by date and type
6. For each matched workout, compare:
   - **Running with pace targets:** actual pace vs planned pace, actual HR at that pace
   - **Running with HR targets:** actual HR zone vs target zone
   - **Cycling with power targets:** actual power zone vs target zone
   - **Swimming:** completion (did the session happen?)
   - **Distance:** actual vs planned
7. Flag mismatches:
   - HR too high at target pace → pace target may be too ambitious, suggest slowing
   - HR too low at target pace → pace target may be too easy, suggest speeding up
   - Missed workouts → note which ones
   - Significantly different distance → note deviation
8. Present findings conversationally and discuss adjustments
9. If pace adjustments are agreed, update the YAML plan:
   - Modify `targetValueOne`/`targetValueTwo` on affected pace zone steps
   - Update workout descriptions to reflect new paces
10. Add a review entry to the YAML:
    ```yaml
    reviews:
      - week: N
        date: "YYYY-MM-DD"
        notes: "Summary of findings"
        adjustments:
          - "Description of each change made"
    ```
11. Validate: `make test`

## Garmin Activity Fields

Key fields from `get_activities_by_date` response:
- `activityName`, `activityType` — match to planned workout
- `startTimeLocal` — date for matching
- `distance` — meters
- `duration` — seconds
- `averageSpeed` — m/s (convert to pace: 1000/speed = sec/km)
- `averageHR`, `maxHR` — heart rate
- `averagePower`, `maxPower` — cycling power (if available)

## Authentication

Use the same Garmin credentials from `.env` (GARMIN_EMAIL, GARMIN_PASSWORD) and token store at `~/.garmin_tokens`. See `src/integrations/garmin.py` for the authentication pattern.
