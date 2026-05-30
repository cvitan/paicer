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
