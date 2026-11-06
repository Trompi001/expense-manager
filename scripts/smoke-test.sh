#!/usr/bin/env bash
#
# Smoke-Test fuer den Expense Manager.
#
# Aufruf:
#   ./scripts/smoke-test.sh https://<APP_URL>
#
# Prueft die kritische Strecke gegen eine *laufende* Instanz:
#   1. /health   Liveness (mit Wartezeit, weil eine Render-Free-Instanz nach
#                15 Min. Ruhe schlaeft und beim ersten Aufruf bis zu 60 s braucht)
#   2. /ready    Readiness
#   3. POST      Ausgabe anlegen        (/api/expense)
#   4. GET       Ausgabe zuruecklesen   (/api/expense/<id>)
#   5. DELETE    Ausgabe wieder loeschen
#
# Endet mit Exit-Code != 0 beim ersten Fehler und gibt "SMOKE TEST PASSED" nur
# aus, wenn alle Pruefungen bestanden wurden.
#
# Abhaengigkeiten: bash, curl, grep (kein jq).

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <base-url>" >&2
  echo "example: $0 https://expense-manager-xxxx.onrender.com" >&2
  exit 2
fi

# Abschliessenden Schraegstrich entfernen.
BASE_URL="${1%/}"

# Wartebudget fuer /health (linearer Backoff: 5, 10, 15, ... Sekunden).
HEALTH_RETRIES="${HEALTH_RETRIES:-12}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-5}"

# Kein --fail: wir wollen Body und Status auch bei 4xx/5xx selbst auswerten.
CURL_OPTS=(--silent --show-error --connect-timeout 10 --max-time 60)

echo "Target: ${BASE_URL}"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

STATUS=""
BODY=""

# Zerlegt "<body>\n<status>" (curl -w '\n%{http_code}') in BODY und STATUS.
split_response() {
  local raw="$1"
  STATUS="${raw##*$'\n'}"
  BODY="${raw%$'\n'*}"
}

# --- 1/5 Liveness mit Cold-Start-Backoff --------------------------------------

echo "== 1/5 waiting for /health (tolerates a cold start) =="

attempt=1
healthy=0
while [ "$attempt" -le "$HEALTH_RETRIES" ]; do
  if raw="$(curl "${CURL_OPTS[@]}" -w $'\n%{http_code}' "${BASE_URL}/health" 2>/dev/null)"; then
    split_response "$raw"
    if [ "$STATUS" = "200" ] && printf '%s' "$BODY" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"'; then
      echo "  /health OK (attempt ${attempt}): ${BODY}"
      healthy=1
      break
    fi
  fi
  wait_for=$(( BACKOFF_SECONDS * attempt ))
  echo "  not ready yet (attempt ${attempt}/${HEALTH_RETRIES}); waiting ${wait_for}s..."
  sleep "$wait_for"
  attempt=$(( attempt + 1 ))
done

[ "$healthy" -eq 1 ] || fail "/health did not become healthy after ${HEALTH_RETRIES} attempts"

# --- 2/5 Readiness ------------------------------------------------------------

echo "== 2/5 checking /ready =="
raw="$(curl "${CURL_OPTS[@]}" -w $'\n%{http_code}' "${BASE_URL}/ready")" || fail "/ready request failed"
split_response "$raw"
[ "$STATUS" = "200" ] || fail "/ready returned HTTP ${STATUS} (expected 200); body: ${BODY}"
printf '%s' "$BODY" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ready"' || fail "/ready body missing status ready: ${BODY}"
echo "  /ready OK: ${BODY}"

# --- 3/5 Anlegen --------------------------------------------------------------

echo "== 3/5 creating an expense via POST /api/expense =="
description="smoke-test-${RANDOM}-$$"
raw="$(curl "${CURL_OPTS[@]}" \
  -H 'Content-Type: application/json' \
  -d "{\"description\":\"${description}\",\"amount\":1.5,\"category\":\"Sonstiges\",\"date\":\"2026-01-01\"}" \
  -w $'\n%{http_code}' \
  "${BASE_URL}/api/expense")" || fail "POST /api/expense request failed"
split_response "$raw"
[ "$STATUS" = "201" ] || fail "POST /api/expense returned HTTP ${STATUS} (expected 201); body: ${BODY}"
printf '%s' "$BODY" | grep -q "${description}" || fail "created expense is missing its description: ${BODY}"

# Numerische id nur mit grep aus dem JSON holen.
id="$(printf '%s' "$BODY" | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' | grep -m1 -oE '[0-9]+')"
[ -n "$id" ] || fail "could not parse an expense id from: ${BODY}"
echo "  created expense id=${id}"

# --- 4/5 Zuruecklesen ---------------------------------------------------------

echo "== 4/5 reading it back via GET /api/expense/${id} =="
raw="$(curl "${CURL_OPTS[@]}" -w $'\n%{http_code}' "${BASE_URL}/api/expense/${id}")" || fail "GET /api/expense/${id} request failed"
split_response "$raw"
[ "$STATUS" = "200" ] || fail "GET /api/expense/${id} returned HTTP ${STATUS} (expected 200); body: ${BODY}"
printf '%s' "$BODY" | grep -q "${description}" || fail "read-back expense is missing its description: ${BODY}"
echo "  read-back OK: ${BODY}"

# --- 5/5 Loeschen -------------------------------------------------------------

echo "== 5/5 deleting it via DELETE /api/expense/${id} =="
status="$(curl "${CURL_OPTS[@]}" -o /dev/null -w '%{http_code}' -X DELETE "${BASE_URL}/api/expense/${id}")" || fail "DELETE /api/expense/${id} request failed"
[ "$status" = "204" ] || fail "DELETE /api/expense/${id} returned HTTP ${status} (expected 204)"
echo "  deleted expense id=${id}"

echo
echo "SMOKE TEST PASSED"
