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
