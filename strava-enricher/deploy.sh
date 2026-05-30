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
  python3 - "$1" <<'PY'
import os, sys, tomllib
from pathlib import Path
key = sys.argv[1]
home = os.environ.get("PAICER_HOME")
base = Path(home) if home else Path.home() / ".paicer"
path = base / "config"
if not path.exists():
    sys.exit(0)
data = tomllib.load(open(path, "rb"))
val = data.get(key)
if val is not None:
    print(val)
PY
}

PLAN_PATH=$(read_config plan)
UNITS=$(read_config units)
UNITS="${UNITS:-metric}"

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found in ~/.paicer/config."
  echo "Set it with: paicer config set plan /path/to/your-plan.yaml"
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml

echo "Running: npx wrangler deploy --var UNITS:${UNITS}"
npx wrangler deploy --var "UNITS:${UNITS}"

echo "Deployed. Plan and units are now live."
