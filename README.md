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

See [`strava-enricher/`](strava-enricher/README.md) for setup (scaffold it with `npx degit cvitan/paicer/strava-enricher` — no repo clone needed).

## CLI Commands

If you prefer to run paicer directly rather than through the Claude plugin:

```bash
paicer render --plan my-plan.yaml               # Generate Markdown
paicer render --html --plan my-plan.yaml        # Generate HTML
paicer sync w7 --plan my-plan.yaml              # Sync week 7 to Garmin
paicer sync w7d2 --plan my-plan.yaml            # Sync specific workout
paicer sync p2 --plan my-plan.yaml              # Sync entire phase
```

## Supported Sports

Running, cycling, swimming (pool and open water), track sessions, and multisport/brick workouts (bike + run with transition tracking). Requires a Garmin watch — multisport needs a compatible model (Fenix, Forerunner 570/970, Enduro).

