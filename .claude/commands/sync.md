# Sync Workouts to Garmin

Upload and schedule workouts from the plan to Garmin Connect.

## Steps

1. Ask the user what to sync. Common patterns:
   - "sync next week" → determine the upcoming week number from today's date and plan start_date
   - "sync week 7" → specific week
   - "sync week 7 day 2" → specific workout
   - "sync phase 2" → entire phase
2. Map to the SCOPE format: `w7`, `w7d2`, `p2`, or `all`
3. Show what will be synced (list workout names, dates, types)
4. Run: `make workouts SCOPE=<scope>`
5. Report results

## Options

- `--no-schedule` flag uploads to Garmin library without scheduling to calendar
- `SCHEDULE=0` in make command does the same thing

## Troubleshooting

- **Authentication fails:** Check `.env` has GARMIN_EMAIL and GARMIN_PASSWORD
- **MFA required:** The script will prompt for the code — check email
- **400 error on upload:** Usually a malformed workout structure — check garmin steps in YAML
- **Workout already exists:** The script auto-deletes existing workouts with the same name before uploading
