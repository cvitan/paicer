# Strava Enricher Design

**Date:** 2026-05-30
**Status:** Verified end-to-end (2026-05-30) — deployed to Cloudflare and
confirmed enriching a real Strava activity. Two bugs were found and fixed
during live testing: (1) `buildPlanLookup` threw on optional workouts whose
day exceeds the phase's `training_days`; (2) `setup.sh` wrote tokens to
Wrangler's local KV simulation instead of the remote namespace the deployed
worker reads (and `--remote` was also missing on the verification read, which
masked it). `setup.sh` config parsing was also moved off Python `tomllib`
(not present before 3.11) to pure bash, and Step 1 was hardened against an
already-existing KV namespace under `set -euo pipefail`.

## Goal

Auto-enrich Strava activities with paicer training-plan data. When Garmin
syncs a workout to Strava, a Cloudflare Worker renames the activity to the
planned workout name and writes a description with planned-vs-actual stats —
so the Strava feed reads "Tempo 2x15 min" instead of "Afternoon Run".

Full detailed design lives in `strava-enricher/DESIGN.md`. This spec is the
canonical convention-level record; it summarizes the design and tracks the
remaining work to reach a verified v1.

## Architecture

A single Cloudflare Worker (TypeScript), deployed per athlete:

```
Garmin → Strava (auto-sync) → webhook POST → Worker
  → return 200 immediately, then ctx.waitUntil:
    → GET /activities/{id}
    → match to bundled plan (date + sport)
    → PUT /activities/{id}  (name + description)
```

- **Async processing:** return 200 within Strava's 5s deadline, then do the
  Strava API calls in `ctx.waitUntil`. Network I/O does not count toward the
  free-tier 10ms CPU limit.
- **Plan bundling:** the plan YAML is imported as a text module at deploy time
  (Wrangler `[[rules]] type = "Text"`), parsed once on cold start, cached in
  module scope as a `Map<"YYYY-MM-DD:sport", Workout>`.
- **Date math:** ported from `plan_utils.py` (`first_monday_on_or_after` +
  training-day offsets). Activity date comes from `start_date_local` to avoid
  timezone drift.
- **Tokens:** Strava access tokens expire every 6h; refresh tokens are
  long-lived. Tokens live in a KV namespace (`STRAVA_TOKENS`, key
  `tokens:{athlete_id}`), refreshed lazily 5 min before expiry. Secrets are
  immutable at runtime so KV is required for the rotating tokens.

## Module layout

```
strava-enricher/src/
  index.ts          — Worker entry, routing, webhook validation + events
  strava.ts         — OAuth token refresh (KV), GET/PUT activity
  plan-matcher.ts   — YAML parse, date calc, activity → workout matching
  description.ts    — pace/duration/distance formatting
  types.ts          — shared types
```

Supporting: `setup.sh` (one-time OAuth + KV + secrets + deploy + webhook),
`wrangler.example.toml`, `.dev.vars.example`, `README.md`, `DESIGN.md`.

## Sport + date matching

| Strava sport_type           | Plan types matched |
|-----------------------------|--------------------|
| Run, TrailRun, VirtualRun   | run, track, race   |
| Ride, VirtualRide           | bike               |
| Swim                        | swim               |

Lookup key is `"YYYY-MM-DD:sport"`. Two workouts mapping to the same key fail
the deploy (plan-authoring guard). No match = no-op; manual Strava entries are
left untouched.

## Configuration

- Plan path + units come from `~/.paicer/config` (TOML) — the same source the
  rest of paicer uses. The worker is given the plan at deploy time and units as
  a Wrangler var.
- Secrets via `wrangler secret put`: `STRAVA_CLIENT_ID`,
  `STRAVA_CLIENT_SECRET`, `STRAVA_VERIFY_TOKEN`, `STRAVA_ATHLETE_ID`
  (the last set by `setup.sh` after OAuth; used to reject webhook events
  for other athletes since Strava does not sign payloads).

## Scope

**In scope (v1):** webhook listener for new activities, plan matching by
date + sport, rename + description update, token refresh, single-athlete
setup, setup script, metric + imperial descriptions.

**Out of scope:** image/photo upload (partner-only), multi-athlete per worker,
web UI, time-of-day disambiguation for same-day/same-sport conflicts, edit/
delete events.

## Gaps closed (drove the implementation plan)

These were the gaps in the original draft; all are now resolved on this branch.

1. ✅ `setup.sh` read the plan path from a stale `../.env` — now reads
   `~/.paicer/config` (plan + units), parsed in pure bash (no Python `tomllib`).
2. ✅ No deploy entry point — added `deploy.sh`; removed the dead
   `make deploy-strava-enricher` references.
3. ✅ Removed the leftover `/debug/kv` diagnostic endpoint.
4. ✅ Added Vitest coverage (date-calc port vs `plan_utils.py`, collisions,
   sport/date matching, metric + imperial description formatting).
5. ✅ Added imperial unit support to descriptions (via the `UNITS` var).
6. ✅ Deployed and verified end-to-end against Strava (2026-05-30).

Additional fixes surfaced during testing: webhook `owner_id` filtering,
optional-overflow training days, the local-vs-remote KV write in setup, and a
fresh-checkout typecheck setup (`@cloudflare/workers-types` + a tracked
`*.yaml` module declaration).
