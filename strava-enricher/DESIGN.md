# Paicer Strava Enricher — Design

Cloudflare Worker that listens to Strava webhook events. When a new
activity appears (synced from Garmin Connect), the worker matches it to
the training plan, renames the activity, and writes a structured
description with planned-vs-actual stats.

## Constraints

- Strava photo uploads are partner-only; we update name + description
- Strava rate limits: 200 requests / 15 min, 2,000 / day
- Strava access tokens expire every 6 hours; refresh tokens are
  long-lived
- One webhook subscription per Strava app (covers all authenticated
  athletes)
- Cloudflare Workers free tier: 100k requests/day, 10ms CPU per
  invocation

## Execution model

The worker returns 200 immediately on every webhook POST, then uses
`ctx.waitUntil()` to process the activity asynchronously. This ensures
Strava's 5-second response deadline is always met, and the worker is
not killed before the Strava API calls complete.

```
webhook POST --> return 200 immediately
                   |
            ctx.waitUntil(...)
                   |-- GET /activities/{id}
                   |-- match to bundled plan (date + sport)
                   |-- PUT /activities/{id}
```

Network I/O (fetch calls) does not count toward the 10ms CPU limit on
the free tier, so two Strava API calls are well within budget.

## Data flow

```
Garmin Watch --> Garmin Connect --> Strava (auto-sync)
                                      |
                                webhook POST
                                      v
                              Cloudflare Worker
                               |-- return 200
                               |-- ctx.waitUntil:
                                    |-- GET /activities/{id}
                                    |-- match to bundled plan (date + sport)
                                    |-- PUT /activities/{id}
                                         name: "Tempo 2x15 min"
                                         description: stats summary
```

## Strava OAuth

The worker acts on behalf of one athlete at a time. Each user
completes the OAuth flow once; the worker stores refresh + access
tokens as secrets.

### Initial setup (one-time, per user)

1. User creates a Strava API app at strava.com/settings/api
2. User runs a local setup script that opens the OAuth consent page
3. User authorizes; script exchanges the code for tokens
4. Tokens are stored via `wrangler secret put`

### Token refresh (automatic)

Before each API call, the worker checks token expiry. If expired (or
within 5 minutes of expiry), it calls `POST /oauth/token` with the
refresh token. Both the new access token and new refresh token are
persisted.

**Storage:** Tokens need to survive across requests and be updatable at
runtime. Cloudflare secrets are immutable at runtime, so tokens go in
KV. One KV namespace (`STRAVA_TOKENS`) with keys like
`tokens:{athlete_id}`. The KV free tier (100k reads/day, 1k
writes/day) is more than sufficient — we write at most once per token
refresh (every 6 hours) and read once per webhook event.

**Concurrent refresh:** If two webhook events arrive simultaneously,
both may attempt a token refresh. This is acceptable for single-user,
low-volume use — Strava's token endpoint is idempotent and both
refreshes will succeed. The last write wins in KV, and both new tokens
remain valid until their expiry.

## Webhook setup

### Subscription creation (one-time)

```
POST https://www.strava.com/api/v3/push_subscriptions
  client_id, client_secret, callback_url, verify_token
```

The worker must respond to the validation GET within 2 seconds by
echoing `hub.challenge`.

### Event handling

Webhook POST payload:

```json
{
  "aspect_type": "create",
  "event_time": 1516126040,
  "object_id": 12345678,
  "object_type": "activity",
  "owner_id": 99999,
  "subscription_id": 1
}
```

The worker only processes events where `object_type == "activity"` and
`aspect_type == "create"`. All others return 200 immediately.

## Plan matching

The training plan YAML is bundled into the worker at deploy time
(imported as a text module via Wrangler rules). The plan matcher:

1. Parses the YAML once on cold start (cached across requests via
   module scope)
2. Calculates each workout's calendar date from `start_date` +
   `training_days` offsets (reuses the same logic as `plan_utils.py`,
   ported to TypeScript)
3. Builds a lookup: `Map<"YYYY-MM-DD:sport", Workout>`
4. On each webhook: extracts the activity date and sport type from
   the Strava DetailedActivity, looks up the planned workout

### Sport type mapping

Strava `sport_type` values vary by how Garmin syncs each activity.
The matcher normalizes Strava sport types to plan types:

