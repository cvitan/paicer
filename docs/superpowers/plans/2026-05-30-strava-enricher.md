# Strava Enricher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the existing Strava-enricher draft (a Cloudflare Worker that renames Strava activities to their planned workout names and adds planned-vs-actual stats) from untested draft to a verified v1.

**Architecture:** The worker is already built (`strava-enricher/src/*.ts`). This plan adds automated tests for the pure logic (date matching, description formatting), adds imperial-unit support, removes a leftover debug endpoint, fixes the setup/deploy scripts to read paicer's real config (`~/.paicer/config`), and ends with a manual end-to-end verification against Strava.

**Tech Stack:** TypeScript, Cloudflare Workers (Wrangler 4), js-yaml, Vitest (new — unit tests), bash + Python 3.12 tomllib (setup/deploy scripts).

---

## File Map

**Create:**
- `strava-enricher/vitest.config.ts` — test config (include glob)
- `strava-enricher/src/plan-matcher.test.ts` — date calc, lookup, collision, sport mapping tests
- `strava-enricher/src/description.test.ts` — metric + imperial formatting tests
- `strava-enricher/deploy.sh` — redeploy after a plan change (reads `~/.paicer/config`)

**Modify:**
- `strava-enricher/package.json` — add Vitest devDep + `test` script
- `strava-enricher/src/description.ts` — add `units` parameter (metric/imperial)
- `strava-enricher/src/types.ts` — add `UNITS` to `Env`
- `strava-enricher/src/index.ts` — remove `/debug/kv`; pass units to `buildDescription`
- `strava-enricher/wrangler.example.toml` — add `[vars] UNITS`
- `strava-enricher/setup.sh` — read plan path + units from `~/.paicer/config`, not `../.env`
- `strava-enricher/README.md` — replace `make deploy-strava-enricher` with `./deploy.sh`
- `strava-enricher/DESIGN.md` — update deploy + config sections

---

## Task 1: Add Vitest and test the date-calc / lookup (highest-risk port)

The `plan-matcher.ts` date logic is a hand-port of `plan_utils.py`. This task pins it down first.

**Files:**
- Modify: `strava-enricher/package.json`
- Create: `strava-enricher/vitest.config.ts`
- Create: `strava-enricher/src/plan-matcher.test.ts`

- [ ] **Step 1: Install Vitest**

```bash
cd strava-enricher && npm install --save-dev vitest
```

Then add a `test` script to `package.json` (in the `"scripts"` block):

```json
    "test": "vitest run",
```

- [ ] **Step 2: Create the Vitest config**

Create `strava-enricher/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/**/*.test.ts"],
  },
});
```

(No resolver config needed — Vite resolves `./foo.js` import specifiers to `foo.ts` source files automatically.)

- [ ] **Step 3: Write the failing test**

Create `strava-enricher/src/plan-matcher.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { buildPlanLookup } from "./plan-matcher.js";

// start_date 2026-01-01 is a Thursday; first Monday on/after is 2026-01-05.
// training_days [1,3,6] = Mon, Wed, Sat.
const PLAN = `
plan:
  name: Test Plan
  start_date: "2026-01-01"
  training_days: [1, 3, 6]
phases:
  - phase: 1
    name: Base
    weeks:
      - week: 1
        workouts:
          - day: 1
            type: run
            name: Easy 5 km
            description: "Easy 5 km @ 6:00/km"
          - day: 2
            type: bike
            name: Spin 30 min
      - week: 2
        workouts:
          - day: 1
            type: swim
            name: Swim 1 km
`;

describe("buildPlanLookup", () => {
  it("computes workout dates matching plan_utils.py", () => {
    const lookup = buildPlanLookup(PLAN);
    // week 1 day 1 (Mon) -> 2026-01-05
    expect(lookup.get("2026-01-05:run")?.name).toBe("Easy 5 km");
    // week 1 day 2 (Wed) -> 2026-01-07
    expect(lookup.get("2026-01-07:bike")?.name).toBe("Spin 30 min");
    // week 2 day 1 (Mon) -> 2026-01-12
    expect(lookup.get("2026-01-12:swim")?.name).toBe("Swim 1 km");
  });

  it("carries phase + week metadata onto the workout", () => {
    const lookup = buildPlanLookup(PLAN);
    const w = lookup.get("2026-01-05:run");
    expect(w?.week).toBe(1);
    expect(w?.phaseNumber).toBe(1);
    expect(w?.phaseName).toBe("Base");
  });
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npm test`
Expected: PASS (the implementation already exists and the dates were hand-verified). If it FAILS, the date port has a bug — debug `plan-matcher.ts` against `src/paicer/plan_utils.py` before continuing.

