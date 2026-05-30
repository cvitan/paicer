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
