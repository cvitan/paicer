# PyPI Packaging & Distribution Design

**Date:** 2026-05-24
**Status:** Approved

## Goal

Make paicer installable via `pip install paicer` so users don't need to clone the repo. Pair with a Claude Code plugin as the single entry point for new users.

## Distribution Architecture

Two published packages:

| Package | Registry | Purpose |
|---|---|---|
| `paicer` | PyPI | CLI tool — all functionality |
| `paicer` | npm | Claude Code plugin — skills only |

User journey:
1. `claude plugin install paicer` — installs the Claude Code plugin
2. Run any skill (e.g. `/paicer:create-plan`)
3. If `paicer` CLI not found, skill detects this and tells user: `pip install paicer`
4. Everything works from that point on

## Package Layout

Restructure `src/` into a proper Python package:

```
src/
  paicer/
    __init__.py
    cli.py          ← Click entry point
    config.py       ← ~/.paicer/config management
    render.py       ← from render_plan.py
    sync.py         ← from generate_workouts.py
    plan_utils.py
    formatters/
    integrations/
```

`pyproject.toml` changes:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
dependencies = [
    "click>=8.0",
    "garminconnect>=0.2.40,<0.3.0",
    "keyring>=24.0",
    "markdown>=3.10.2",
    "pyyaml>=6.0",
]

[project.scripts]
paicer = "paicer.cli:main"
```

## CLI Interface

```
paicer render [--html] [--format a4|letter] [-o file]
paicer sync <scope> [--no-schedule]
paicer version
```

- Output: stdout by default; `-o path` writes to file
- No positional plan argument — plan path comes from config

## Config

File: `~/.paicer/config` (TOML)

```toml
plan = "/Users/tom/.paicer/myplan.yaml"
units = "metric"
garmin_email = "tom@example.com"
```

- Default plan path: `~/.paicer/`
- First `paicer render` with no config: prompts for plan path, writes config
- Garmin password: stored in system keychain via `keyring` (prompted on first `paicer sync`)
- `python-dotenv` dependency can be dropped — config replaces `.env`

## Versioning

- Version lives only in `pyproject.toml`
- To release: bump version in `pyproject.toml`, commit, tag, push

```bash
# bump version in pyproject.toml
git add pyproject.toml && git commit -m "chore: bump to v0.2.0"
git tag v0.2.0
git push && git push --tags
```

GitHub Actions triggers on `v*` tags.

## GitHub Actions Workflow

File: `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # required for Trusted Publishers (OIDC)

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install hatchling build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Uses PyPI **Trusted Publishers** (OIDC) — no API token stored in GitHub secrets. Requires a one-time setup on PyPI: create the project, add a trusted publisher pointing to this repo + workflow file.

## Out of Scope

- Strava integration commands (future)
- Claude Code plugin npm package (follow-up task)
- Homebrew formula
