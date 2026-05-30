import { describe, expect, it } from "vitest";
import { buildDescription } from "./description.js";
import type { PlanSession } from "./plan-matcher.js";
import type { StravaActivity } from "./types.js";

const workout: PlanSession = {
  name: "Tempo 2x15 min",
  description: "2x15 min @ 5:25/km + warmup/cooldown (~13 km)\nsecond line",
  type: "run",
  date: "2026-03-14",
  week: 2,
  day: 1,
  phaseNumber: 1,
  phaseName: "HM Build",
  family: "run",
  targetDistance: null,
  targetDuration: null,
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

  it("shows --:-- pace for zero-speed activity", () => {
    const out = buildDescription(workout, { ...activity, average_speed: 0 });
    expect(out).toContain("--:--");
  });
});
