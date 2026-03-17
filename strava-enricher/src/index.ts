import { buildDescription } from "./description.js";
import { buildPlanLookup, matchActivity } from "./plan-matcher.js";
import { getActivity, getValidAccessToken, updateActivity } from "./strava.js";
import type { Env, PlanWorkout, StravaWebhookEvent } from "./types.js";

import planYamlText from "../plan.yaml";

let planLookup: Map<string, PlanWorkout> | null = null;

function getPlanLookup(): Map<string, PlanWorkout> {
  if (!planLookup) {
    planLookup = buildPlanLookup(planYamlText as string);
  }
  return planLookup;
}

async function processActivity(
  env: Env,
  event: StravaWebhookEvent,
): Promise<void> {
  const accessToken = await getValidAccessToken(env, event.owner_id);
  if (!accessToken) return;

  const activity = await getActivity(accessToken, event.object_id);
  if (!activity) return;

  const lookup = getPlanLookup();
  const workout = matchActivity(
    lookup,
    activity.sport_type,
    activity.start_date_local,
  );

  if (!workout) {
    console.log(
      `No plan match for activity ${activity.id} ` +
      `(${activity.sport_type} on ${activity.start_date_local})`,
    );
    return;
  }

  const description = buildDescription(workout, activity);
  const ok = await updateActivity(
    accessToken,
    activity.id,
    workout.name,
    description,
  );

  if (ok) {
    console.log(
      `Updated activity ${activity.id}: "${workout.name}" ` +
      `(week ${workout.week}, phase ${workout.phaseNumber})`,
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

    // Webhook validation (GET)
    if (request.method === "GET" && url.pathname === "/webhook") {
      return handleWebhookValidation(url, env);
    }

    // Webhook events (POST)
    if (request.method === "POST" && url.pathname === "/webhook") {
      return handleWebhookEvent(request, env, ctx);
    }

    // Health check
    if (request.method === "GET" && url.pathname === "/") {
      return new Response("strava-worker ok");
    }

    // KV diagnostic — remove after debugging
    if (request.method === "GET" && url.pathname === "/debug/kv") {
      // Write a test key through the binding, then list everything
      await env.STRAVA_TOKENS.put("debug:test", "hello");
      const keys = await env.STRAVA_TOKENS.list();
      const keyNames = keys.keys.map((k) => k.name);
      const debugVal = await env.STRAVA_TOKENS.get("debug:test");
      await env.STRAVA_TOKENS.delete("debug:test");
      return Response.json({ keys: keyNames, debugWrite: debugVal });
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

  // Only process new activities
  if (event.object_type === "activity" && event.aspect_type === "create") {
    ctx.waitUntil(processActivity(env, event));
  }

  return new Response("OK", { status: 200 });
}
