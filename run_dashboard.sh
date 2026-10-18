#!/usr/bin/env bash
# Chạy dashboard M22 (FastAPI + React) khi phát triển: API ở cổng 8000, giao diện ở http://localhost:5173.
# Dùng: ./run_dashboard.sh          (Ctrl+C dừng cả hai)
#       API_PORT=8010 ./run_dashboard.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
API_PORT="${API_PORT:-8000}"

cd "$ROOT/dashboard"
"$PY" -m uvicorn api.main:app --reload --port "$API_PORT" &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

cd web
[ -d node_modules ] || npm install
M22_API_URL="http://127.0.0.1:$API_PORT" npm run dev