- [ ] **Step 5: Add the collision test**

Append to `plan-matcher.test.ts`:

```ts
describe("buildPlanLookup collisions", () => {
  it("throws when two workouts map to the same date+sport key", () => {
    const colliding = `
plan:
  name: Collide
  start_date: "2026-01-01"
  training_days: [1, 1]
phases:
  - phase: 1
    name: Base
    weeks:
      - week: 1
        workouts:
          - day: 1
            type: run
            name: Run A
          - day: 2
            type: run
            name: Run B
`;
    expect(() => buildPlanLookup(colliding)).toThrow(/collision/i);
  });
});
```

- [ ] **Step 6: Run to verify it passes**

Run: `cd strava-enricher && npm test`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add strava-enricher/package.json strava-enricher/package-lock.json strava-enricher/vitest.config.ts strava-enricher/src/plan-matcher.test.ts
git commit -m "test(strava-enricher): pin plan-matcher date calc + collision detection"
```

---

## Task 2: Test activity → workout matching

**Files:**
- Modify: `strava-enricher/src/plan-matcher.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `strava-enricher/src/plan-matcher.test.ts`:

```ts
import { matchActivity } from "./plan-matcher.js";

describe("matchActivity", () => {
  const lookup = buildPlanLookup(PLAN);

  it("matches a Run to a run workout on the same local date", () => {
    const w = matchActivity(lookup, "Run", "2026-01-05T18:30:00Z");
    expect(w?.name).toBe("Easy 5 km");
  });

  it("maps TrailRun and VirtualRun to the run family", () => {
    expect(matchActivity(lookup, "TrailRun", "2026-01-05T07:00:00Z")?.name)
      .toBe("Easy 5 km");
    expect(matchActivity(lookup, "VirtualRun", "2026-01-05T07:00:00Z")?.name)
      .toBe("Easy 5 km");
  });

  it("maps Ride to bike", () => {
    expect(matchActivity(lookup, "Ride", "2026-01-07T17:00:00Z")?.name)
      .toBe("Spin 30 min");
  });

  it("returns null for an unknown sport type", () => {
    expect(matchActivity(lookup, "AlpineSki", "2026-01-05T18:30:00Z")).toBeNull();
  });

  it("returns null when no workout falls on that date", () => {
    expect(matchActivity(lookup, "Run", "2026-02-01T18:30:00Z")).toBeNull();
  });

  it("uses the local date, not UTC", () => {
    // 2026-01-06 00:30 local is still the 2026-01-05 plan day in spirit,
    // but matching keys off the local calendar date: this is 2026-01-06 -> no run.
    expect(matchActivity(lookup, "Run", "2026-01-06T00:30:00Z")).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify it passes**

Run: `cd strava-enricher && npm test`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add strava-enricher/src/plan-matcher.test.ts
git commit -m "test(strava-enricher): cover activity-to-workout matching"
```

---

## Task 3: Add imperial-unit support to descriptions (TDD)

`buildDescription` is currently metric-only. Add a `units` parameter.

**Files:**
- Create: `strava-enricher/src/description.test.ts`
- Modify: `strava-enricher/src/description.ts`

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/description.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { buildDescription } from "./description.js";
import type { PlanWorkout, StravaActivity } from "./types.js";

const workout: PlanWorkout = {
  name: "Tempo 2x15 min",
  description: "2x15 min @ 5:25/km + warmup/cooldown (~13 km)\nsecond line",
  type: "run",
  date: "2026-03-14",
  week: 2,
  day: 1,
  phaseNumber: 1,
  phaseName: "HM Build",
  optional: false,
};

const activity: StravaActivity = {
  id: 1,
  name: "Afternoon Run",
  sport_type: "Run",
  start_date: "2026-03-14T18:30:00Z",
  start_date_local: "2026-03-14T18:30:00Z",
  distance: 13200,
  moving_time: 4232,
  elapsed_time: 4300,
  average_speed: 3.12,
  average_heartrate: 156,
  total_elevation_gain: 0,
  description: null,
};

