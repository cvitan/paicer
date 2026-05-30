import {
  assignWeek,
  buildPlanIndex,
  formatTitle,
  sessionsForWeek,
  stravaFamily,
  weekBounds,
  weekForDate,
  type ActivityLite,
  type PlanIndex,
} from "./plan-matcher.js";
import { getActivity, getValidAccessToken, listActivities, updateActivity } from "./strava.js";
import type { Env, StravaWebhookEvent } from "./types.js";

import planYamlText from "../plan.yaml";

let planIndex: PlanIndex | null = null;

function getPlanIndex(): PlanIndex {
  if (!planIndex) {
    planIndex = buildPlanIndex(planYamlText as string);
  }
  return planIndex;
}

async function processActivity(
  env: Env,
  event: StravaWebhookEvent,
): Promise<void> {
  const accessToken = await getValidAccessToken(env, event.owner_id);
  if (!accessToken) return;

  const activity = await getActivity(accessToken, event.object_id);
  if (!activity) return;

  const index = getPlanIndex();
  const family = stravaFamily(activity.sport_type);
  if (!family) {
    console.log(`No sport family for ${activity.sport_type} (activity ${activity.id})`);
    return;
  }

  const activityDate = activity.start_date_local.slice(0, 10);
  const week = weekForDate(index.startDate, activityDate);
  if (week === null) {
    console.log(`Activity ${activity.id} on ${activityDate} is outside the plan`);
    return;
  }

  const sessions = sessionsForWeek(index, week, family);
  if (sessions.length === 0) {
    console.log(`No ${family} sessions planned in week ${week}`);
    return;
  }

  const { after, before, monday, sunday } = weekBounds(index.startDate, week);
  const raw = await listActivities(accessToken, after, before);
  const weekActivities: ActivityLite[] = raw
    .filter((a) => stravaFamily(a.sport_type) === family)
    .map((a) => ({
      id: a.id,
      distance: a.distance,
      movingTime: a.moving_time,
      startDateLocal: a.start_date_local,
    }))
    .filter((a) => {
      const d = a.startDateLocal.slice(0, 10);
      return d >= monday && d <= sunday;
    });

  if (!weekActivities.some((a) => a.id === activity.id)) {
    weekActivities.push({
      id: activity.id,
      distance: activity.distance,
      movingTime: activity.moving_time,
      startDateLocal: activity.start_date_local,
    });
  }

  const assignment = assignWeek(sessions, weekActivities);
  const workout = assignment.get(activity.id);
  if (!workout) {
    console.log(
      `No plan match for activity ${activity.id} (${family}, week ${week})`,
    );
    return;
  }

  const title = formatTitle(workout);
  const ok = await updateActivity(accessToken, activity.id, title);
  if (ok) {
    console.log(
      `Updated activity ${activity.id}: "${title}" (phase ${workout.phaseNumber})`,
    );
  }
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);

    // The webhook lives at a secret path: /webhook/<WEBHOOK_SECRET>. Strava
    // does not sign payloads, so this per-deployment secret (set at setup time
    // and baked into the registered callback URL) is what actually
    // authenticates incoming events — owner_id alone is caller-supplied and
    // spoofable. Requests to the wrong path get a plain 404.
    if (env.WEBHOOK_SECRET && url.pathname === `/webhook/${env.WEBHOOK_SECRET}`) {
      if (request.method === "GET") {
        return handleWebhookValidation(url, env);
      }
      if (request.method === "POST") {
        return handleWebhookEvent(request, env, ctx);
      }
    }

    // Health check
    if (request.method === "GET" && url.pathname === "/") {
      return new Response("strava-worker ok");
    }

    return new Response("Not found", { status: 404 });
  },
};

function handleWebhookValidation(url: URL, env: Env): Response {
  const mode = url.searchParams.get("hub.mode");
  const token = url.searchParams.get("hub.verify_token");
  const challenge = url.searchParams.get("hub.challenge");

  if (mode === "subscribe" && token === env.STRAVA_VERIFY_TOKEN && challenge) {
    return Response.json({ "hub.challenge": challenge });
  }

  return new Response("Forbidden", { status: 403 });
}

async function handleWebhookEvent(
  request: Request,
  env: Env,
  ctx: ExecutionContext,
): Promise<Response> {
  let event: StravaWebhookEvent;
  try {
    event = (await request.json()) as StravaWebhookEvent;
  } catch {
    return new Response("Bad request", { status: 400 });
  }

  // Reject events that aren't for the configured athlete. Strava does not
  // sign webhook payloads, so owner_id is our only authenticity signal.
  if (env.STRAVA_ATHLETE_ID && event.owner_id !== Number(env.STRAVA_ATHLETE_ID)) {
    return new Response("Forbidden", { status: 403 });
  }

  // Only process new activities
  if (event.object_type === "activity" && event.aspect_type === "create") {
    ctx.waitUntil(processActivity(env, event));
  }

  return new Response("OK", { status: 200 });
}
