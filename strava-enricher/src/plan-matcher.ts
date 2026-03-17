import yaml from "js-yaml";
import type { PlanWorkout, PlanYaml } from "./types.js";

const STRAVA_SPORT_TO_PLAN: Record<string, string[]> = {
  Run: ["run", "track", "race"],
  TrailRun: ["run", "track", "race"],
  VirtualRun: ["run", "track", "race"],
  Ride: ["bike"],
  VirtualRide: ["bike"],
  Swim: ["swim"],
};

function firstMondayOnOrAfter(dateStr: string): Date {
  const d = new Date(`${dateStr}T00:00:00`);
  const dayOfWeek = d.getDay(); // 0=Sun, 1=Mon, ...
  const daysUntilMonday = dayOfWeek === 0 ? 1 : dayOfWeek === 1 ? 0 : 8 - dayOfWeek;
  d.setDate(d.getDate() + daysUntilMonday);
  return d;
}

function calculateWorkoutDate(
  startDate: string,
  week: number,
  day: number,
  trainingDays: number[],
): string {
  const weekday = trainingDays[day - 1];
  if (weekday === undefined) {
    throw new Error(
      `Day ${day} out of range for ${trainingDays.length} training days`,
    );
  }

  const firstMonday = firstMondayOnOrAfter(startDate);
  const weekStart = new Date(firstMonday);
  weekStart.setDate(weekStart.getDate() + (week - 1) * 7);

  const workoutDate = new Date(weekStart);
  workoutDate.setDate(workoutDate.getDate() + (weekday - 1));

  const y = workoutDate.getFullYear();
  const m = String(workoutDate.getMonth() + 1).padStart(2, "0");
  const d = String(workoutDate.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function buildPlanLookup(
  yamlText: string,
): Map<string, PlanWorkout> {
  const plan = yaml.load(yamlText) as PlanYaml;
  const globalTrainingDays = plan.plan.training_days ?? [1, 2, 3, 4, 5, 6, 7];
  const startDate = plan.plan.start_date;

  const lookup = new Map<string, PlanWorkout>();

  for (const phase of plan.phases) {
    const phaseTrainingDays = phase.training_days ?? globalTrainingDays;

    for (const week of phase.weeks) {
      for (const workout of week.workouts) {
        const date = calculateWorkoutDate(
          startDate,
          week.week,
          workout.day,
          phaseTrainingDays,
        );

        const sportKey = normalizePlanType(workout.type);
        const key = `${date}:${sportKey}`;

        if (lookup.has(key)) {
          const existing = lookup.get(key);
          throw new Error(
            `Plan collision: "${workout.name}" and "${existing?.name}" ` +
            `both map to ${key}. Two workouts on the same date with the ` +
            `same sport type cannot be distinguished.`,
          );
        }

        lookup.set(key, {
          name: workout.name,
          description: workout.description ?? "",
          type: workout.type,
          date,
          week: week.week,
          day: workout.day,
          phaseNumber: phase.phase,
          phaseName: phase.name,
          optional: workout.optional ?? false,
        });
      }
    }
  }

  return lookup;
}

function normalizePlanType(planType: string): string {
  switch (planType) {
    case "run":
    case "track":
    case "race":
      return "run";
    case "bike":
      return "bike";
    case "swim":
      return "swim";
    default:
      return planType;
  }
}

function stravaToNormalized(stravaSportType: string): string | null {
  const planTypes = STRAVA_SPORT_TO_PLAN[stravaSportType];
  if (!planTypes || planTypes.length === 0) return null;
  return normalizePlanType(planTypes[0] ?? "");
}

export function matchActivity(
  lookup: Map<string, PlanWorkout>,
  stravaSportType: string,
  startDateLocal: string,
): PlanWorkout | null {
  const normalized = stravaToNormalized(stravaSportType);
  if (!normalized) return null;

  // startDateLocal is ISO 8601: "2026-03-14T18:30:00Z" — extract date
  const date = startDateLocal.slice(0, 10);
  const key = `${date}:${normalized}`;

  return lookup.get(key) ?? null;
}
