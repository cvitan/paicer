# Week-Based Session Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the strava-enricher's exact-date matching with per-training-week, per-sport assignment by distance/duration (deduplicated, within ±35%), so sessions done on a shifted day still match and no two activities get the same planned session.

**Architecture:** `plan-matcher.ts` gains: garmin-step target extraction (distance + duration, with an easy-pace estimate for the missing unit), a per-(week, family) session index, and a deterministic greedy one-to-one assignment. `strava.ts` gains `listActivities`. `index.ts` orchestrates: find the activity's plan week → fetch that week's activities → assign → enrich only the current activity. Spec: `docs/superpowers/specs/2026-05-30-strava-enricher-matching-design.md`.

**Tech Stack:** TypeScript, Cloudflare Workers, js-yaml, Vitest.

---

## File Map

**Modify:**
- `strava-enricher/src/types.ts` — add `GarminStep`; add `garmin?` to the workout type.
- `strava-enricher/src/plan-matcher.ts` — step expansion, target extraction, week math, plan index, assignment, `stravaFamily`. (Old `buildPlanLookup`/`matchActivity` stay until Task 7, then are removed.)
- `strava-enricher/src/strava.ts` — `listActivities`.
- `strava-enricher/src/index.ts` — orchestration.
- `strava-enricher/src/description.ts` — widen the param type to `PlanSession` (output unchanged).
- `strava-enricher/src/plan-matcher.test.ts` — remove old `buildPlanLookup`/`matchActivity` tests in Task 7.

**Create (tests):**
- `strava-enricher/src/steps.test.ts`, `targets.test.ts`, `week.test.ts`, `plan-index.test.ts`, `assign.test.ts`, `strava.test.ts`.

Constants (define once in `plan-matcher.ts`, Task 2):
```ts
const PACE_SEC_PER_METER: Record<string, number> = {
  run: 0.36,   // 6:00/km
  bike: 0.12,  // 30 km/h
  swim: 1.2,   // 2:00/100 m
};
const TOLERANCE = 0.35;
```

---

## Task 1: Garmin step types + step expansion

**Files:**
- Modify: `strava-enricher/src/types.ts`
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/steps.test.ts`

- [ ] **Step 1: Add the `GarminStep` type and attach it to the workout type**

In `strava-enricher/src/types.ts`, add this interface (anywhere among the plan types):

```ts
export interface GarminStep {
  stepType: string;
  endCondition?: string;
  endConditionValue?: number;
  numberOfIterations?: number;
  steps?: GarminStep[];
}
```

Then add a `garmin` field to the `PlanWeekWorkout` interface (it currently has `day`, `type`, `name`, `description?`, `optional?`):

```ts
  garmin?: { steps?: GarminStep[] };
```

- [ ] **Step 2: Write the failing test**

Create `strava-enricher/src/steps.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { expandSteps } from "./plan-matcher.js";
import type { GarminStep } from "./types.js";

