#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP" 2>/dev/null || true
}
trap cleanup EXIT

if ! command -v node >/dev/null 2>&1; then
  echo "E2E: FAIL node is not installed"
  exit 1
fi

if [ ! -d "$ROOT/node_modules/playwright" ]; then
  echo "E2E: FAIL dependencies are not installed (run: npm install)"
  exit 1
fi

PORT="$(python3 - <<'PY'
import socket
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
print(sock.getsockname()[1])
sock.close()
PY
)"

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT" >"$TMP/server.log" 2>&1 &
SERVER_PID=$!

ready=0
for _ in $(seq 1 100); do
  if curl -sf "http://127.0.0.1:$PORT/index.html" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.05
done

if [ "$ready" -ne 1 ]; then
  echo "E2E: FAIL local server did not start"
  cat "$TMP/server.log"
  exit 1
fi

node "$ROOT/tests/e2e.mjs" "http://127.0.0.1:$PORT"
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ] && [ -s "$TMP/server.log" ]; then
  echo "--- server log (tail) ---"
  tail -10 "$TMP/server.log"
fi

exit "$EXIT_CODE"
