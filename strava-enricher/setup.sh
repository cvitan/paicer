#!/usr/bin/env bash
set -euo pipefail

# Paicer Strava Enricher setup: OAuth authorization + webhook subscription.
# Run once after creating your Strava API app at https://www.strava.com/settings/api
#
# Prerequisites:
#   - wrangler authenticated (npx wrangler login)
#   - .dev.vars populated with STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET
#
# Usage:
#   cd strava-enricher
#   ./setup.sh

# Load secrets from .dev.vars
if [[ ! -f .dev.vars ]]; then
  echo "Error: .dev.vars not found. Copy from .dev.vars.example and fill in your credentials."
  exit 1
fi

# shellcheck source=/dev/null
source .dev.vars

if [[ -z "${STRAVA_CLIENT_ID:-}" || -z "${STRAVA_CLIENT_SECRET:-}" ]]; then
  echo "Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .dev.vars"
  exit 1
fi

VERIFY_TOKEN="${STRAVA_VERIFY_TOKEN:-paicer-strava-hook}"

echo "=== Step 1: Generate wrangler.toml ==="

if [[ ! -f wrangler.example.toml ]]; then
  echo "Error: wrangler.example.toml not found. Run this from the strava-enricher directory."
  exit 1
fi

# Reuse existing KV namespace ID from wrangler.toml if present
if [[ -f wrangler.toml ]]; then
  KV_ID=$(grep '^id' wrangler.toml | head -1 | sed 's/.*= *"\(.*\)"/\1/')
  if [[ -n "$KV_ID" && "$KV_ID" != "YOUR_KV_NAMESPACE_ID" ]]; then
    echo "Reusing KV namespace from existing wrangler.toml: ${KV_ID}"
  else
    KV_ID=""
  fi
fi

if [[ -z "${KV_ID:-}" ]]; then
  echo "Creating KV namespace..."
  # `create` exits non-zero if the namespace already exists; `|| true` keeps
  # `set -e` from killing the script so we can fall through to the lookup.
  KV_OUTPUT=$(npx wrangler kv namespace create STRAVA_TOKENS 2>&1) || true
  KV_ID=$(echo "$KV_OUTPUT" | grep -o '"[a-f0-9]\{32\}"' | tr -d '"' | head -1) || true

  if [[ -z "$KV_ID" ]]; then
    echo "Namespace may already exist, looking it up..."
    KV_LIST=$(npx wrangler kv namespace list 2>&1) || true
    # Track the most recent "id" line, print it when the matching title appears.
    KV_ID=$(echo "$KV_LIST" | awk -F'"' '/"id":/{id=$4} /"title": "STRAVA_TOKENS"/{print id; exit}') || true
  fi
fi

if [[ -z "$KV_ID" ]]; then
  echo "Failed to create or find KV namespace."
  echo "Find its ID at https://dash.cloudflare.com and create wrangler.toml manually from wrangler.example.toml."
  exit 1
fi

sed "s/YOUR_KV_NAMESPACE_ID/${KV_ID}/" wrangler.example.toml > wrangler.toml
echo "Generated wrangler.toml with KV namespace ID: ${KV_ID}"

echo ""
echo "=== Step 2: OAuth Authorization ==="
echo ""
echo "Open this URL in your browser and authorize the app:"
echo ""
echo "  https://www.strava.com/oauth/authorize?client_id=${STRAVA_CLIENT_ID}&response_type=code&redirect_uri=http://localhost&scope=activity:read_all,activity:write&approval_prompt=auto"
echo ""
echo "After authorizing, you'll be redirected to localhost with a 'code' parameter."
echo "Paste the code from the URL (the value after ?code= and before &scope=):"
echo ""
read -rp "Authorization code: " AUTH_CODE

if [[ -z "$AUTH_CODE" ]]; then
  echo "Error: No authorization code provided"
  exit 1
fi

echo ""
echo "Exchanging code for tokens..."

