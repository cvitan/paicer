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
