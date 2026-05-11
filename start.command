#!/usr/bin/env bash
# Double click this file to launch the Portfolio Tracker.
# What it does:
#   1. Makes sure Postgres is running
#   2. If IB Gateway is not running, auto opens the Gateway window for you
#      and waits until you log in. Tick "Save settings" in Gateway once and
#      future launches pre-fill your password.
#   3. Builds the frontend the first time, or after code changes
#   4. Starts the backend in the background
#   5. Opens the dashboard in your default browser

set -e

# Project location:
#  1. If a sibling .portfolio_tracker_path file exists (created by
#     scripts/install_desktop_launcher.sh), use the path it stores.
#  2. Otherwise assume this script lives in the project root.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.portfolio_tracker_path" ]; then
  PROJECT_DIR="$(cat "$SCRIPT_DIR/.portfolio_tracker_path")"
else
  PROJECT_DIR="$SCRIPT_DIR"
fi

if [ ! -d "$PROJECT_DIR/backend" ] || [ ! -d "$PROJECT_DIR/frontend" ]; then
  echo "Could not find backend/ or frontend/ in $PROJECT_DIR"
  echo "Make sure start.command lives inside the project folder, or run"
  echo "scripts/install_desktop_launcher.sh once to install a Desktop alias."
  read -n 1 -s -p "Press any key to exit..."
  exit 1
fi

BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/.logs"
mkdir -p "$LOG_DIR"

echo "Portfolio Tracker"
echo "================="

# 1. Postgres
if ! brew services list | grep -q "postgresql.*started"; then
  echo "Starting Postgres..."
  brew services start postgresql@16 >/dev/null 2>&1 || true
  sleep 2
fi

# 2. IB Gateway. Determine port from your .env (default live = 4001).
PORT=4001
ENV_PORT=$(grep -E '^IBKR_PORT=' "$BACKEND_DIR/.env" 2>/dev/null | cut -d= -f2 | tr -d ' \r')
[ -n "$ENV_PORT" ] && PORT="$ENV_PORT"

if nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
  echo "IB Gateway already running on port $PORT."
else
  # Find Gateway app bundle
  GATEWAY_APP=""
  for root in "/Applications" "$HOME/Applications"; do
    for candidate in "$root"/"IB Gateway"*/"IB Gateway"*.app; do
      [ -d "$candidate" ] && GATEWAY_APP="$candidate"
    done
  done

  if [ -z "$GATEWAY_APP" ]; then
    echo "IB Gateway is not installed. Install it from interactivebrokers.com first."
    read -n 1 -s -p "Press any key to exit..."
    exit 1
  fi

  echo "Opening IB Gateway..."
  open "$GATEWAY_APP"

  # Friendly nudge in case password is not saved
  osascript -e 'display notification "Click Log In in the IB Gateway window. Tick Save settings if you want to skip the password next time." with title "Portfolio Tracker"' 2>/dev/null || true

  echo "Waiting for Gateway login (up to 5 minutes)..."
  echo "  Tip: tick \"Save settings\" in the Gateway login dialog so the password fills in next time."
  for i in {1..300}; do
    if nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
      echo "Gateway is up."
      break
    fi
    sleep 1
  done

  if ! nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
    echo "Gateway never came up. The dashboard will still load with cached data."
  fi
fi

# 3. Build frontend if dist is missing OR any source file is newer than the build
NEEDS_BUILD=0
if [ ! -d "$FRONTEND_DIR/dist" ]; then
  NEEDS_BUILD=1
else
  # Any .jsx, .js, .css, or config file newer than the built index.html?
  NEWEST=$(find "$FRONTEND_DIR/src" "$FRONTEND_DIR/index.html" "$FRONTEND_DIR/tailwind.config.js" "$FRONTEND_DIR/vite.config.js" \
    -newer "$FRONTEND_DIR/dist/index.html" 2>/dev/null | head -n1)
  [ -n "$NEWEST" ] && NEEDS_BUILD=1
fi
if [ "$NEEDS_BUILD" = "1" ]; then
  echo "Building dashboard..."
  cd "$FRONTEND_DIR"
  if [ ! -d node_modules ]; then
    npm install >>"$LOG_DIR/frontend_build.log" 2>&1
  fi
  npm run build >>"$LOG_DIR/frontend_build.log" 2>&1
fi

# 4. Stop any old backend
if [ -f "$LOG_DIR/backend.pid" ]; then
  OLD_PID=$(cat "$LOG_DIR/backend.pid")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Stopping old backend (pid $OLD_PID)..."
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
  fi
fi

# 5. Start backend
cd "$BACKEND_DIR"
if [ ! -d venv ]; then
  echo "Creating Python venv (one time)..."
  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip >>"$LOG_DIR/backend_install.log" 2>&1
  pip install -r requirements.txt >>"$LOG_DIR/backend_install.log" 2>&1
else
  source venv/bin/activate
fi

echo "Starting backend..."
nohup uvicorn app.main:app --loop asyncio --host 127.0.0.1 --port 8000 \
  >>"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$LOG_DIR/backend.pid"

# 6. Wait for API and open browser
echo "Waiting for API..."
for i in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Opening dashboard..."
open "http://127.0.0.1:8000"

echo ""
echo "Backend pid: $BACKEND_PID"
echo "Logs: $LOG_DIR/backend.log"
echo ""
echo "This window can be closed. The backend keeps running in the background."
echo "Press any key to close..."
read -n 1 -s
