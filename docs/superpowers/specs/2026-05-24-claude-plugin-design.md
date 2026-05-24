# Claude Plugin Design

**Goal:** Package paicer's Claude Code skills as an installable npm plugin so users don't need to clone the repo.

**Package name:** `paicer-claude-plugin`  
**Location:** `claude-plugin/` subdirectory of the paicer repo  
**Versioning:** Independent from the PyPI package. Released via tags prefixed `plugin-` (e.g. `plugin-0.1.0`).

---

## Directory Structure

```
claude-plugin/
  package.json                  # name: paicer-claude-plugin
  .claude-plugin/
    plugin.json                 # name, description, version, author, homepage
  skills/
    create-plan/
      SKILL.md
    review-progress/
      SKILL.md
    plan-authoring/
      SKILL.md
      examples/
        reference-metric.yaml   # copied from examples/reference-metric.yaml
        reference-imperial.yaml # copied from examples/reference-imperial.yaml
```

## Skills

### create-plan

Adapted from `.claude/commands/paicer/create-plan.md`. Opens with a paicer install check before doing anything else:

1. Run `which paicer` (or `paicer version`)
2. If not found: check for `uv` with `which uv`
   - If uv available: run `uv tool install paicer`
   - Otherwise: run `pip install paicer` (note: installs into current Python env — user may need to activate it)
3. Confirm paicer is available before proceeding

The rest of the skill is identical to the current `.claude/commands/paicer/create-plan.md`.

### review-progress

Adapted from `.claude/commands/paicer/review-progress.md`. Same install check at the top. Content otherwise identical.

### plan-authoring

Adapted from `.claude/skills/plan-authoring.md`. This is the large reference skill covering YAML structure, pace tables, Garmin step patterns, and periodization principles.

The two bundled reference examples live alongside it at `skills/plan-authoring/examples/`. The skill references them by relative path so Claude can read them when needed.

The skill also mentions near the top:
> For a full real-world example (half marathon + triathlon combo plan), see `examples/hm-tri-combo.yaml` in the [paicer GitHub repo](https://github.com/cvitan/paicer).

## Publishing

A GitHub Actions workflow at `.github/workflows/publish-plugin.yml` (alongside the existing `publish.yml` for PyPI):

- Triggers on `release: types: [published]`
- Validates that the release tag (minus the `plugin-` prefix) matches the `version` field in `claude-plugin/package.json`
- Publishes to npm using `npm publish` from the `claude-plugin/` directory
- Uses an `NPM_TOKEN` secret (stored in GitHub repo secrets)

Tag convention: `plugin-0.1.0` → publishes `paicer-claude-plugin@0.1.0` to npm.

## Installation (user flow)

```bash
claude plugin install paicer-claude-plugin
```

Then use `/paicer:create-plan` or `/paicer:review-progress` in any Claude Code session. The skill handles paicer CLI installation if needed.

## What stays in the repo

`.claude/commands/paicer/` and `.claude/skills/plan-authoring.md` remain in the repo for contributors and existing users. The plugin is a packaged distribution of the same skills — not a replacement.

## Out of scope

- GitHub Pages landing page (follow-up)
- Automated sync between repo skills and plugin skills (manual copy for now)
