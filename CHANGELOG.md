# Changelog

## 2026-03-15

- Add training status to review data (VO2max, load balance, acute-to-chronic ratio)
- Add HR time in zones and aerobic training effect to review data
- Add elevation gain/loss to review data and skill
- Update review skill to interpret all new metrics
- Fix inaccurate distance totals in tempo workout descriptions
- Smooth long run progression (12 → 14 → 15 → 17 → 16 → 18 → 19 → 18 → 20 → 19 → 16 → Race)
- Add strides to W4, W5, W8, W10, W11 (every non-race week now has strides)
- Add introductory comment to hm-tri-combo.yaml example

## 2026-03-14

- Fix advanced example plan (hm-tri-combo): remove duplicate workouts, correct step ordering

## 2026-03-12

- Fix plan formatting across all example plans (descriptions, date displays, en dashes)

## 2026-03-11

- Extract plan-authoring knowledge into shared skill (used by both create-plan and review-progress)
- Rename commands to `paicer/create-plan` and `paicer/review-progress`
- Fix hm-tri phase 1 training day assignments

## 2026-03-10

- Add imperial unit system support (pace in min/mile, paper format switches to letter)
- Add optional workout support (`skip_garmin: true` for strength/rest days)
- Add sport labels (emoji in HTML, text in Markdown) and plan validation
- Add imperial reference example plan
- Update README

## 2026-03-08

- Add coaching commands: `/paicer:create-plan` and `/paicer:review-progress`
- Add `review_data.py` for pulling Garmin activity data by plan week
- Add Garmin API reference docs
- Add CLAUDE.md project instructions
- Move plans to `examples/` directory

## 2026-03-04

- Add multisport (brick) workout support for Garmin
- Add track session support with reusable YAML anchors

## 2026-03-03

- Add cycling and swimming workout types
- Expand hm-tri-combo plan with full Phase 2 (swim/bike integration)

## 2026-02-22

- Initial release: YAML plan parser, Markdown/HTML renderers, Garmin workout sync
- Run-only support with tempo, interval, and easy run structures
- Scope filtering (phase, week, day)
