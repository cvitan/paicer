import { describe, expect, it } from "vitest";
import { formatTitle } from "./plan-matcher.js";
import type { PlanSession } from "./plan-matcher.js";

function session(week: number, name: string): PlanSession {
  return {
    name,
    description: "",
    type: "run",
    date: "2026-03-14",
    week,
    day: 1,
    phaseNumber: 1,
    phaseName: "Base",
    family: "run",
    targetDistance: null,
    targetDuration: null,
  };
}

describe("formatTitle", () => {
  it("prefixes the workout name with the plan week", () => {
    expect(formatTitle(session(14, "Easy 9 km"))).toBe("W14: Easy 9 km");
    expect(formatTitle(session(12, "Tempo 4x1 km"))).toBe("W12: Tempo 4x1 km");
  });
});