describe("buildDescription", () => {
  it("formats metric output", () => {
    const out = buildDescription(workout, activity, "metric");
    expect(out).toBe(
      "Week 2, Phase 1 (HM Build)\n" +
        "\n" +
        "Planned: 2x15 min @ 5:25/km + warmup/cooldown (~13 km)\n" +
        "Actual: 13.2 km | 5:21/km | 1:10:32 | HR 156",
    );
  });

  it("formats imperial output", () => {
    const out = buildDescription(workout, activity, "imperial");
    expect(out).toBe(
      "Week 2, Phase 1 (HM Build)\n" +
        "\n" +
        "Planned: 2x15 min @ 5:25/km + warmup/cooldown (~13 km)\n" +
        "Actual: 8.2 mi | 8:36/mi | 1:10:32 | HR 156",
    );
  });

  it("defaults to metric and omits HR when absent", () => {
    const noHr = { ...activity, average_heartrate: undefined };
    const out = buildDescription(workout, noHr);
    expect(out).toContain("Actual: 13.2 km | 5:21/km | 1:10:32");
    expect(out).not.toContain("HR");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npm test`
Expected: FAIL — `buildDescription` does not accept a third argument / imperial output wrong.

- [ ] **Step 3: Rewrite `description.ts`**

Replace the entire contents of `strava-enricher/src/description.ts` with:

```ts
import type { PlanWorkout, StravaActivity } from "./types.js";

export type Units = "metric" | "imperial";

const METERS_PER_MILE = 1609.34;

function formatPace(metersPerSecond: number, units: Units): string {
  if (metersPerSecond <= 0) return "--:--";
  const secsPerUnit =
    units === "imperial"
      ? METERS_PER_MILE / metersPerSecond
      : 1000 / metersPerSecond;
  const mins = Math.floor(secsPerUnit / 60);
  const secs = Math.round(secsPerUnit % 60);
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function formatDistance(meters: number, units: Units): string {
  const value =
    units === "imperial" ? meters / METERS_PER_MILE : meters / 1000;
  return value % 1 === 0 ? `${value}` : value.toFixed(1);
}

export function buildDescription(
  workout: PlanWorkout,
  activity: StravaActivity,
  units: Units = "metric",
): string {
  const header =
    `Week ${workout.week}, Phase ${workout.phaseNumber} (${workout.phaseName})`;

  const planned = workout.description.split("\n")[0] ?? "";

  const distUnit = units === "imperial" ? "mi" : "km";
  const paceUnit = units === "imperial" ? "/mi" : "/km";

  const dist = formatDistance(activity.distance, units);
  const pace = formatPace(activity.average_speed, units);
  const duration = formatDuration(activity.moving_time);

  let actual = `${dist} ${distUnit} | ${pace}${paceUnit} | ${duration}`;
  if (activity.average_heartrate) {
    actual += ` | HR ${Math.round(activity.average_heartrate)}`;
  }

  const lines = [header, ""];
  if (planned) {
    lines.push(`Planned: ${planned}`);
  }
  lines.push(`Actual: ${actual}`);

  return lines.join("\n");
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npm test`
Expected: PASS (all three description tests + earlier tests)

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/description.ts strava-enricher/src/description.test.ts
git commit -m "feat(strava-enricher): imperial unit support in descriptions"
```

---

## Task 4: Wire units through the worker

`buildDescription` now takes units; the worker must supply them from a Wrangler var.

**Files:**
- Modify: `strava-enricher/src/types.ts`
- Modify: `strava-enricher/src/index.ts`
- Modify: `strava-enricher/wrangler.example.toml`

- [ ] **Step 1: Add `UNITS` to the `Env` interface**

In `strava-enricher/src/types.ts`, change the `Env` interface to:

```ts
export interface Env {
  STRAVA_TOKENS: KVNamespace;
  STRAVA_CLIENT_ID: string;
  STRAVA_CLIENT_SECRET: string;
  STRAVA_VERIFY_TOKEN: string;
  UNITS?: string;
}
```

- [ ] **Step 2: Pass units into `buildDescription`**

In `strava-enricher/src/index.ts`, update the `import` for description and the `processActivity` call. Change the import line:

```ts
import { buildDescription, type Units } from "./description.js";
```

And replace the `buildDescription` call (currently `const description = buildDescription(workout, activity);`) with:

```ts
  const units: Units = env.UNITS === "imperial" ? "imperial" : "metric";
  const description = buildDescription(workout, activity, units);
```

- [ ] **Step 3: Add the var to the example config**

Append to `strava-enricher/wrangler.example.toml`:

```toml

[vars]
UNITS = "metric"
```

- [ ] **Step 4: Typecheck**

Run: `cd strava-enricher && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/types.ts strava-enricher/src/index.ts strava-enricher/wrangler.example.toml
git commit -m "feat(strava-enricher): thread UNITS var through worker"
```

---

## Task 5: Remove the leftover `/debug/kv` endpoint

**Files:**
- Modify: `strava-enricher/src/index.ts`

- [ ] **Step 1: Delete the debug block**

In `strava-enricher/src/index.ts`, delete this entire block from the `fetch` handler:

```ts
    // KV diagnostic — remove after debugging
    if (request.method === "GET" && url.pathname === "/debug/kv") {
      // Write a test key through the binding, then list everything
      await env.STRAVA_TOKENS.put("debug:test", "hello");
      const keys = await env.STRAVA_TOKENS.list();
      const keyNames = keys.keys.map((k) => k.name);
      const debugVal = await env.STRAVA_TOKENS.get("debug:test");
      await env.STRAVA_TOKENS.delete("debug:test");
      return Response.json({ keys: keyNames, debugWrite: debugVal });
    }
```

- [ ] **Step 2: Verify it's gone and still typechecks**

Run: `cd strava-enricher && grep -r "debug/kv" src/ ; npx tsc --noEmit`
Expected: grep prints nothing; tsc reports no errors.

- [ ] **Step 3: Commit**

```bash
git add strava-enricher/src/index.ts
git commit -m "chore(strava-enricher): remove /debug/kv diagnostic endpoint"
```

---

## Task 6: Fix `setup.sh` and add `deploy.sh` to read paicer config

Both scripts must read the plan path and units from `~/.paicer/config` (TOML), not the obsolete `../.env`.

**Files:**
- Modify: `strava-enricher/setup.sh`
- Create: `strava-enricher/deploy.sh`
- Modify: `strava-enricher/README.md`
- Modify: `strava-enricher/DESIGN.md`

- [ ] **Step 1: Replace the plan-discovery block in `setup.sh`**

In `strava-enricher/setup.sh`, replace this block (the `if [[ -f ../.env ]]` discovery through the `cp "$PLAN_PATH" plan.yaml` line, i.e. the current lines that read `../.env`):

```bash
# Copy plan YAML from repo root
if [[ -f ../.env ]]; then
  # shellcheck source=/dev/null
  PLAN_PATH=$(grep '^PLAN=' ../.env | cut -d= -f2)
fi
PLAN_PATH="../${PLAN_PATH:-}"

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found."
  echo "Set PLAN=plans/your-plan.yaml in the repo root .env file."
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml
```

with:

```bash
# Read plan path + units from ~/.paicer/config (the same config the rest of
# paicer uses).
read_config() {
  python3 - "$1" <<'PY'
import os, sys, tomllib
from pathlib import Path
key = sys.argv[1]
home = os.environ.get("PAICER_HOME")
base = Path(home) if home else Path.home() / ".paicer"
path = base / "config"
if not path.exists():
    sys.exit(0)
data = tomllib.load(open(path, "rb"))
val = data.get(key)
if val is not None:
    print(val)
PY
}

PLAN_PATH=$(read_config plan)
UNITS=$(read_config units)
UNITS="${UNITS:-metric}"

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found in ~/.paicer/config."
  echo "Set it with: paicer config set plan /path/to/your-plan.yaml"
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml
```

- [ ] **Step 2: Pass UNITS on deploy in `setup.sh`**

In `strava-enricher/setup.sh`, change the deploy line (`npx wrangler deploy`) to:

```bash
echo "Running: npx wrangler deploy --var UNITS:${UNITS}"
npx wrangler deploy --var "UNITS:${UNITS}"
```

- [ ] **Step 3: Create `deploy.sh`**

Create `strava-enricher/deploy.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Redeploy the Strava enricher after a plan change. Reads the plan path and
# units from ~/.paicer/config (set via `paicer config set`).
#
# Usage:
#   cd strava-enricher
#   ./deploy.sh

if [[ ! -f wrangler.toml ]]; then
  echo "Error: wrangler.toml not found. Run ./setup.sh first."
  exit 1
fi

read_config() {
  python3 - "$1" <<'PY'
import os, sys, tomllib
from pathlib import Path
key = sys.argv[1]
home = os.environ.get("PAICER_HOME")
base = Path(home) if home else Path.home() / ".paicer"
path = base / "config"
if not path.exists():
    sys.exit(0)
data = tomllib.load(open(path, "rb"))
val = data.get(key)
if val is not None:
    print(val)
PY
}

PLAN_PATH=$(read_config plan)
UNITS=$(read_config units)
UNITS="${UNITS:-metric}"

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found in ~/.paicer/config."
  echo "Set it with: paicer config set plan /path/to/your-plan.yaml"
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml

echo "Running: npx wrangler deploy --var UNITS:${UNITS}"
npx wrangler deploy --var "UNITS:${UNITS}"

echo "Deployed. Plan and units are now live."
```

Then make it executable:

```bash
chmod +x strava-enricher/deploy.sh
```

- [ ] **Step 4: Update `README.md` deploy section**

In `strava-enricher/README.md`, replace the `## Deploy` section body (the `make deploy-strava-enricher` block) with:

```markdown
After changing your training plan:

```bash
cd strava-enricher
./deploy.sh
```

This copies your plan YAML (from `~/.paicer/config`) into the worker and redeploys with your configured units.
```

- [ ] **Step 5: Update `DESIGN.md`**

In `strava-enricher/DESIGN.md`, replace the `## Makefile integration` section with:

```markdown
## Deploy script

`deploy.sh` redeploys after a plan change. It reads the plan path and units
from `~/.paicer/config` (TOML), copies the plan to `plan.yaml`, and runs
`wrangler deploy --var UNITS:<units>`.
```

And in the `## Configuration` / `.dev.vars` area, ensure no reference to a
repo-root `.env` `PLAN=` variable remains (the plan path now comes from
`~/.paicer/config`).

- [ ] **Step 6: Lint the scripts**

Run: `cd strava-enricher && bash -n setup.sh && bash -n deploy.sh`
Expected: no syntax errors.

- [ ] **Step 7: Commit**

```bash
git add strava-enricher/setup.sh strava-enricher/deploy.sh strava-enricher/README.md strava-enricher/DESIGN.md
git commit -m "fix(strava-enricher): read plan + units from ~/.paicer/config; add deploy.sh"
```

---

## Task 7: End-to-end verification (manual — requires Strava + Cloudflare)

This task is not automated; it confirms the never-deployed worker actually works. Requires a Strava API app, a Cloudflare account, and `paicer config set plan ...` already done.

- [ ] **Step 1: Full local check**

Run: `cd strava-enricher && npm test && npx tsc --noEmit`
Expected: all tests PASS, no type errors.

- [ ] **Step 2: Run setup**

Run: `cd strava-enricher && ./setup.sh`
Follow the prompts (OAuth, subdomain). Expected: worker deploys, webhook subscription is created, KV holds `tokens:{athlete_id}`.

- [ ] **Step 3: Confirm the worker is live**

Run: `curl https://paicer-strava-enricher.<your-subdomain>.workers.dev/`
Expected: `strava-worker ok`

- [ ] **Step 4: Trigger a real activity**

Record (or manually re-sync from Garmin) a workout whose date + sport match a planned workout in the active plan. Wait for Garmin → Strava sync.

- [ ] **Step 5: Verify enrichment**

Open the activity in Strava. Expected: the name is the planned workout name, and the description shows the `Week N, Phase N` header, `Planned:` line, and `Actual:` stats in the configured units.

- [ ] **Step 6: Check worker logs if it didn't update**

Run: `cd strava-enricher && npx wrangler tail`
Then trigger another activity. Look for `Updated activity ...` or `No plan match ...`. Debug from there (token refresh failure, sport-type mapping, date mismatch).

- [ ] **Step 7: Record the result**

Update the spec status in `docs/superpowers/specs/2026-05-30-strava-enricher-design.md` from "pending end-to-end verification" to "Verified" (or note what failed), and commit.

```bash
git add docs/superpowers/specs/2026-05-30-strava-enricher-design.md
git commit -m "docs(strava-enricher): mark end-to-end verification result"
```

---

## Self-Review Notes

- **Spec coverage:** Gaps 1–6 in the spec map to Tasks 6, 6, 5, 1+2, 3, 7 respectively. In-scope v1 features (webhook, matching, rename+description, token refresh, single-athlete setup, setup script, metric+imperial) are all either pre-existing in the draft or added here (imperial → Task 3).
- **Type consistency:** `Units` is defined in `description.ts` (Task 3) and imported in `index.ts` (Task 4). `Env.UNITS` (Task 4) is read as `env.UNITS` in `index.ts`. `buildDescription(workout, activity, units)` signature is consistent across Tasks 3 and 4.
- **Out of scope (unchanged):** photo upload, multi-athlete, web UI, time-of-day disambiguation, edit/delete events.
