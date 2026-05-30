#!/usr/bin/env bash
set -euo pipefail

# Redeploy the Strava enricher after a plan change. Reads the plan path and
# units from ~/.paicer/config (set via `paicer config set`).
#
# Usage:
#   cd strava-enricher
#   ./deploy.sh

if [[ ! -f wrangler.toml ]]; then
  echo "Error: wrangler.toml not found. Run ./setup.sh first."
  exit 1
fi

read_config() {
  local key="$1"
  local config="${PAICER_HOME:-$HOME/.paicer}/config"
  [[ -f "$config" ]] || return 0
  # paicer writes each entry as: key = "value"
  sed -n "s/^${key}[[:space:]]*=[[:space:]]*\"\(.*\)\"[[:space:]]*\$/\1/p" "$config" | head -1
}

PLAN_PATH=$(read_config plan)

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found in ~/.paicer/config."
  echo "Set it with: paicer config set plan /path/to/your-plan.yaml"
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml

echo "Running: npx wrangler deploy"
npx wrangler deploy

echo "Deployed. Plan is now live."
