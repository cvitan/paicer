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

- **paicer + a training plan.** Install the CLI (`pip install paicer`), then create a plan with `/paicer:create-plan` in Claude Code (or point at an existing one: `paicer config set plan /path/to/plan.yaml`). The enricher reads your plan path and units from `~/.paicer/config` at deploy time — you don't need to clone the paicer repo.
- [Node.js](https://nodejs.org/) 22+ (`brew install node`)
- A free [Cloudflare account](https://dash.cloudflare.com/sign-up)
- A [Strava API app](https://www.strava.com/settings/api) (set callback domain to `localhost`)

## Setup

### 1. Get the enricher

You don't need to clone the whole paicer repo — `degit` copies just this worker into a new directory:

```bash
npx degit cvitan/paicer/strava-enricher my-strava-enricher
cd my-strava-enricher
npm install
npx wrangler login
```

(Already working inside the paicer repo? Just `cd strava-enricher && npm install && npx wrangler login` instead.)

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

After changing your training plan, from the worker directory:

```bash
./deploy.sh
```

This copies your plan YAML (from `~/.paicer/config`) into the worker and redeploys with your configured units.

## How it works

Garmin Watch &rarr; Garmin Connect &rarr; Strava &rarr; Webhook &rarr; Worker &rarr; Updates activity name + description

The worker matches activities to your plan by date and sport type, using the same date calculation logic as the rest of paicer. Unmatched activities (manual entries, unplanned workouts) are left untouched.
