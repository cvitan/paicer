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
  KV_OUTPUT=$(npx wrangler kv namespace create STRAVA_TOKENS 2>&1)
  KV_ID=$(echo "$KV_OUTPUT" | grep -o '"[a-f0-9]\{32\}"' | tr -d '"')

  if [[ -z "$KV_ID" ]]; then
    echo "Namespace may already exist, looking it up..."
    KV_LIST=$(npx wrangler kv namespace list 2>&1)
    KV_ID=$(echo "$KV_LIST" | python3 -c "
import sys, json
for ns in json.load(sys.stdin):
    if 'STRAVA_TOKENS' in ns.get('title', ''):
        print(ns['id'])
        break
" 2>/dev/null || true)
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

TOKEN_JSON=$(python3 -c "
import json
print(json.dumps({
    'access_token': '${ACCESS_TOKEN}',
    'refresh_token': '${REFRESH_TOKEN}',
    'expires_at': ${EXPIRES_AT}
}))
")

npx wrangler kv key put "tokens:${ATHLETE_ID}" "$TOKEN_JSON" --namespace-id "$KV_ID"
echo "Tokens stored in KV as tokens:${ATHLETE_ID}"

# Verify the token was actually stored
echo "Verifying token storage..."
VERIFY=$(npx wrangler kv key get "tokens:${ATHLETE_ID}" --namespace-id "$KV_ID" 2>&1)
if echo "$VERIFY" | grep -q "access_token"; then
  echo "Verified: token is stored correctly."
else
  echo "WARNING: Token verification failed. Output:"
  echo "$VERIFY"
  echo ""
  echo "Try storing manually:"
  echo "  npx wrangler kv key put \"tokens:${ATHLETE_ID}\" '${TOKEN_JSON}' --namespace-id \"${KV_ID}\""
  exit 1
fi

echo ""
echo "=== Step 4: Set secrets ==="

echo "${STRAVA_CLIENT_ID}" | npx wrangler secret put STRAVA_CLIENT_ID
echo "${STRAVA_CLIENT_SECRET}" | npx wrangler secret put STRAVA_CLIENT_SECRET
echo "${VERIFY_TOKEN}" | npx wrangler secret put STRAVA_VERIFY_TOKEN

echo ""
echo "=== Step 5: Deploy worker ==="

# Copy plan YAML from repo root
if [[ -f ../.env ]]; then
  # shellcheck source=/dev/null
  PLAN_PATH=$(grep '^PLAN=' ../.env | cut -d= -f2)
fi
PLAN_PATH="../${PLAN_PATH:-}"

if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
  echo "Error: No training plan found."
  echo "Set PLAN=plans/your-plan.yaml in the repo root .env file."
  exit 1
fi

echo "Copying plan: $PLAN_PATH -> plan.yaml"
cp "$PLAN_PATH" plan.yaml

echo "Running: npx wrangler deploy"
npx wrangler deploy

WORKER_NAME=$(grep '^name' wrangler.toml | head -1 | sed 's/.*= *"\(.*\)"/\1/')
echo ""
read -rp "Enter your workers.dev subdomain (the part before .workers.dev): " WORKERS_SUBDOMAIN
WORKER_URL="https://${WORKER_NAME}.${WORKERS_SUBDOMAIN}.workers.dev"
CALLBACK_URL="${WORKER_URL}/webhook"
echo "Worker URL: ${WORKER_URL}"

echo ""
echo "=== Step 6: Create webhook subscription ==="

SUB_RESPONSE=$(curl -s -X POST "https://www.strava.com/api/v3/push_subscriptions" \
  -d "client_id=${STRAVA_CLIENT_ID}" \
  -d "client_secret=${STRAVA_CLIENT_SECRET}" \
  -d "callback_url=${CALLBACK_URL}" \
  -d "verify_token=${VERIFY_TOKEN}")

if echo "$SUB_RESPONSE" | grep -q '"id"'; then
  SUB_ID=$(echo "$SUB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "Webhook subscription created: ${SUB_ID}"
else
  echo "Webhook subscription response:"
  echo "$SUB_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SUB_RESPONSE"
  echo ""
  echo "If you see 'callback url already registered', you already have a subscription."
  echo "To delete it: curl -X DELETE 'https://www.strava.com/api/v3/push_subscriptions/{id}?client_id=${STRAVA_CLIENT_ID}&client_secret=${STRAVA_CLIENT_SECRET}'"
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
