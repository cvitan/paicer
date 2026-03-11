# Paicer

Training plan tool: YAML plan → Garmin workouts + Markdown/HTML documents.

## Architecture

```
src/
  render_plan.py        — YAML → Markdown/HTML (entry point)
  generate_workouts.py  — YAML → Garmin workouts with filtering
  plan_utils.py         — Date calculation, YAML loading, plan validation, sport maps
  formatters/           — Base class + MarkdownFormatter + HTMLFormatter
  integrations/         — Base class + GarminIntegration
examples/               — Example training plans
plans/                  — User plans (gitignored, created by /paicer:create-plan)
output/                 — Generated documents (gitignored)
docs/                   — Garmin API reference, other docs
```

## Commands

```bash
make markdown                  # Generate Markdown
make html                      # Generate HTML (A4 for metric, letter for imperial)
make workouts SCOPE=w7         # Sync week 7 to Garmin
make workouts SCOPE=w7d2       # Sync week 7 day 2
make workouts SCOPE=p2         # Sync phase 2
make workouts SCOPE=all        # Sync everything
make test                      # Validate YAML, Python, and plan structure
```

Plan path is set in `.env` as `PLAN=plans/your-plan.yaml`.

Set `UNITS=metric` or `UNITS=imperial` in `.env` to control the unit system used when creating or editing plans. Garmin steps always use metric internally. Text fields (`name`, `description`) and YAML comments use the preferred system.

## Plan Authoring

Invoke the `plan-authoring` skill for YAML structure rules, workout types, Garmin patterns, unit conventions, and periodization principles.

Reference plans: `examples/reference-metric.yaml` and `examples/reference-imperial.yaml` demonstrate every pattern in a minimal 2-week plan.

Garmin API: `docs/garmin-api.md` for step types, end conditions, target types, pace conversions.
