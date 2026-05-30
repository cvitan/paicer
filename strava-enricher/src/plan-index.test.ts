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
