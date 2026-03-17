import type { PlanWorkout, StravaActivity } from "./types.js";

function formatPace(metersPerSecond: number): string {
  if (metersPerSecond <= 0) return "--:--";
  const secsPerKm = 1000 / metersPerSecond;
  const mins = Math.floor(secsPerKm / 60);
  const secs = Math.round(secsPerKm % 60);
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

function formatDistance(meters: number): string {
  const km = meters / 1000;
  return km % 1 === 0 ? `${km}` : km.toFixed(1);
}

export function buildDescription(
  workout: PlanWorkout,
  activity: StravaActivity,
): string {
  const header =
    `Week ${workout.week}, Phase ${workout.phaseNumber} (${workout.phaseName})`;

  const planned = workout.description.split("\n")[0] ?? "";

  const dist = formatDistance(activity.distance);
  const pace = formatPace(activity.average_speed);
  const duration = formatDuration(activity.moving_time);

  let actual = `${dist} km | ${pace}/km | ${duration}`;
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
