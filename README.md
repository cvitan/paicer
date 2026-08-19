# p**ai**cer

AI-powered training plan manager for Claude Code. Provide your race goals, schedule, and fitness level to create a plan, with structured workouts that sync to your Garmin watch. After each training week, review your Garmin activity data against the plan and adjust targets based on how your body is responding — all through conversation.

**Disclaimer:** This tool is not a substitute for professional coaching or medical advice. Always listen to your body and consult a qualified professional for health or injury concerns.

## Get Started

Install the Claude Code plugin:

```
/plugin marketplace add cvitan/paicer
/plugin install paicer@paicer
```

Then run `/paicer:create-plan` to create a training plan through a guided conversation. It handles CLI setup, configuration, and walks you through the process.

After each week of training, run `/paicer:review-progress` to review your plan progress and make any tweaks if needed. The review will also be appended to your plan for future reference.

### Plan output options
- **Markdown**
- **HTML** — set up to print 1 wk/page
- **Garmin** — sync scheduled structured workouts

## Strava Enrichment (optional)

Auto-label your Strava activities with your plan. When Garmin syncs a workout to Strava, a small Cloudflare Worker matches it to your plan by date and sport, renames it, and adds a planned-vs-actual description — turning "Afternoon Run" into "Tempo 2x15 min" with the week's targets and your actual stats.

See [`strava-enricher/`](strava-enricher/README.md) for setup.

## CLI Commands

If you prefer to run paicer directly rather than through the Claude plugin:

```bash
paicer render --plan my-plan.yaml               # Generate Markdown
paicer render --html --plan my-plan.yaml        # Generate HTML
paicer sync w7 --plan my-plan.yaml              # Sync week 7 to Garmin
paicer sync w7d2 --plan my-plan.yaml            # Sync specific workout
paicer sync p2 --plan my-plan.yaml              # Sync entire phase
paicer exercises --search bench                 # Look up Garmin strength exercise names
```

## Supported Sports

Running, cycling, swimming (pool and open water), track sessions, strength training, and multisport/brick workouts (bike + run with transition tracking). Requires a Garmin watch — multisport needs a compatible model (Fenix, Forerunner 570/970, Enduro).

### Strength training

Strength sessions sync as structured Garmin workouts with the exercise, set and rep count, and rest timer on each step, so the watch guides you through the session and logs what you actually lifted. Plans can be strength-only or mix lifting with endurance work.

Exercise names come from Garmin's own catalog (51 categories, 1,846 exercises), vendored so it works offline. Paicer validates every exercise before upload — a wrong name would otherwise upload without complaint and show as a generic exercise on the watch. Look names up with `paicer exercises --search bench`.

Plans that include lifting get coaching guidance on splits, set and rep schemes, equipment substitutions, and — the part general lifting advice misses — how to place strength work so it doesn't compromise key runs or rides.

