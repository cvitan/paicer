---
name: review-progress
description: Compare last week's Garmin activities against the training plan and discuss adjustments
---

# Training Plan Weekly Review

Compare last week's Garmin activities against the plan and discuss adjustments.

**Read the plan-authoring guide** at `../../guides/plan-authoring.md` relative to this skill's base directory for unit conventions and pace conversion reference.

## Setup Check

Before anything else, verify paicer is installed:

- Run: `paicer version`
- If the command is not found:
  - Run: `which uv`
  - If uv is available: run `uv tool install paicer`
  - Otherwise: run `pip install paicer`
- Confirm `paicer version` runs without error before continuing.

## Steps

Read `units` from `~/.paicer/config` (default: `metric`). Present all values in the user's preferred system.

1. Read `plan` path from `~/.paicer/config` (TOML format), then read the plan YAML using Read tool (do NOT write scripts to parse YAML).
2. Pull review data:
   ```
   paicer review        # most recently completed week
   paicer review w3     # specific week number
   paicer review w3d2   # individual workout (week 3, day 2)
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
   - **Strength:** use the `exerciseSets` array, not `intervals` — see the Strength Sessions section below
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

   **Notes content:** stick to training-relevant facts — pace, HR, power, distance, elevation, completion vs plan, perceived effort, weather if it affected execution, illness/injury that affected sessions. **Skip lifestyle context** like alcohol consumption, social events, work stress, or other personal details that are not training data — even when the user mentions them in chat.

10. Run `paicer render --plan <plan_path>` to confirm the YAML is valid after edits. Output is written next to the plan file (e.g. `<plan_stem>.md`); the path is echoed. Use `-o <path>` to override.

## Strength Sessions

Strength activities carry an `exerciseSets` array instead of `intervals`.
Each entry is one working set: `category`, `exerciseName`, `reps`,
`weight`, `weightUnit`, `duration`. Rest sets are already filtered out.

Read `../../guides/strength-coaching.md` for the programming
principles behind these judgements.

**Analyse:**

- **Progressive overload** — compare load and reps against the same
  exercise in previous weeks. This is the main signal; a strength block
  that isn't progressing isn't working.
- **Prescribed vs actual** — did they hit the planned sets and reps? Read
  the planned session from the plan YAML's `garmin.steps`.
- **Stalls** — same load and reps for two or three consecutive weeks means
  recovery is the limiter, not programming. Check endurance load before
  suggesting more work.
- **Dropoff within a session** — reps falling across sets (8/8/6) means the
  load was too heavy for the prescription. Hold load rather than
  progressing.
- **Interference** — did lifting land the day before a quality run or long
  run? If a key endurance session underperformed, check what preceded it
  before blaming fitness.
- **Completion** — strength is the first thing athletes silently drop.
  Missing sessions are worth raising directly.

**If `exerciseSets` is empty**, the watch recorded the session without
exercise detection — normal for manually-started strength activities.
Fall back to duration, HR and training effect, and note that set detail
wasn't available rather than treating it as a missed session.

## Race Week (special handling)

When the upcoming week contains a race, the standard review flow still applies — but **race-week conversations must lead with the HR ceiling rule, not with fueling/kit/course details.** See the "Race Strategy and Execution Priorities" section of the plan-authoring guide for the priority order.

The single highest-leverage piece of race-day advice is: *"Stay below the HR ceiling until the release km. Then push."* If that gets buried under gel timing, breakfast composition, and kit selection conversations, the user loses the race in execution even when training is fit. Make it the headline of every race-week message.

If the race workout has a `race_strategy:` field, surface its `one_liner` prominently in every race-week conversation.
