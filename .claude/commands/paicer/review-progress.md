# Training Plan Weekly Review

Compare last week's Garmin activities against the plan and discuss adjustments.

**Invoke the `plan-authoring` skill** for unit conventions and pace conversion reference.

## Steps

Read `UNITS` from `.env` (default: `metric`). Present all values in the user's preferred system.

1. Read the plan YAML from `PLAN` path in `.env` using Read tool (do NOT write scripts to parse YAML).
2. Pull review data:
   ```
   uv run python src/review_data.py $PLAN          # most recently completed week
   uv run python src/review_data.py $PLAN 3        # specific week number
   ```
3. Match activities by `activityName` against `W{week_num}: {name}` (prefixed format from Garmin upload). Do NOT match by date — users often shift days.
4. Analyze using the `intervals` array — NOT overall activity averages. Each interval has `type` (INTERVAL_WARMUP, INTERVAL_ACTIVE, INTERVAL_RECOVERY, INTERVAL_COOLDOWN), `paceSecPerKm`, `averageHR`, `averagePower`, `distance`, `duration`.
   - **Structured workouts (tempo, intervals):** Compare INTERVAL_ACTIVE entries against targets. Overall average is misleading (includes warmup/cooldown).
   - **Easy runs:** May only have INTERVAL_ACTIVE or no intervals. Use overall average.
   - **Elevation context:** Check `elevationGain`/`elevationLoss` on every activity. Hilly runs raise HR at the same effort — don't flag elevated HR without accounting for elevation. Mention gain when it's notable (>5 m/km).
   - **Running with pace targets:** compare each INTERVAL_ACTIVE pace vs planned, note HR
   - **Running with HR targets:** compare INTERVAL_ACTIVE HR vs target zone
   - **Cycling with power targets:** compare INTERVAL_ACTIVE power vs target zone
   - **Swimming:** completion check (did the session happen?)
   - **Distance:** actual vs planned
   - **HR time in zones** (`hrTimeInZones`): Use to verify easy runs stayed in Zone 1–2. If zone 3+ time exceeds ~10% of duration on an easy run, flag it (accounting for elevation). For tempo/interval workouts, zone distribution confirms effort matched intent.
   - **Aerobic training effect** (`aerobicTrainingEffect`): 1–5 scale. Easy runs should be 2.0–3.0 ("maintaining"). Tempo/intervals 3.0–4.0 ("improving"). Long runs 3.0–4.5. Flag if an easy run scores >3.5 (too hard) or a key session scores <2.5 (too easy). Useful as a weekly load summary — sum or average across sessions to gauge overall training stress.
   - **Training status** (`trainingStatus`): Included at top level of review data. Report:
     - **Acute-to-chronic ratio**: optimal 0.8–1.5. Below 0.8 = detraining. Above 1.5 = overreaching risk. If above 1.3, note it as something to watch.
     - **Load balance feedback**: Garmin's own assessment (e.g., ABOVE_TARGETS, WITHIN_TARGETS). If above targets, discuss whether next week should be lighter.
     - **VO2max trend**: note if it changed from previous review.
     - **Training status phrase**: e.g., PRODUCTIVE, MAINTAINING, OVERREACHING. Flag non-productive states.
5. For unmatched workouts: check for other activities that might be the same workout done under a different name. Ask user to confirm before using.
6. Flag mismatches: HR too high/low at target pace, missed workouts, distance deviations.
7. Present findings conversationally. Discuss adjustments.
8. If pace adjustments agreed, update `targetValueOne`/`targetValueTwo` and descriptions in YAML.
9. Add review entry:
   ```yaml
   reviews:
     - week: N
       date: "YYYY-MM-DD"
       notes: "Summary"
       adjustments:
         - "Description of each change"
   ```
10. Validate: `make test`