describe("expandSteps", () => {
  it("returns flat steps unchanged", () => {
    const steps: GarminStep[] = [
      { stepType: "warmup", endCondition: "distance", endConditionValue: 2000 },
      { stepType: "cooldown", endCondition: "distance", endConditionValue: 2000 },
    ];
    expect(expandSteps(steps)).toHaveLength(2);
  });

  it("expands a repeat block by its iteration count", () => {
    const steps: GarminStep[] = [
      { stepType: "warmup", endCondition: "distance", endConditionValue: 2000 },
      {
        stepType: "repeat",
        numberOfIterations: 3,
        steps: [
          { stepType: "interval", endCondition: "time", endConditionValue: 480 },
          { stepType: "recovery", endCondition: "time", endConditionValue: 120 },
        ],
      },
      { stepType: "cooldown", endCondition: "distance", endConditionValue: 2000 },
    ];
    // 2 (warmup+cooldown) + 3*2 (repeat children) = 8
    expect(expandSteps(steps)).toHaveLength(8);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/steps.test.ts`
Expected: FAIL — `expandSteps` is not exported.

- [ ] **Step 4: Implement `expandSteps`**

In `strava-enricher/src/plan-matcher.ts`, add the import for `GarminStep` to the existing type import line (it currently imports `PlanWorkout`, `PlanYaml`), then add:

```ts
export function expandSteps(steps: GarminStep[]): GarminStep[] {
  const out: GarminStep[] = [];
  for (const step of steps) {
    if (step.stepType === "repeat" && step.steps) {
      const iterations = step.numberOfIterations ?? 1;
      for (let i = 0; i < iterations; i++) {
        out.push(...expandSteps(step.steps));
      }
    } else {
      out.push(step);
    }
  }
  return out;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/steps.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add strava-enricher/src/types.ts strava-enricher/src/plan-matcher.ts strava-enricher/src/steps.test.ts
git commit -m "feat(strava-enricher): garmin step types + repeat expansion"
```

---

## Task 2: Target extraction from steps (distance + duration with pace estimate)

**Files:**
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/targets.test.ts`

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/targets.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { stepTargets } from "./plan-matcher.js";
import type { GarminStep } from "./types.js";

describe("stepTargets", () => {
  it("a single distance step gives exact distance and pace-estimated duration (run)", () => {
    const steps: GarminStep[] = [
      { stepType: "interval", endCondition: "distance", endConditionValue: 8000 },
    ];
    // run pace 0.36 s/m -> 8000 m, 2880 s
    expect(stepTargets(steps, "run")).toEqual({ distance: 8000, duration: 2880 });
  });

  it("a single time step gives exact duration and pace-estimated distance (run)", () => {
    const steps: GarminStep[] = [
      { stepType: "interval", endCondition: "time", endConditionValue: 1800 },
    ];
    // 1800 s -> 1800/0.36 = 5000 m
    expect(stepTargets(steps, "run")).toEqual({ distance: 5000, duration: 1800 });
  });

  it("sums a mixed tempo (2km wu + 3x[8min+2min] + 2km cd) to ~9km / ~54min", () => {
    const steps: GarminStep[] = [
      { stepType: "warmup", endCondition: "distance", endConditionValue: 2000 },
      {
        stepType: "repeat",
        numberOfIterations: 3,
        steps: [
          { stepType: "interval", endCondition: "time", endConditionValue: 480 },
          { stepType: "recovery", endCondition: "time", endConditionValue: 120 },
        ],
      },
      { stepType: "cooldown", endCondition: "distance", endConditionValue: 2000 },
    ];
    expect(stepTargets(steps, "run")).toEqual({ distance: 9000, duration: 3240 });
  });

  it("returns nulls when there are no distance/time steps", () => {
    const steps: GarminStep[] = [
      { stepType: "interval", endCondition: "lap.button" },
    ];
    expect(stepTargets(steps, "swim")).toEqual({ distance: null, duration: null });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/targets.test.ts`
Expected: FAIL — `stepTargets` not exported.

- [ ] **Step 3: Implement constants + `stepTargets`**

In `strava-enricher/src/plan-matcher.ts`, add near the top (after the existing `STRAVA_SPORT_TO_PLAN` map):

```ts
const PACE_SEC_PER_METER: Record<string, number> = {
  run: 0.36, // 6:00/km
  bike: 0.12, // 30 km/h
  swim: 1.2, // 2:00/100 m
};
const TOLERANCE = 0.35;

export interface SessionTarget {
  distance: number | null;
  duration: number | null;
}

export function stepTargets(steps: GarminStep[], family: string): SessionTarget {
  const pace = PACE_SEC_PER_METER[family];
  let distance = 0;
  let duration = 0;
  for (const step of expandSteps(steps)) {
    const v = step.endConditionValue;
    if (v === undefined) continue;
    if (step.endCondition === "distance") {
      distance += v;
      if (pace !== undefined) duration += v * pace;
    } else if (step.endCondition === "time") {
      duration += v;
      if (pace !== undefined) distance += v / pace;
    }
  }
  return {
    distance: distance > 0 ? Math.round(distance) : null,
    duration: duration > 0 ? Math.round(duration) : null,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/targets.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/plan-matcher.ts strava-enricher/src/targets.test.ts
git commit -m "feat(strava-enricher): distance+duration targets from garmin steps"
```

---

## Task 3: Name-parse fallback + combined target resolution

**Files:**
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/targets.test.ts` (append)

- [ ] **Step 1: Write the failing test**

Append to `strava-enricher/src/targets.test.ts`:

```ts
import { parseNameTarget, resolveTargets } from "./plan-matcher.js";

describe("parseNameTarget", () => {
  it("parses km and pace-estimates duration", () => {
    expect(parseNameTarget("Long 12 km", "run")).toEqual({ distance: 12000, duration: 4320 });
  });
  it("parses miles", () => {
    const t = parseNameTarget("Easy 5 mi", "run");
    expect(t.distance).toBe(8047); // 5 * 1609.34 rounded
  });
  it("parses minutes and pace-estimates distance", () => {
    expect(parseNameTarget("Easy Ride 60 min", "bike")).toEqual({ distance: 30000, duration: 3600 });
  });
  it("returns nulls when nothing parseable", () => {
    expect(parseNameTarget("Track Session #1", "run")).toEqual({ distance: null, duration: null });
  });
});

describe("resolveTargets", () => {
  it("prefers garmin steps when present", () => {
    const workout = {
      name: "Easy 8 km",
      garmin: { steps: [{ stepType: "interval", endCondition: "distance", endConditionValue: 8000 }] },
    };
    expect(resolveTargets(workout, "run").distance).toBe(8000);
  });
  it("falls back to the name when steps yield nothing", () => {
    const workout = { name: "Open Water 1000 m" };
    expect(resolveTargets(workout, "swim").distance).toBe(1000);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/targets.test.ts`
Expected: FAIL — `parseNameTarget`/`resolveTargets` not exported.

- [ ] **Step 3: Implement `parseNameTarget` and `resolveTargets`**

In `strava-enricher/src/plan-matcher.ts`, add:

```ts
export function parseNameTarget(name: string, family: string): SessionTarget {
  const pace = PACE_SEC_PER_METER[family];
  let distance: number | null = null;
  let duration: number | null = null;

  const distMatch = name.match(/(\d+(?:\.\d+)?)\s*(km|mi|m)\b/i);
  if (distMatch) {
    const value = parseFloat(distMatch[1]!);
    const unit = distMatch[2]!.toLowerCase();
    const meters = unit === "km" ? value * 1000 : unit === "mi" ? value * 1609.34 : value;
    distance = Math.round(meters);
  }

  const durMatch = name.match(/(\d+)\s*min\b/i);
  if (durMatch) {
    duration = parseInt(durMatch[1]!, 10) * 60;
  }

  if (pace !== undefined) {
    if (distance !== null && duration === null) duration = Math.round(distance * pace);
    if (duration !== null && distance === null) distance = Math.round(duration / pace);
  }
  return { distance, duration };
}

export function resolveTargets(
  workout: { name: string; garmin?: { steps?: GarminStep[] } },
  family: string,
): SessionTarget {
  const steps = workout.garmin?.steps;
  if (steps && steps.length > 0) {
    const fromSteps = stepTargets(steps, family);
    if (fromSteps.distance !== null || fromSteps.duration !== null) return fromSteps;
  }
  return parseNameTarget(workout.name, family);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/targets.test.ts`
Expected: PASS (all target tests).

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/plan-matcher.ts strava-enricher/src/targets.test.ts
git commit -m "feat(strava-enricher): name-parse fallback + resolveTargets"
```

---

## Task 4: Week math — `weekForDate` and `weekBounds`

**Files:**
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/week.test.ts`

Note: `firstMondayOnOrAfter(dateStr)` already exists in `plan-matcher.ts` and returns a `Date`. Reuse it.

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/week.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { weekForDate, weekBounds } from "./plan-matcher.js";

// start_date 2026-01-01 (Thu) -> first Monday 2026-01-05.
describe("weekForDate", () => {
  it("maps the first Monday to week 1", () => {
    expect(weekForDate("2026-01-01", "2026-01-05")).toBe(1);
  });
  it("maps a day inside week 1 to week 1", () => {
    expect(weekForDate("2026-01-01", "2026-01-10")).toBe(1); // Sat of week 1
  });
  it("maps the next Monday to week 2", () => {
    expect(weekForDate("2026-01-01", "2026-01-12")).toBe(2);
  });
  it("returns null before the first Monday", () => {
    expect(weekForDate("2026-01-01", "2026-01-02")).toBeNull();
  });
});

describe("weekBounds", () => {
  it("returns the Monday and Sunday local dates for a week", () => {
    const b = weekBounds("2026-01-01", 2);
    expect(b.monday).toBe("2026-01-12");
    expect(b.sunday).toBe("2026-01-18");
    expect(b.before).toBeGreaterThan(b.after);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/week.test.ts`
Expected: FAIL — functions not exported.

- [ ] **Step 3: Implement `weekForDate` and `weekBounds`**

In `strava-enricher/src/plan-matcher.ts`, add:

```ts
export function weekForDate(startDate: string, dateStr: string): number | null {
  const firstMonday = firstMondayOnOrAfter(startDate);
  const d = new Date(`${dateStr}T00:00:00`);
  const diffDays = Math.round((d.getTime() - firstMonday.getTime()) / 86400000);
  if (diffDays < 0) return null;
  return Math.floor(diffDays / 7) + 1;
}

function isoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function weekBounds(
  startDate: string,
  week: number,
): { after: number; before: number; monday: string; sunday: string } {
  const firstMonday = firstMondayOnOrAfter(startDate);
  const monday = new Date(firstMonday);
  monday.setDate(monday.getDate() + (week - 1) * 7);
  const sunday = new Date(monday);
  sunday.setDate(sunday.getDate() + 6);
  // Padded ±1 day UTC epoch range for the Strava fetch; exact filtering is
  // done by local date afterwards.
  const after = Math.floor(monday.getTime() / 1000) - 86400;
  const before = Math.floor(sunday.getTime() / 1000) + 2 * 86400;
  return { after, before, monday: isoDate(monday), sunday: isoDate(sunday) };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/week.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/plan-matcher.ts strava-enricher/src/week.test.ts
git commit -m "feat(strava-enricher): week-for-date and week-bounds helpers"
```

---

## Task 5: Plan index by (week, family) + `stravaFamily`

**Files:**
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/plan-index.test.ts`

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/plan-index.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { buildPlanIndex, sessionsForWeek, stravaFamily } from "./plan-matcher.js";

const PLAN = `
plan:
  name: Test
  start_date: "2026-01-01"
  training_days: [1, 2, 3, 4]
phases:
  - phase: 1
    name: Base
    weeks:
      - week: 1
        workouts:
          - day: 1
            type: run
            name: Easy 8 km
            garmin:
              steps:
                - stepType: interval
                  endCondition: distance
                  endConditionValue: 8000
          - day: 2
            type: bike
            name: Spin 30 min
          - day: 5
            type: run
            name: Optional Easy Ride
            optional: true
`;

describe("buildPlanIndex", () => {
  it("indexes sessions with family + resolved targets", () => {
    const index = buildPlanIndex(PLAN);
    const runs = sessionsForWeek(index, 1, "run");
    expect(runs).toHaveLength(1);
    expect(runs[0]!.name).toBe("Easy 8 km");
    expect(runs[0]!.targetDistance).toBe(8000);
  });

  it("skips optional workouts beyond the training_days count", () => {
    const index = buildPlanIndex(PLAN);
    // day 5 optional with only 4 training days -> not indexed
    expect(index.sessions.some((s) => s.name === "Optional Easy Ride")).toBe(false);
  });

  it("groups by family", () => {
    const index = buildPlanIndex(PLAN);
    expect(sessionsForWeek(index, 1, "bike")).toHaveLength(1);
    expect(sessionsForWeek(index, 1, "swim")).toHaveLength(0);
  });
});

describe("stravaFamily", () => {
  it("maps Strava sport types to families", () => {
    expect(stravaFamily("Run")).toBe("run");
    expect(stravaFamily("TrailRun")).toBe("run");
    expect(stravaFamily("Ride")).toBe("bike");
    expect(stravaFamily("Swim")).toBe("swim");
    expect(stravaFamily("AlpineSki")).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/plan-index.test.ts`
Expected: FAIL — functions not exported.

- [ ] **Step 3: Implement the index + helpers**

In `strava-enricher/src/plan-matcher.ts`, add. (`calculateWorkoutDate` and `normalizePlanType` already exist and are reused.)

```ts
export interface PlanSession {
  name: string;
  description: string;
  type: string;
  date: string;
  week: number;
  day: number;
  phaseNumber: number;
  phaseName: string;
  family: string;
  targetDistance: number | null;
  targetDuration: number | null;
}

export interface PlanIndex {
  startDate: string;
  sessions: PlanSession[];
}

export function buildPlanIndex(yamlText: string): PlanIndex {
  const plan = yaml.load(yamlText) as PlanYaml;
  const globalTrainingDays = plan.plan.training_days ?? [1, 2, 3, 4, 5, 6, 7];
  const startDate = plan.plan.start_date;
  const sessions: PlanSession[] = [];

  for (const phase of plan.phases) {
    const phaseTrainingDays = phase.training_days ?? globalTrainingDays;
    for (const week of phase.weeks) {
      for (const workout of week.workouts) {
        if ((workout.optional ?? false) && workout.day > phaseTrainingDays.length) {
          continue;
        }
        const date = calculateWorkoutDate(
          startDate,
          week.week,
          workout.day,
          phaseTrainingDays,
        );
        const family = normalizePlanType(workout.type);
        const targets = resolveTargets(
          { name: workout.name, garmin: workout.garmin },
          family,
        );
        sessions.push({
          name: workout.name,
          description: workout.description ?? "",
          type: workout.type,
          date,
          week: week.week,
          day: workout.day,
          phaseNumber: phase.phase,
          phaseName: phase.name,
          family,
          targetDistance: targets.distance,
          targetDuration: targets.duration,
        });
      }
    }
  }
  return { startDate, sessions };
}

export function sessionsForWeek(
  index: PlanIndex,
  week: number,
  family: string,
): PlanSession[] {
  return index.sessions.filter((s) => s.week === week && s.family === family);
}

const STRAVA_SPORT_TO_FAMILY: Record<string, string> = {
  Run: "run",
  TrailRun: "run",
  VirtualRun: "run",
  Ride: "bike",
  VirtualRide: "bike",
  Swim: "swim",
};

export function stravaFamily(stravaSportType: string): string | null {
  return STRAVA_SPORT_TO_FAMILY[stravaSportType] ?? null;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/plan-index.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/plan-matcher.ts strava-enricher/src/plan-index.test.ts
git commit -m "feat(strava-enricher): per-week/family plan index + stravaFamily"
```

---

## Task 6: Week assignment (dedup + tolerance + date fallback)

**Files:**
- Modify: `strava-enricher/src/plan-matcher.ts`
- Test: `strava-enricher/src/assign.test.ts`

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/assign.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { assignWeek } from "./plan-matcher.js";
import type { ActivityLite, PlanSession } from "./plan-matcher.js";

function session(name: string, d: number | null, dur: number | null, date: string): PlanSession {
  return {
    name, description: "", type: "run", date, week: 1, day: 1,
    phaseNumber: 1, phaseName: "Base", family: "run",
    targetDistance: d, targetDuration: dur,
  };
}
function activity(id: number, distance: number, movingTime: number, date: string): ActivityLite {
  return { id, distance, movingTime, startDateLocal: `${date}T08:00:00Z` };
}

describe("assignWeek", () => {
  it("assigns two similar runs to two distinct sessions (dedup)", () => {
    const sessions = [
      session("Easy 8 km", 8000, 2880, "2026-01-06"),
      session("Long 16 km", 16000, 5760, "2026-01-11"),
    ];
    const acts = [activity(1, 8200, 2900, "2026-01-06"), activity(2, 15800, 5700, "2026-01-10")];
    const a = assignWeek(sessions, acts);
    expect(a.get(1)!.name).toBe("Easy 8 km");
    expect(a.get(2)!.name).toBe("Long 16 km");
  });

  it("matches a moved session by size, not date", () => {
    const sessions = [session("Long 16 km", 16000, 5760, "2026-01-11")];
    // done Tuesday instead of the scheduled Sunday
    const a = assignWeek(sessions, [activity(1, 16100, 5800, "2026-01-06")]);
    expect(a.get(1)!.name).toBe("Long 16 km");
  });

  it("leaves an out-of-tolerance activity unmatched", () => {
    const sessions = [session("Easy 8 km", 8000, 2880, "2026-01-06")];
    const a = assignWeek(sessions, [activity(1, 20000, 7200, "2026-01-06")]); // 150% over
    expect(a.has(1)).toBe(false);
  });

  it("assigns a target-less session by nearest date", () => {
    const sessions = [session("Track Session #1", null, null, "2026-01-07")];
    const a = assignWeek(sessions, [activity(1, 6000, 1800, "2026-01-07")]);
    expect(a.get(1)!.name).toBe("Track Session #1");
  });

  it("leaves extra activities unmatched when there are more activities than sessions", () => {
    const sessions = [session("Easy 8 km", 8000, 2880, "2026-01-06")];
    const acts = [activity(1, 8000, 2880, "2026-01-06"), activity(2, 8100, 2890, "2026-01-08")];
    const a = assignWeek(sessions, acts);
    expect(a.size).toBe(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/assign.test.ts`
Expected: FAIL — `assignWeek`/`ActivityLite` not exported.

- [ ] **Step 3: Implement `assignWeek` + `ActivityLite`**

In `strava-enricher/src/plan-matcher.ts`, add:

```ts
export interface ActivityLite {
  id: number;
  distance: number;
  movingTime: number;
  startDateLocal: string;
}

export function assignWeek(
  sessions: PlanSession[],
  activities: ActivityLite[],
): Map<number, PlanSession> {
  const assignment = new Map<number, PlanSession>();
  const usedSessions = new Set<PlanSession>();
  const usedActivities = new Set<number>();

  interface Pair {
    activity: ActivityLite;
    session: PlanSession;
    err: number;
  }
  const pairs: Pair[] = [];
  for (const activity of activities) {
    for (const session of sessions) {
      if (session.targetDistance === null && session.targetDuration === null) continue;
      let err = Infinity;
      if (session.targetDistance !== null) {
        err = Math.min(
          err,
          Math.abs(activity.distance - session.targetDistance) / session.targetDistance,
        );
      }
      if (session.targetDuration !== null) {
        err = Math.min(
          err,
          Math.abs(activity.movingTime - session.targetDuration) / session.targetDuration,
        );
      }
      if (err <= TOLERANCE) pairs.push({ activity, session, err });
    }
  }

  pairs.sort(
    (a, b) =>
      a.err - b.err ||
      a.activity.startDateLocal.localeCompare(b.activity.startDateLocal) ||
      a.session.date.localeCompare(b.session.date),
  );

  for (const p of pairs) {
    if (usedActivities.has(p.activity.id) || usedSessions.has(p.session)) continue;
    assignment.set(p.activity.id, p.session);
    usedActivities.add(p.activity.id);
    usedSessions.add(p.session);
  }

  // Date fallback for sessions without any size target.
  const targetlessSessions = sessions
    .filter(
      (s) => s.targetDistance === null && s.targetDuration === null && !usedSessions.has(s),
    )
    .sort((a, b) => a.date.localeCompare(b.date));

  for (const session of targetlessSessions) {
    let best: ActivityLite | undefined;
    let bestDiff = Infinity;
    for (const activity of activities) {
      if (usedActivities.has(activity.id)) continue;
      const diff = Math.abs(
        new Date(activity.startDateLocal.slice(0, 10)).getTime() -
          new Date(session.date).getTime(),
      );
      if (diff < bestDiff) {
        bestDiff = diff;
        best = activity;
      }
    }
    if (best) {
      assignment.set(best.id, session);
      usedActivities.add(best.id);
      usedSessions.add(session);
    }
  }

  return assignment;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/assign.test.ts`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/plan-matcher.ts strava-enricher/src/assign.test.ts
git commit -m "feat(strava-enricher): week assignment with dedup, tolerance, date fallback"
```

---

## Task 7: `strava.listActivities`

**Files:**
- Modify: `strava-enricher/src/strava.ts`
- Test: `strava-enricher/src/strava.test.ts`

- [ ] **Step 1: Write the failing test**

Create `strava-enricher/src/strava.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { listActivities } from "./strava.js";

afterEach(() => vi.restoreAllMocks());

describe("listActivities", () => {
  it("calls the athlete activities endpoint with the time range and returns the array", async () => {
    const fakeActivities = [{ id: 1 }, { id: 2 }];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeActivities,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await listActivities("tok", 100, 200);

    expect(result).toEqual(fakeActivities);
    const url = fetchMock.mock.calls[0]![0] as string;
    expect(url).toContain("/athlete/activities");
    expect(url).toContain("after=100");
    expect(url).toContain("before=200");
  });

  it("returns [] on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => "err" }),
    );
    expect(await listActivities("tok", 1, 2)).toEqual([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd strava-enricher && npx vitest run src/strava.test.ts`
Expected: FAIL — `listActivities` not exported.

- [ ] **Step 3: Implement `listActivities`**

In `strava-enricher/src/strava.ts`, add (the file already defines `STRAVA_API` and imports `StravaActivity`):

```ts
export async function listActivities(
  accessToken: string,
  after: number,
  before: number,
): Promise<StravaActivity[]> {
  const url = `${STRAVA_API}/athlete/activities?after=${after}&before=${before}&per_page=100`;
  const resp = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!resp.ok) {
    console.error(`List activities failed: ${resp.status} ${await resp.text()}`);
    return [];
  }
  return (await resp.json()) as StravaActivity[];
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd strava-enricher && npx vitest run src/strava.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/strava.ts strava-enricher/src/strava.test.ts
git commit -m "feat(strava-enricher): listActivities for the week fetch"
```

---

## Task 8: Wire into the worker + remove the old exact-date matcher

**Files:**
- Modify: `strava-enricher/src/index.ts`
- Modify: `strava-enricher/src/description.ts`
- Modify: `strava-enricher/src/plan-matcher.ts` (remove `buildPlanLookup`, `matchActivity`, `STRAVA_SPORT_TO_PLAN`, `stravaToNormalized`)
- Modify: `strava-enricher/src/plan-matcher.test.ts` (remove tests for the removed functions)

- [ ] **Step 1: Widen `buildDescription` to accept a `PlanSession`**

In `strava-enricher/src/description.ts`, change the import and the `workout` parameter type from `PlanWorkout` to `PlanSession`. Replace the import line:

```ts
import type { StravaActivity } from "./types.js";
import type { PlanSession } from "./plan-matcher.js";
```

and change the `buildDescription` signature's first parameter type to `workout: PlanSession`. The body is unchanged (it uses `workout.week`, `workout.phaseNumber`, `workout.phaseName`, `workout.description`, all present on `PlanSession`).

- [ ] **Step 2: Rewrite `processActivity` orchestration in `index.ts`**

In `strava-enricher/src/index.ts`:

(a) Replace the plan-matcher import line with:

```ts
import {
  assignWeek,
  buildPlanIndex,
  sessionsForWeek,
  stravaFamily,
  weekBounds,
  weekForDate,
  type ActivityLite,
  type PlanIndex,
} from "./plan-matcher.js";
import { getActivity, getValidAccessToken, listActivities, updateActivity } from "./strava.js";
```

(b) Replace the cached lookup helper:

```ts
let planIndex: PlanIndex | null = null;

function getPlanIndex(): PlanIndex {
  if (!planIndex) {
    planIndex = buildPlanIndex(planYamlText as string);
  }
  return planIndex;
}
```

(c) Replace the body of `processActivity` (everything after `const activity = await getActivity(...)` returns non-null) with:

```ts
  const index = getPlanIndex();
  const family = stravaFamily(activity.sport_type);
  if (!family) {
    console.log(`No sport family for ${activity.sport_type} (activity ${activity.id})`);
    return;
  }

  const activityDate = activity.start_date_local.slice(0, 10);
  const week = weekForDate(index.startDate, activityDate);
  if (week === null) {
    console.log(`Activity ${activity.id} on ${activityDate} is outside the plan`);
    return;
  }

  const sessions = sessionsForWeek(index, week, family);
  if (sessions.length === 0) {
    console.log(`No ${family} sessions planned in week ${week}`);
    return;
  }

  const { after, before, monday, sunday } = weekBounds(index.startDate, week);
  const raw = await listActivities(accessToken, after, before);
  const weekActivities: ActivityLite[] = raw
    .filter((a) => stravaFamily(a.sport_type) === family)
    .map((a) => ({
      id: a.id,
      distance: a.distance,
      movingTime: a.moving_time,
      startDateLocal: a.start_date_local,
    }))
    .filter((a) => {
      const d = a.startDateLocal.slice(0, 10);
      return d >= monday && d <= sunday;
    });

  if (!weekActivities.some((a) => a.id === activity.id)) {
    weekActivities.push({
      id: activity.id,
      distance: activity.distance,
      movingTime: activity.moving_time,
      startDateLocal: activity.start_date_local,
    });
  }

  const assignment = assignWeek(sessions, weekActivities);
  const workout = assignment.get(activity.id);
  if (!workout) {
    console.log(
      `No plan match for activity ${activity.id} (${family}, week ${week})`,
    );
    return;
  }

  const units: Units = env.UNITS === "imperial" ? "imperial" : "metric";
  const description = buildDescription(workout, activity, units);
  const ok = await updateActivity(accessToken, activity.id, workout.name, description);
  if (ok) {
    console.log(
      `Updated activity ${activity.id}: "${workout.name}" ` +
        `(week ${workout.week}, phase ${workout.phaseNumber})`,
    );
  }
```

(Keep the existing top of `processActivity`: `getValidAccessToken` → return if null, `getActivity` → return if null. `accessToken` and `env` are already in scope.)

- [ ] **Step 3: Remove the dead exact-date matcher**

In `strava-enricher/src/plan-matcher.ts`, delete `buildPlanLookup`, `matchActivity`, the `STRAVA_SPORT_TO_PLAN` constant, and `stravaToNormalized` (all superseded). Keep `firstMondayOnOrAfter`, `calculateWorkoutDate`, `normalizePlanType`, and everything added in Tasks 1–6.

In `strava-enricher/src/plan-matcher.test.ts`, delete the `describe` blocks that test `buildPlanLookup` and `matchActivity` (and remove their now-unused imports). The collision-detection test goes too — same-date/same-sport sessions are now valid (handled by assignment).

- [ ] **Step 4: Typecheck and run the whole suite**

Run: `cd strava-enricher && npx tsc --noEmit && npm test`
Expected: `No errors found`; all tests pass (Tasks 1–7 suites green, old removed tests gone).

- [ ] **Step 5: Commit**

```bash
git add strava-enricher/src/index.ts strava-enricher/src/description.ts strava-enricher/src/plan-matcher.ts strava-enricher/src/plan-matcher.test.ts
git commit -m "feat(strava-enricher): week-based matching in the worker; drop exact-date lookup"
```

- [ ] **Step 6: Deploy and verify live**

Run: `cd strava-enricher && ./deploy.sh`
Then create a test activity on a day *different* from a planned session's date but matching its distance, confirm it enriches to that session, and that two similar runs in a week get two distinct labels. Delete test activities in the Strava app afterward (the API can't). Tail logs with `npx wrangler tail --format json` if needed.

---

## Self-Review Notes

- **Spec coverage:** week window → `weekForDate` (Task 4) + `index.ts` (Task 8); per-session distance+duration targets w/ pace estimate → Tasks 2–3; garmin repeat expansion → Task 1; name + date fallbacks → Tasks 3, 6; dedup one-to-one + ±35% tolerance → Task 6; week fetch → Task 7 + Task 8; family normalization → Task 5; testing matrix → Tasks 1–7.
- **Deferred (out of scope):** enrichment content/format changes; multisport; config-exposed pace/tolerance.
- **Type consistency:** `SessionTarget` (Task 2) used by `resolveTargets` (Task 3) and `buildPlanIndex` (Task 5). `PlanSession`/`ActivityLite` defined in `plan-matcher.ts` (Tasks 5–6) and consumed by `index.ts` and `description.ts` (Task 8). `stravaFamily` (Task 5) used in Task 8. `weekBounds` fields `{after, before, monday, sunday}` (Task 4) match Task 8 usage.
- **Edge:** `index.ts` adds the current activity to `weekActivities` if the Strava list hasn't caught up yet.
