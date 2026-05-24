# paicer-claude-plugin

Claude Code skills for [paicer](https://github.com/cvitan/paicer) — create and sync training plans to Garmin Connect.

## Install

```
claude mcp add npm:paicer-claude-plugin
```

## Skills

- `/paicer:create-plan` — Interview-driven plan creation; uploads workouts to Garmin Connect
- `/paicer:review-progress` — Compare last week's Garmin activities against the plan and discuss adjustments
- `/paicer:plan-authoring` — Reference for plan YAML structure, Garmin patterns, and periodization principles

## Requirements

- [Claude Code](https://claude.ai/code)
- [paicer CLI](https://pypi.org/project/paicer/) (`pip install paicer` or `uv tool install paicer`)
- Garmin Connect account (optional — for workout sync)
