#!/usr/bin/env bash
# Start the Nando web app (API + React UI).
#
# Usage:
#   ./run.sh          Dev mode: API on :8000, UI on :5173 (hot reload)
#   ./run.sh --prod   Build UI once, serve everything on :8000

set -euo pipefail

PORT=80

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PROD=false
if [[ "${1:-}" == "--prod" || "${1:-}" == "prod" ]]; then
  PROD=true
fi

# --- Python venv ---
if [[ ! -d .venv ]]; then
  echo "Creating Python virtual environment…"
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Installing Python dependencies…"
pip install -q -r requirements.txt

# --- Node (frontend) ---
if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm is required. Install Node.js 18+ from https://nodejs.org/" >&2
  exit 1
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "Installing frontend dependencies…"
  npm install --prefix frontend
fi

cleanup() {
  [[ -n "${UVICORN_PID:-}" ]] && kill "$UVICORN_PID" 2>/dev/null || true
  [[ -n "${VITE_PID:-}" ]] && kill "$VITE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if $PROD; then
  echo "Building frontend…"
  npm run build --prefix frontend
  echo ""
  echo "Nando is running at http://127.0.0.1:${PORT}"
  echo "Press Ctrl+C to stop."
  exec uvicorn app:app --host 127.0.0.1 --port ${PORT}
else
  echo "Starting API on http://127.0.0.1:${PORT} …"
  uvicorn app:app --reload --host 127.0.0.1 --port ${PORT}
  UVICORN_PID=$!

  echo "Starting frontend on http://127.0.0.1:5173 …"
  npm run dev --prefix frontend &
  VITE_PID=$!

  echo ""
  echo "Nando is ready:"
  echo "  Open http://127.0.0.1:5173 in your browser"
  echo "  API: http://127.0.0.1:${PORT}"
  echo ""
  echo "Press Ctrl+C to stop both servers."

  wait
fi