| Strava sport_type        | Plan types matched |
|--------------------------|--------------------|
| Run, TrailRun, VirtualRun | run, track, race  |
| Ride, VirtualRide        | bike               |
| Swim                     | swim               |

Multisport activities from Garmin may arrive as separate activities
(one per leg) or as a single `Workout` type. For v1, multisport
matching is best-effort: individual legs match if they arrive as
separate Run/Ride/Swim activities. A `Workout` sport type is not
matched.

Race workouts are matched via the `run` sport family. The plan's
`type: "race"` is treated as a run for matching purposes.

### Date matching

Activity dates are extracted from `start_date_local` (not
`start_date` which is UTC). This prevents timezone mismatches for
evening workouts — e.g., an 8pm run in UTC+8 has a UTC date of the
previous day.

### Key collision detection

The lookup key is `"YYYY-MM-DD:sport"`. At parse time, if two
workouts produce the same key, the deploy fails with an error
identifying the conflicting workouts. This catches plan authoring
mistakes early.

### No match behavior

If no planned workout matches (e.g., unscheduled activity, wrong
sport), the worker does nothing. User's manual Strava entries are left
untouched.

## Activity update

`PUT https://www.strava.com/api/v3/activities/{id}`

### Name

Set to the workout name from the plan: `"Tempo 2x15 min"`,
`"Long 18 km"`, `"Easy 8 km + Strides"`.

### Description

```
Week 2, Phase 1 (HM Build)

Planned: 2x15 min @ 5:25/km + warmup/cooldown (~13 km)
Actual:  13.2 km | 5:21/km avg | 1:10:32 | HR 156 avg
```

Description fields pulled from the Strava DetailedActivity:
- `distance` (meters, convert to km)
- `moving_time` (seconds, format as H:MM:SS)
- `average_speed` (m/s, convert to min:sec/km)
- `average_heartrate` (bpm, optional — not all activities have HR)

Plan context from the YAML:
- Week number, phase number, phase name
- Workout description (the `description` field from YAML)

## Directory structure

```
strava-enricher/
  src/
    index.ts            -- Worker entry, route handling
    strava.ts           -- Strava API client (OAuth, fetch, update)
    plan-matcher.ts     -- YAML parse, date calc, activity matching
    description.ts      -- Format the description text
    types.ts            -- Shared types
  plan.yaml             -- Copied from plans/ at deploy time
  wrangler.toml         -- Worker config + KV binding
  package.json
  tsconfig.json
  .dev.vars             -- Local dev secrets (gitignored)
```

## Configuration

### wrangler.toml

```toml
name = "paicer-strava-enricher"
main = "src/index.ts"
compatibility_date = "2025-04-01"

[[kv_namespaces]]
binding = "STRAVA_TOKENS"
id = "<created-at-setup>"

[[rules]]
type = "Text"
globs = ["**/*.yaml"]
```

This allows `import planYaml from "../plan.yaml"` to return the YAML
as a string at runtime.

### Secrets (via `wrangler secret put`)

- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_VERIFY_TOKEN`

### .dev.vars (local development)

```
STRAVA_CLIENT_ID=xxxxx
STRAVA_CLIENT_SECRET=xxxxx
STRAVA_VERIFY_TOKEN=paicer-strava-hook
```

## Makefile integration

Add to the project Makefile:

```makefile
deploy-strava-enricher:
    cp $(PLAN) strava-enricher/plan.yaml
    cd strava-enricher && npx wrangler deploy
```

## Error handling

- Strava API errors: log and return 200 (Strava retries on non-200,
  we don't want retries for auth errors or missing activities)
- Token refresh failure: log error, skip activity update
- Plan match miss: no-op, return 200
- YAML parse error at deploy: fail the deploy (caught at import time)

## Scope boundaries

### In scope (v1)

- Webhook listener for new activities
- Plan matching by date + sport type
- Activity rename + description update
- Token refresh flow
- Single-user setup (one athlete per deployment)
- Setup script for initial OAuth + webhook subscription

### Out of scope (future)

- Image generation / photo upload
- Multi-user (multiple athletes per worker)
- Web UI for plan upload
- Matching by time-of-day for same-day/same-sport conflicts
- Activity deletion or edit events
