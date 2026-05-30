import type { StravaActivity } from "./types.js";
import type { PlanSession } from "./plan-matcher.js";

export type Units = "metric" | "imperial";

const METERS_PER_MILE = 1609.34;

function formatPace(metersPerSecond: number, units: Units): string {
  if (metersPerSecond <= 0) return "--:--";
  const secsPerUnit =
    units === "imperial"
      ? METERS_PER_MILE / metersPerSecond
      : 1000 / metersPerSecond;
  const totalRounded = Math.round(secsPerUnit);
  const mins = Math.floor(totalRounded / 60);
  const secs = totalRounded % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function formatDistance(meters: number, units: Units): string {
  const value =
    units === "imperial" ? meters / METERS_PER_MILE : meters / 1000;
  return value.toFixed(1);
}

export function buildDescription(
  workout: PlanSession,
  activity: StravaActivity,
  units: Units = "metric",
): string {
  const header =
    `Week ${workout.week}, Phase ${workout.phaseNumber} (${workout.phaseName})`;

  const planned = workout.description.split("\n")[0] ?? "";

  const distUnit = units === "imperial" ? "mi" : "km";
  const paceUnit = units === "imperial" ? "/mi" : "/km";

  const dist = formatDistance(activity.distance, units);
  const pace = formatPace(activity.average_speed, units);
  const duration = formatDuration(activity.moving_time);

  let actual = `${dist} ${distUnit} | ${pace}${paceUnit} | ${duration}`;
  if (activity.average_heartrate) {
    actual += ` | HR ${Math.round(activity.average_heartrate)}`;
  }

  const lines = [header, ""];
  if (planned) {
    lines.push(`Planned: ${planned}`);
  }
  lines.push(`Actual: ${actual}`);

  return lines.join("\n");
}
