#!/usr/bin/env bash
# Double click to stop the Portfolio Tracker backend.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.portfolio_tracker_path" ]; then
  PROJECT_DIR="$(cat "$SCRIPT_DIR/.portfolio_tracker_path")"
else
  PROJECT_DIR="$SCRIPT_DIR"
fi
LOG_DIR="$PROJECT_DIR/.logs"

if [ -f "$LOG_DIR/backend.pid" ]; then
  PID=$(cat "$LOG_DIR/backend.pid")
  if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping backend (pid $PID)..."
    kill "$PID"
    sleep 1
    echo "Stopped."
  else
    echo "No running backend found."
  fi
  rm -f "$LOG_DIR/backend.pid"
else
  # Fallback: kill any uvicorn we started.
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  echo "Cleaned up."
fi

echo "Press any key to close..."
read -n 1 -s
