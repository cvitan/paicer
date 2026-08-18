# Paicer

Training plan tool: YAML plan → Garmin workouts + Markdown/HTML documents.

## Architecture

```
src/paicer/
  cli.py                — Click entry point (render, sync, review, exercises, config)
  render.py             — YAML → Markdown/HTML
  sync.py               — YAML → Garmin workouts with filtering
  review_data.py        — Garmin activity data for weekly review
  plan_utils.py         — Dates, YAML loading, validation, sport maps, step lines
  exercises.py          — Garmin strength exercise catalog (lookup + validation)
  data/exercises.json   — Vendored catalog, generated (see scripts/)
  formatters/           — Base class + MarkdownFormatter + HTMLFormatter
  integrations/         — Base class + GarminIntegration
claude-plugin/          — Claude Code plugin (skills + guides)
scripts/                — Build-time generators
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
paicer exercises --search bench    # Look up Garmin strength exercise names
uv run pytest                      # Run tests
```

Regenerate the strength exercise catalog (only when Garmin adds exercises):

```bash
uv run --with garmin-fit-sdk python scripts/generate_exercises.py
```

Plan path and units are stored in `~/.paicer/config` (TOML). Set once via `paicer render` prompt or pass `--plan` directly.

## Plugin Development

Skills live in `claude-plugin/skills/`. Edit them here and they take effect immediately — no publish needed. The `.claude/commands/` and `.claude/skills/` files delegate to the plugin directory, so there's a single source of truth.

## Plan Authoring

Read `claude-plugin/guides/plan-authoring.md` for YAML structure rules, workout types, Garmin patterns, unit conventions, and periodization principles.

Strength programming — splits, set/rep schemes, equipment substitutions, interaction with endurance training — lives in `claude-plugin/guides/strength-coaching.md`.

Reference plans: `claude-plugin/guides/examples/reference-metric.yaml` and `reference-imperial.yaml` demonstrate every pattern in a minimal 2-week plan.

Garmin API: `docs/garmin-api.md` for step types, end conditions, target types, pace conversions, and the strength step shape.

**Strength exercise names** are exact uppercase enum strings from a vendored catalog (51 categories, 1,846 exercises). Never guess them — use `paicer exercises --search`. Plausible names are frequently wrong (`AIR_SQUAT`, not `BODYWEIGHT_SQUAT`). `paicer render` validates every pair.
