export interface Env {
  STRAVA_TOKENS: KVNamespace;
  STRAVA_CLIENT_ID: string;
  STRAVA_CLIENT_SECRET: string;
  STRAVA_VERIFY_TOKEN: string;
}

export interface StravaWebhookEvent {
  aspect_type: "create" | "update" | "delete";
  event_time: number;
  object_id: number;
  object_type: "activity" | "athlete";
  owner_id: number;
  subscription_id: number;
  updates: Record<string, string>;
}

export interface StravaTokens {
  access_token: string;
  refresh_token: string;
  expires_at: number;
}

export interface StravaActivity {
  id: number;
  name: string;
  sport_type: string;
  start_date: string;
  start_date_local: string;
  distance: number;
  moving_time: number;
  elapsed_time: number;
  average_speed: number;
  average_heartrate?: number;
  max_heartrate?: number;
  total_elevation_gain: number;
  description: string | null;
}

export interface PlanWorkout {
  name: string;
  description: string;
  type: string;
  date: string;
  week: number;
  day: number;
  phaseNumber: number;
  phaseName: string;
  optional: boolean;
}

export interface PlanYaml {
  plan: {
    name: string;
    start_date: string;
    training_days?: number[];
  };
  phases: PlanPhase[];
}

interface PlanPhase {
  phase: number;
  name: string;
  training_days?: number[];
  weeks: PlanWeek[];
}

interface PlanWeek {
  week: number;
  description?: string;
  workouts: PlanWeekWorkout[];
}

interface PlanWeekWorkout {
  day: number;
  type: string;
  name: string;
  description?: string;
  optional?: boolean;
}
