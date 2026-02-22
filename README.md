# p**ai**cer

A tool for creating structured training plans and sync workouts to devices. Currently supports Garmin Connect.

## Quick Start

```bash
# Install dependencies
uv sync

# Set Garmin credentials and plan
cp .env.example .env


# Generate documents
make markdown               # Generate Markdown
make html                   # Generate HTML (letter, default)
make html FORMAT=a4         # Generate HTML (A4)

# Upload workouts to Garmin
make workouts SCOPE=p1w1    # Upload Phase 1 Week 1
make workouts SCOPE=p1w1d1  # Upload Phase 1 Week 1 Day 1 only
make workouts SCOPE=all     # Upload everything (use with caution)
```

## Example Plans

See `plans/` directory

## Creating Your Own Plan

1. Copy an example: `cp plans/hm-tri-combo.yaml plans/my-plan.yaml`
2. Edit your plan (use Claude Code for help - see [docs/CLAUDE_GUIDE.md](docs/CLAUDE_GUIDE.md))
3. Set as default in `.env`: `PLAN=plans/my-plan.yaml`
4. Generate: `make markdown`
5. Upload: `make workouts SCOPE=p1w1`

## Generated Files

All generated files go to `output/` directory (gitignored).

## Outputs from plan.yaml

### 1. Markdown Document
```bash
make markdown
# Creates output/training_plan.md
```
- GitHub/Obsidian/Notion compatible
- Includes all calculated dates
- All coaching notes preserved

### 2. HTML Document (Printable)
```bash
make html
# Creates output/training_plan.html
```
- **One week per page** for printing
- Table layout with checkbox column

### 3. Garmin Connect Workouts
```bash
# Upload specific week (phase 1, week 1)
make workouts SCOPE=p1w1

# Upload single workout
make workouts SCOPE=p1w1d1

# Upload everything (use with caution)
make workouts SCOPE=all

```

## YAML Structure

```yaml
plan:
  name: "Plan Name"
  start_date: "2026-02-22"
  training_days: [1, 3, 5, 7]  # Mon, Wed, Fri, Sun (1=Mon, 7=Sun)
  overview: |
    All intro text (races, philosophy, RPE)

phases:
  - phase: 1
    name: "Phase Name"
    # training_days: [1, 2, 3, 5, 7]  # Optional: override global
    description: |
      Phase description (includes format)

    weeks:
      - week: 1
        description: |
          Week description (includes volume)

        workouts:
          - day: 1  # 1-7 (Mon-Sun)
            type: "run"
            name: "Workout Name"
            garmin_name: "W1D1: Short Name"
            description: "Full description"
            garmin:
              steps:
                - stepType: "interval"
                  endCondition: "distance"
                  # ... see docs/integrations/garmin.md
```

## Garmin Workout Structure

All workouts use the `garmin.steps` structure with step types:

**Easy run (8km):**
```yaml
garmin:
  steps:
    - stepType: "interval"
      endCondition: "distance"
      endConditionValue: 8000
      targetType: "heart.rate.zone"
      zoneNumber: 2
```

**Tempo intervals (3×8min @ pace):**
```yaml
garmin:
  steps:
    - stepType: "warmup"        # 2km warmup
      # ...
    - stepType: "repeat"         # Main set
      numberOfIterations: 3
      steps:
        - stepType: "interval"   # Work (8min @ pace)
          # ...
        - stepType: "recovery"   # Recovery (2min)
          # ...
    - stepType: "cooldown"       # 2km cooldown
      # ...
```

**Strides (7km + 4×20sec):**
```yaml
garmin:
  steps:
    - stepType: "interval"       # Easy 7km
      # ...
    - stepType: "repeat"         # Strides
      numberOfIterations: 4
      steps:
        - stepType: "interval"   # 20sec stride
          # ...
        - stepType: "recovery"   # Lap button
          endCondition: "lap.button"
          # ...
```

See [docs/integrations/garmin.md](docs/integrations/garmin.md) for all step types and targets.