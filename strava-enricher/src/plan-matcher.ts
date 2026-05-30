import yaml from "js-yaml";
import type { GarminStep, PlanWorkout, PlanYaml } from "./types.js";

export function expandSteps(steps: GarminStep[]): GarminStep[] {
  const out: GarminStep[] = [];
  for (const step of steps) {
    if (step.stepType === "repeat" && step.steps) {
      const iterations = step.numberOfIterations ?? 1;
      for (let i = 0; i < iterations; i++) {
        out.push(...expandSteps(step.steps));
      }
    } else {
      out.push(step);
    }
  }
  return out;
}

const PACE_SEC_PER_METER: Record<string, number> = {
  run: 0.36, // 6:00/km
  bike: 0.12, // 30 km/h
  swim: 1.2, // 2:00/100 m
};
const TOLERANCE = 0.35;

export interface SessionTarget {
  distance: number | null;
  duration: number | null;
}

export function stepTargets(steps: GarminStep[], family: string): SessionTarget {
  const pace = PACE_SEC_PER_METER[family];
  let distance = 0;
  let duration = 0;
  for (const step of expandSteps(steps)) {
    const v = step.endConditionValue;
    if (v === undefined) continue;
    if (step.endCondition === "distance") {
      distance += v;
      if (pace !== undefined) duration += v * pace;
    } else if (step.endCondition === "time") {
      duration += v;
      if (pace !== undefined) distance += v / pace;
    }
  }
  return {
    distance: distance > 0 ? Math.round(distance) : null,
    duration: duration > 0 ? Math.round(duration) : null,
  };
}

export function parseNameTarget(name: string, family: string): SessionTarget {
  const pace = PACE_SEC_PER_METER[family];
  let distance: number | null = null;
  let duration: number | null = null;

  const distMatch = name.match(/(\d+(?:\.\d+)?)\s*(km|mi|m)\b/i);
  if (distMatch) {
    const value = parseFloat(distMatch[1]!);
    const unit = distMatch[2]!.toLowerCase();
    const meters = unit === "km" ? value * 1000 : unit === "mi" ? value * 1609.34 : value;
    distance = Math.round(meters);
  }

  const durMatch = name.match(/(\d+)\s*min\b/i);
  if (durMatch) {
    duration = parseInt(durMatch[1]!, 10) * 60;
  }

  if (pace !== undefined) {
    if (distance !== null && duration === null) duration = Math.round(distance * pace);
    if (duration !== null && distance === null) distance = Math.round(duration / pace);
  }
  return { distance, duration };
}

export function resolveTargets(
  workout: { name: string; garmin?: { steps?: GarminStep[] } },
  family: string,
): SessionTarget {
  const steps = workout.garmin?.steps;
  if (steps && steps.length > 0) {
    const fromSteps = stepTargets(steps, family);
    if (fromSteps.distance !== null || fromSteps.duration !== null) return fromSteps;
  }
  return parseNameTarget(workout.name, family);
}

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

export function weekForDate(startDate: string, dateStr: string): number | null {
  const firstMonday = firstMondayOnOrAfter(startDate);
  const d = new Date(`${dateStr}T00:00:00`);
  const diffDays = Math.round((d.getTime() - firstMonday.getTime()) / 86400000);
  if (diffDays < 0) return null;
  return Math.floor(diffDays / 7) + 1;
}

function isoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function weekBounds(
  startDate: string,
  week: number,
): { after: number; before: number; monday: string; sunday: string } {
  const firstMonday = firstMondayOnOrAfter(startDate);
  const monday = new Date(firstMonday);
  monday.setDate(monday.getDate() + (week - 1) * 7);
  const sunday = new Date(monday);
  sunday.setDate(sunday.getDate() + 6);
  // Padded ±1 day UTC epoch range for the Strava fetch; exact filtering is
  // done by local date afterwards.
  const after = Math.floor(monday.getTime() / 1000) - 86400;
  const before = Math.floor(sunday.getTime() / 1000) + 2 * 86400;
  return { after, before, monday: isoDate(monday), sunday: isoDate(sunday) };
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
        // Mirror paicer's scheduling (sync.py): an optional workout whose day
        // exceeds the phase's training_days is an "extra" day that never gets
        // scheduled, so it must not be matched here either. Without this the
        // lookup throws on plans that use optional overflow days.
        if ((workout.optional ?? false) && workout.day > phaseTrainingDays.length) {
          continue;
        }

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

export interface PlanSession {
  name: string;
  description: string;
  type: string;
  date: string;
  week: number;
  day: number;
  phaseNumber: number;
  phaseName: string;
  family: string;
  targetDistance: number | null;
  targetDuration: number | null;
}

export interface PlanIndex {
  startDate: string;
  sessions: PlanSession[];
}

export function buildPlanIndex(yamlText: string): PlanIndex {
  const plan = yaml.load(yamlText) as PlanYaml;
  const globalTrainingDays = plan.plan.training_days ?? [1, 2, 3, 4, 5, 6, 7];
  const startDate = plan.plan.start_date;
  const sessions: PlanSession[] = [];

  for (const phase of plan.phases) {
    const phaseTrainingDays = phase.training_days ?? globalTrainingDays;
    for (const week of phase.weeks) {
      for (const workout of week.workouts) {
        if ((workout.optional ?? false) && workout.day > phaseTrainingDays.length) {
          continue;
        }
        const date = calculateWorkoutDate(
          startDate,
          week.week,
          workout.day,
          phaseTrainingDays,
        );
        const family = normalizePlanType(workout.type);
        const targets = resolveTargets(
          { name: workout.name, garmin: workout.garmin },
          family,
        );
        sessions.push({
          name: workout.name,
          description: workout.description ?? "",
          type: workout.type,
          date,
          week: week.week,
          day: workout.day,
          phaseNumber: phase.phase,
          phaseName: phase.name,
          family,
          targetDistance: targets.distance,
          targetDuration: targets.duration,
        });
      }
    }
  }
  return { startDate, sessions };
}

export function sessionsForWeek(
  index: PlanIndex,
  week: number,
  family: string,
): PlanSession[] {
  return index.sessions.filter((s) => s.week === week && s.family === family);
}

const STRAVA_SPORT_TO_FAMILY: Record<string, string> = {
  Run: "run",
  TrailRun: "run",
  VirtualRun: "run",
  Ride: "bike",
  VirtualRide: "bike",
  Swim: "swim",
};

export function stravaFamily(stravaSportType: string): string | null {
  return STRAVA_SPORT_TO_FAMILY[stravaSportType] ?? null;
}

export interface ActivityLite {
  id: number;
  distance: number;
  movingTime: number;
  startDateLocal: string;
}

export function assignWeek(
  sessions: PlanSession[],
  activities: ActivityLite[],
): Map<number, PlanSession> {
  const assignment = new Map<number, PlanSession>();
  const usedSessions = new Set<PlanSession>();
  const usedActivities = new Set<number>();

  interface Pair {
    activity: ActivityLite;
    session: PlanSession;
    err: number;
  }
  const pairs: Pair[] = [];
  for (const activity of activities) {
    for (const session of sessions) {
      if (session.targetDistance === null && session.targetDuration === null) continue;
      let err = Infinity;
      if (session.targetDistance !== null) {
        err = Math.min(
          err,
          Math.abs(activity.distance - session.targetDistance) / session.targetDistance,
        );
      }
      if (session.targetDuration !== null) {
        err = Math.min(
          err,
          Math.abs(activity.movingTime - session.targetDuration) / session.targetDuration,
        );
      }
      if (err <= TOLERANCE) pairs.push({ activity, session, err });
    }
  }

  pairs.sort(
    (a, b) =>
      a.err - b.err ||
      a.activity.startDateLocal.localeCompare(b.activity.startDateLocal) ||
      a.session.date.localeCompare(b.session.date),
  );

  for (const p of pairs) {
    if (usedActivities.has(p.activity.id) || usedSessions.has(p.session)) continue;
    assignment.set(p.activity.id, p.session);
    usedActivities.add(p.activity.id);
    usedSessions.add(p.session);
  }

  // Date fallback for sessions without any size target.
  const targetlessSessions = sessions
    .filter(
      (s) => s.targetDistance === null && s.targetDuration === null && !usedSessions.has(s),
    )
    .sort((a, b) => a.date.localeCompare(b.date));

  for (const session of targetlessSessions) {
    let best: ActivityLite | undefined;
    let bestDiff = Infinity;
    for (const activity of activities) {
      if (usedActivities.has(activity.id)) continue;
      const diff = Math.abs(
        new Date(activity.startDateLocal.slice(0, 10)).getTime() -
          new Date(session.date).getTime(),
      );
      if (diff < bestDiff) {
        bestDiff = diff;
        best = activity;
      }
    }
    if (best) {
      assignment.set(best.id, session);
      usedActivities.add(best.id);
      usedSessions.add(session);
    }
  }

  return assignment;
}
