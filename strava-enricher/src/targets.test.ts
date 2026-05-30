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
