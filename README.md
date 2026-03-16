# p**ai**cer

AI-powered training plan manager. Provide your race goals, schedule, and fitness level to create a plan, with structured workouts that can be synced to your Garmin watch. After each training week, run the progress review command to pull your Garmin activity and training status data, compare it against the plan, and adjust targets based on how your body is responding.

**Disclaimer:** This tool is not a substitute for professional coaching or medical advice. Always listen to your body and consult a qualified professional for health or injury concerns.

## Get Started

```bash
git clone https://github.com/cvitan/paicer && cd paicer
```

Open the project in Claude Code and run `/paicer:create-plan` to create a YAML-based training plan through a guided conversation. It handles setup, configuration, and walks you through the process.

After each week of training, run `/paicer:review-progress` to review your plan progress and make any tweaks if needed. The review will also be appended to your plan for future reference.

### Plan output options
- **Markdown**
- **HTML** — set up to print 1 wk/page
- **Garmin** — sync scheduled structured workouts

## Commands

```bash
make markdown               # Generate Markdown
make html                   # Generate HTML (A4 for metric, letter for imperial)
make workouts SCOPE=w7      # Sync week 7 to Garmin
make workouts SCOPE=w7d2    # Sync specific workout
make workouts SCOPE=p2      # Sync entire phase
make test                   # Validate plan
```

## Supported Sports

Running, cycling, swimming (pool and open water), track sessions, and multisport/brick workouts (bike + run with transition tracking). Requires a Garmin watch — multisport needs a compatible model (Fenix, Forerunner 570/970, Enduro).

## Roadmap

1. **Strava activity enrichment**
2. **Zwift Integrations**
3. **Additional Formats** - PDF, iCal, JSON, CSV export
