import { describe, expect, it } from "vitest";
import { buildPlanLookup, matchActivity } from "./plan-matcher.js";

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
