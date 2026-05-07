#!/usr/bin/env bash
# Local laptop "deployment": venv + deps + StreamVault API (no AWS CLI, no EC2 userdata, no systemd).
# Run from anywhere: ./scripts/deploy-ec2-backend.sh [--reload] [--seed] [--background]
set -euo pipefail

RELOAD=0
SEED=0
BACKGROUND=0
for arg in "$@"; do
  case "$arg" in
    --reload) RELOAD=1 ;;
    --seed) SEED=1 ;;
    --background) BACKGROUND=1 ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: $0 [--reload] [--seed] [--background]" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required on PATH (install from python.org or brew install python)." >&2
  exit 1
fi

VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install -q --upgrade pip
python -m pip install -q -r "$ROOT/requirements-deploy.txt"

if [[ ! -f "$ROOT/.env" ]]; then
  if [[ -f "$ROOT/.env.example" ]]; then
    echo "No .env found; copying .env.example -> .env (edit for your machine)."
    cp "$ROOT/.env.example" "$ROOT/.env"
  else
    echo "Warning: no .env and no .env.example; API will use built-in defaults (mock SQLite)." >&2
  fi
fi

export PYTHONPATH="$ROOT"

if [[ "$SEED" -eq 1 ]]; then
  echo "Running seed_data.py ..."
  python "$ROOT/scripts/seed_data.py"
fi

UVICORN_CMD=(python -m uvicorn apps.backend.app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}")
if [[ "$RELOAD" -eq 1 ]]; then
  UVICORN_CMD+=(--reload)
fi

echo "Starting API from $ROOT"
echo "  Health: http://127.0.0.1:${API_PORT:-8000}/api/health"
echo "  Docs:   http://127.0.0.1:${API_PORT:-8000}/docs"
if [[ "$BACKGROUND" -eq 1 ]]; then
  LOG="${ROOT}/.uvicorn-local.log"
  PIDFILE="${ROOT}/.uvicorn-local.pid"
  nohup "${UVICORN_CMD[@]}" >>"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  echo "Background PID $(cat "$PIDFILE") (log: $LOG, stop: kill \$(cat $PIDFILE))"
else
  exec "${UVICORN_CMD[@]}"
fi
