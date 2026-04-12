#!/usr/bin/env bash
# Demo scenarios — calls admin API (backend must be running on :8000)
set -euo pipefail
BASE="${API_BASE:-http://127.0.0.1:8000/api}"

scenario() {
  echo "=== Scenario: $1 ==="
  curl -sS -X POST "$BASE/admin/scenario" -H "Content-Type: application/json" \
    -d "{\"scenario\":\"$1\"}" | jq .
  sleep 2
}

echo "Using API_BASE=$BASE"
scenario "cpu_spike"
scenario "request_surge"
scenario "network_degradation"
scenario "instance_unhealthy"
scenario "periodic_failure"
scenario "steady"

echo "=== Manual failover to DR ==="
curl -sS -X POST "$BASE/admin/failover/manual" -H "Content-Type: application/json" \
  -d '{"target":"dr","reason":"scripted demo"}' | jq .

echo "=== Run ML prediction + recovery evaluation ==="
curl -sS -X POST "$BASE/admin/prediction/run" | jq .

echo "Done."
