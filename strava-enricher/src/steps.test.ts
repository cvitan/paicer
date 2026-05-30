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
