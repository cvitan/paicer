# Strava Enricher

Cloudflare Worker that auto-enriches your Strava activities with training plan data. When Garmin syncs a workout to Strava, the enricher renames it and adds a description with planned-vs-actual stats.

**Before:**
> Afternoon Run

**After:**
> Tempo 2x15 min
>
> Week 2, Phase 1 (HM Build)
>
> Planned: 2x15 min @ 5:25/km + warmup/cooldown (~13 km)
> Actual: 13.2 km | 5:21/km | 1:10:32 | HR 156

## Prerequisites

- A paicer training plan (run `/paicer:create-plan` in Claude Code)
- [Node.js](https://nodejs.org/) 22+ (`brew install node`)
- A free [Cloudflare account](https://dash.cloudflare.com/sign-up)
- A [Strava API app](https://www.strava.com/settings/api) (set callback domain to `localhost`)

## Setup

### 1. Install Wrangler and log in

```bash
cd strava-enricher
npm install
npx wrangler login
```

If this is your first Cloudflare worker, set up your workers.dev subdomain in the [Cloudflare dashboard](https://dash.cloudflare.com) under **Workers & Pages** → **Your subdomain**. Your worker will deploy to `https://paicer-strava-enricher.<your-subdomain>.workers.dev`.

### 2. Add your Strava credentials

```bash
cp .dev.vars.example .dev.vars
```

Edit `.dev.vars` with your client ID and secret from your [Strava API app](https://www.strava.com/settings/api). Leave `STRAVA_VERIFY_TOKEN` as is.

### 3. Run the setup script

```bash
./setup.sh
```

This handles everything else: KV namespace creation, wrangler.toml generation, OAuth authorization, token storage, secrets, deployment, and webhook subscription. Follow the prompts — the worker URL is detected automatically from the deploy output.

## Deploy

After changing your training plan:

```bash
# From the repo root
make deploy-strava-enricher
```

This copies your plan YAML into the worker and redeploys.

## How it works

Garmin Watch &rarr; Garmin Connect &rarr; Strava &rarr; Webhook &rarr; Worker &rarr; Updates activity name + description

The worker matches activities to your plan by date and sport type, using the same date calculation logic as the rest of paicer. Unmatched activities (manual entries, unplanned workouts) are left untouched.
