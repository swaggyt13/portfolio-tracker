#!/usr/bin/env bash
# Drops start.command and stop.command on your Desktop pointing at this
# project. Idempotent: re-run any time you move the project folder.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP="$HOME/Desktop"

if [ ! -d "$DESKTOP" ]; then
  echo "Desktop folder not found at $DESKTOP"
  exit 1
fi

cp "$PROJECT_DIR/start.command" "$DESKTOP/Portfolio Tracker.command"
cp "$PROJECT_DIR/stop.command" "$DESKTOP/Portfolio Tracker (stop).command"
echo -n "$PROJECT_DIR" > "$DESKTOP/.portfolio_tracker_path"

chmod +x "$DESKTOP/Portfolio Tracker.command" "$DESKTOP/Portfolio Tracker (stop).command"

echo "Installed:"
echo "  $DESKTOP/Portfolio Tracker.command"
echo "  $DESKTOP/Portfolio Tracker (stop).command"
echo ""
echo "Double click 'Portfolio Tracker.command' on your Desktop to launch."
