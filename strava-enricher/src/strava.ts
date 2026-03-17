import type { Env, StravaActivity, StravaTokens } from "./types.js";

const STRAVA_API = "https://www.strava.com/api/v3";
const STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token";
const TOKEN_EXPIRY_BUFFER_SECS = 300; // refresh 5 min before expiry

export async function getTokens(
  env: Env,
  athleteId: number,
): Promise<StravaTokens | null> {
  const raw = await env.STRAVA_TOKENS.get(`tokens:${athleteId}`);
  if (!raw) return null;
  return JSON.parse(raw) as StravaTokens;
}

async function saveTokens(
  env: Env,
  athleteId: number,
  tokens: StravaTokens,
): Promise<void> {
  await env.STRAVA_TOKENS.put(
    `tokens:${athleteId}`,
    JSON.stringify(tokens),
  );
}

export async function getValidAccessToken(
  env: Env,
  athleteId: number,
): Promise<string | null> {
  const tokens = await getTokens(env, athleteId);
  if (!tokens) {
    console.error(`No tokens found for athlete ${athleteId}`);
    return null;
  }

  const now = Math.floor(Date.now() / 1000);
  if (tokens.expires_at - now > TOKEN_EXPIRY_BUFFER_SECS) {
    return tokens.access_token;
  }

  // Refresh
  const resp = await fetch(STRAVA_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: env.STRAVA_CLIENT_ID,
      client_secret: env.STRAVA_CLIENT_SECRET,
      grant_type: "refresh_token",
      refresh_token: tokens.refresh_token,
    }),
  });

  if (!resp.ok) {
    console.error(
      `Token refresh failed: ${resp.status} ${await resp.text()}`,
    );
    return null;
  }

  const data = (await resp.json()) as {
    access_token: string;
    refresh_token: string;
    expires_at: number;
  };

  const updated: StravaTokens = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: data.expires_at,
  };

  await saveTokens(env, athleteId, updated);
  return updated.access_token;
}

export async function getActivity(
  accessToken: string,
  activityId: number,
): Promise<StravaActivity | null> {
  const resp = await fetch(`${STRAVA_API}/activities/${activityId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!resp.ok) {
    console.error(
      `GET activity ${activityId} failed: ${resp.status} ${await resp.text()}`,
    );
    return null;
  }

  return (await resp.json()) as StravaActivity;
}

export async function updateActivity(
  accessToken: string,
  activityId: number,
  name: string,
  description: string,
): Promise<boolean> {
  const resp = await fetch(`${STRAVA_API}/activities/${activityId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, description }),
  });

  if (!resp.ok) {
    console.error(
      `PUT activity ${activityId} failed: ${resp.status} ${await resp.text()}`,
    );
    return false;
  }

  return true;
}
