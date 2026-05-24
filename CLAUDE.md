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
claude-plugin/          — Claude Code plugin (skills for create-plan, review-progress, plan-authoring)
examples/               — Example training plans
docs/                   — Garmin API reference, other docs
```

## Commands

```bash
paicer render --plan <path>        # Generate Markdown
paicer render --html --plan <path> # Generate HTML
paicer sync w7 --plan <path>       # Sync week 7 to Garmin
paicer sync w7d2 --plan <path>     # Sync week 7 day 2
paicer sync p2 --plan <path>       # Sync phase 2
uv run pytest                      # Run tests
```

Plan path and units are stored in `~/.paicer/config` (TOML). Set once via `paicer render` prompt or pass `--plan` directly.

## Plugin Development

Skills live in `claude-plugin/skills/`. Edit them here and they take effect immediately — no publish needed. The `.claude/commands/` and `.claude/skills/` files delegate to the plugin directory, so there's a single source of truth.

## Plan Authoring

Invoke the `plan-authoring` skill for YAML structure rules, workout types, Garmin patterns, unit conventions, and periodization principles.

Reference plans: `claude-plugin/skills/plan-authoring/examples/reference-metric.yaml` and `claude-plugin/skills/plan-authoring/examples/reference-imperial.yaml` demonstrate every pattern in a minimal 2-week plan.

Garmin API: `docs/garmin-api.md` for step types, end conditions, target types, pace conversions.
