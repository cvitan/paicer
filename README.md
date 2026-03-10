# p**ai**cer

AI-powered training plan generator. Describe your goals and fitness to Claude, and it builds a structured training plan — with workouts synced to your Garmin watch and printable documents for your fridge.

## Get Started

```bash
git clone https://github.com/cvitan/paicer && cd paicer
pip install .           # or: uv sync
cp .env.example .env    # Add your Garmin credentials
```

Then open the project in Claude Code and run `/paicer-plan` to create your training plan through a guided conversation.

## What It Does

From one YAML plan file, paicer generates:
- **Garmin workouts** — structured sessions auto-scheduled to your calendar
- **Markdown document** — digital reading, week-by-week
- **HTML document** — printable, one week per page

## Commands

```bash
make markdown               # Generate Markdown
make html                   # Generate HTML (letter size)
make html FORMAT=a4         # Generate HTML (A4)
make workouts SCOPE=w7      # Sync week 7 to Garmin
make workouts SCOPE=w7d2    # Sync specific workout
make workouts SCOPE=p2      # Sync entire phase
make test                   # Validate plan
```

## Supported Sports

Running, cycling, swimming (pool and open water), track sessions, and multisport/brick workouts (bike + run with transition tracking). Requires a Garmin watch — multisport needs a compatible model (Fenix, Forerunner 570/970, Enduro).

## Roadmap

1. **Additional Formats** — PDF, iCal, JSON, CSV export
2. **New Integrations** — Strava, Zwift