TOKEN_RESPONSE=$(curl -s -X POST "https://www.strava.com/oauth/token" \
  -d "client_id=${STRAVA_CLIENT_ID}" \
  -d "client_secret=${STRAVA_CLIENT_SECRET}" \
  -d "code=${AUTH_CODE}" \
  -d "grant_type=authorization_code")

# Check for errors
if echo "$TOKEN_RESPONSE" | grep -q '"errors"'; then
  echo "Error from Strava:"
  echo "$TOKEN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TOKEN_RESPONSE"
  exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
EXPIRES_AT=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['expires_at'])")
ATHLETE_ID=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['athlete']['id'])")

echo "Authorized as athlete ${ATHLETE_ID}"
echo "Access token expires at: ${EXPIRES_AT}"

echo ""
echo "=== Step 3: Store tokens in KV ==="

TOKEN_JSON=$(ACCESS_TOKEN="$ACCESS_TOKEN" REFRESH_TOKEN="$REFRESH_TOKEN" EXPIRES_AT="$EXPIRES_AT" python3 -c "
import json, os
print(json.dumps({
    'access_token': os.environ['ACCESS_TOKEN'],
    'refresh_token': os.environ['REFRESH_TOKEN'],
    'expires_at': int(os.environ['EXPIRES_AT']),
}))
")

# --remote is required: without it wrangler writes to a local simulation, and
# the deployed worker (which reads the real remote namespace) never sees it.
npx wrangler kv key put "tokens:${ATHLETE_ID}" "$TOKEN_JSON" --namespace-id "$KV_ID" --remote
echo "Tokens stored in KV as tokens:${ATHLETE_ID}"

# Verify the token was actually stored (also --remote, so we check the real store)
echo "Verifying token storage..."
VERIFY=$(npx wrangler kv key get "tokens:${ATHLETE_ID}" --namespace-id "$KV_ID" --remote 2>&1)
if echo "$VERIFY" | grep -q "access_token"; then
  echo "Verified: token is stored correctly."
else
  echo "WARNING: Token verification failed. Output:"
  echo "$VERIFY"
  echo ""
  echo "Try storing manually:"
  echo "  echo \"\$TOKEN_JSON\" | npx wrangler kv key put \"tokens:${ATHLETE_ID}\" --namespace-id \"${KV_ID}\" --remote --path /dev/stdin"
  echo "  (the token JSON is in the TOKEN_JSON shell variable above; avoid pasting it into shared terminals)"
  exit 1
fi

echo ""
echo "=== Step 4: Set secrets ==="

echo "${STRAVA_CLIENT_ID}" | npx wrangler secret put STRAVA_CLIENT_ID
echo "${STRAVA_CLIENT_SECRET}" | npx wrangler secret put STRAVA_CLIENT_SECRET
echo "${VERIFY_TOKEN}" | npx wrangler secret put STRAVA_VERIFY_TOKEN
echo "${ATHLETE_ID}" | npx wrangler secret put STRAVA_ATHLETE_ID

# Random per-deployment secret embedded in the webhook callback path. Strava
# does not sign payloads, so this is what authenticates incoming events.
if command -v openssl >/dev/null 2>&1; then
  WEBHOOK_SECRET=$(openssl rand -hex 16)
else
  WEBHOOK_SECRET=$(head -c 16 /dev/urandom | xxd -p | tr -d '\n')
fi
echo "${WEBHOOK_SECRET}" | npx wrangler secret put WEBHOOK_SECRET

echo ""
echo "=== Step 5: Deploy worker ==="

# Read plan path + units from ~/.paicer/config (the same config the rest of
# paicer uses).
read_config() {
  local key="$1"
  local config="${PAICER_HOME:-$HOME/.paicer}/config"
  [[ -f "$config" ]] || return 0
  # paicer writes each entry as: key = "value"
  sed -n "s/^${key}[[:space:]]*=[[:space:]]*\"\(.*\)\"[[:space:]]*\$/\1/p" "$config" | head -1
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
DEPLOY_OUTPUT=$(npx wrangler deploy --var "UNITS:${UNITS}" 2>&1)
echo "$DEPLOY_OUTPUT"

# Detect the worker URL from the deploy output; fall back to a prompt.
WORKER_URL=$(echo "$DEPLOY_OUTPUT" | grep -oE 'https://[a-zA-Z0-9._-]+\.workers\.dev' | head -1)
if [[ -z "$WORKER_URL" ]]; then
  WORKER_NAME=$(grep '^name' wrangler.toml | head -1 | sed 's/.*= *"\(.*\)"/\1/')
  echo ""
  read -rp "Could not detect the worker URL. Enter your workers.dev subdomain (the part before .workers.dev): " WORKERS_SUBDOMAIN
  WORKER_URL="https://${WORKER_NAME}.${WORKERS_SUBDOMAIN}.workers.dev"
fi
CALLBACK_URL="${WORKER_URL}/webhook/${WEBHOOK_SECRET}"
echo "Worker URL: ${WORKER_URL}"
echo "Callback URL (keep private): ${CALLBACK_URL}"

echo ""
echo "=== Step 6: Create webhook subscription ==="

create_subscription() {
  curl -s -X POST "https://www.strava.com/api/v3/push_subscriptions" \
    -d "client_id=${STRAVA_CLIENT_ID}" \
    -d "client_secret=${STRAVA_CLIENT_SECRET}" \
    -d "callback_url=${CALLBACK_URL}" \
    -d "verify_token=${VERIFY_TOKEN}"
}

SUB_RESPONSE=$(create_subscription)

# Strava allows only one subscription per app. If one already exists it points
# at an old callback URL (and, now that we use a secret path, an old secret the
# redeployed worker no longer accepts). Replace it so the worker keeps working.
if ! echo "$SUB_RESPONSE" | grep -q '"id"' && echo "$SUB_RESPONSE" | grep -qi "already exists"; then
  echo "An existing subscription was found; replacing it with the new secret callback..."
  EXISTING=$(curl -s -G "https://www.strava.com/api/v3/push_subscriptions" \
    -d "client_id=${STRAVA_CLIENT_ID}" -d "client_secret=${STRAVA_CLIENT_SECRET}")
  OLD_IDS=$(echo "$EXISTING" | python3 -c "import sys,json; [print(s['id']) for s in json.load(sys.stdin)]" 2>/dev/null || true)
  for OLD_ID in $OLD_IDS; do
    echo "Deleting old subscription ${OLD_ID}..."
    curl -s -o /dev/null -X DELETE "https://www.strava.com/api/v3/push_subscriptions/${OLD_ID}?client_id=${STRAVA_CLIENT_ID}&client_secret=${STRAVA_CLIENT_SECRET}"
  done
  SUB_RESPONSE=$(create_subscription)
fi

if echo "$SUB_RESPONSE" | grep -q '"id"'; then
  SUB_ID=$(echo "$SUB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "Webhook subscription created: ${SUB_ID}"
else
  echo "ERROR: Could not create the webhook subscription:"
  echo "$SUB_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SUB_RESPONSE"
  echo ""
  echo "Delete any existing subscription, then re-run ./setup.sh:"
  echo "  curl -G https://www.strava.com/api/v3/push_subscriptions -d client_id=${STRAVA_CLIENT_ID} -d client_secret=${STRAVA_CLIENT_SECRET}"
  echo "  curl -X DELETE 'https://www.strava.com/api/v3/push_subscriptions/{id}?client_id=${STRAVA_CLIENT_ID}&client_secret=${STRAVA_CLIENT_SECRET}'"
  exit 1
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Your worker is live at: ${WORKER_URL}"
if [[ -n "${ATHLETE_ID:-}" ]]; then
  echo "Athlete ID: ${ATHLETE_ID}"
fi
echo ""
echo "Test it by completing a workout synced from Garmin!"
