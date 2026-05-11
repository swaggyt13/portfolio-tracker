#!/usr/bin/env bash
# Launches IB Gateway via IBC. Idempotent: if Gateway is already up,
# this exits cleanly without touching anything.
#
# Why this script is more involved than you might expect:
#   1. IBC's gatewaystartmacos.sh hardcodes IBC_PATH=/opt/ibc, so even an
#      env var won't override it. We patch the file once on first run.
#   2. macOS ships Java 11 but Gateway 10.46+ needs Java 17. Gateway bundles
#      its own JRE; we must point IBC at that bundled JRE explicitly.

set -e

IBC_DIR="$HOME/ibc"
LOG_DIR="$IBC_DIR/logs"
mkdir -p "$LOG_DIR"

# Trading mode and matching port
TRADING_MODE="$(grep -i '^TradingMode' "$IBC_DIR/config.ini" 2>/dev/null | cut -d= -f2 | tr -d ' \r' | tr 'A-Z' 'a-z')"
PORT=4001
[ "$TRADING_MODE" = "paper" ] && PORT=4002

# Already up?
if nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
  echo "Gateway already listening on port $PORT."
  exit 0
fi

# Sanity checks
if [ ! -f "$IBC_DIR/config.ini" ]; then
  echo "IBC not installed. Run scripts/install_ibc.sh first."
  exit 1
fi
if grep -q '^IbPassword=$' "$IBC_DIR/config.ini"; then
  echo "IbPassword is empty in $IBC_DIR/config.ini. Set it and re-run."
  exit 1
fi

# Find Gateway install
GATEWAY_PATH=""
for root in /Applications "$HOME/Applications"; do
  for candidate in "$root"/"IB Gateway"*/; do
    [ -d "$candidate" ] && GATEWAY_PATH="${candidate%/}"
  done
done
if [ -z "$GATEWAY_PATH" ]; then
  found=$(mdfind -name "IB Gateway" 2>/dev/null | grep -E '/IB Gateway [0-9]+\.[0-9]+$' | head -n1)
  [ -n "$found" ] && GATEWAY_PATH="$found"
fi
if [ -z "$GATEWAY_PATH" ]; then
  echo "IB Gateway not found in /Applications or ~/Applications."
  exit 1
fi

TWS_PARENT=$(dirname "$GATEWAY_PATH")
TWS_MAJOR_VRSN=$(basename "$GATEWAY_PATH" | grep -oE '[0-9]+\.[0-9]+' | head -n1)
if [ -z "$TWS_MAJOR_VRSN" ]; then
  echo "Could not derive TWS major version from '$GATEWAY_PATH'."
  exit 1
fi

# Locate Gateway's bundled JRE. install4j puts it at one of these spots.
JAVA_HOME_PATH=""
for cand in \
    "$GATEWAY_PATH/.install4j/jre.bundle/Contents/Home" \
    "$GATEWAY_PATH/IB Gateway $TWS_MAJOR_VRSN.app/Contents/PlugIns/jre/Contents/Home" \
    "$GATEWAY_PATH/jre/Contents/Home" \
    "$GATEWAY_PATH/jre"; do
  if [ -x "$cand/bin/java" ]; then
    JAVA_HOME_PATH="$cand"
    break
  fi
done
if [ -z "$JAVA_HOME_PATH" ]; then
  found_java=$(find "$GATEWAY_PATH" -name java -type f 2>/dev/null | grep '/bin/java$' | head -n1)
  if [ -n "$found_java" ]; then
    JAVA_HOME_PATH=$(dirname "$(dirname "$found_java")")
  fi
fi
if [ -z "$JAVA_HOME_PATH" ]; then
  echo "Could not locate Gateway's bundled JRE inside $GATEWAY_PATH."
  echo "Files containing 'java' inside Gateway:"
  find "$GATEWAY_PATH" -maxdepth 6 -name "java" 2>/dev/null
  exit 1
fi
echo "Using bundled JRE at $JAVA_HOME_PATH"

# Patch IBC's gatewaystartmacos.sh so it uses our IBC location. One time.
SCRIPT="$IBC_DIR/gatewaystartmacos.sh"
if [ ! -x "$SCRIPT" ]; then
  echo "$SCRIPT not found. Re-run scripts/install_ibc.sh."
  exit 1
fi
if grep -q '^IBC_PATH=/opt/ibc' "$SCRIPT"; then
  cp "$SCRIPT" "$SCRIPT.bak"
  sed -i '' "s|^IBC_PATH=/opt/ibc|IBC_PATH=\$HOME/ibc|" "$SCRIPT"
  echo "Patched IBC_PATH in $SCRIPT"
fi
if grep -q "^TWS_PATH=\$HOME/Applications" "$SCRIPT"; then
  : # already correct
elif grep -q '^TWS_PATH=' "$SCRIPT"; then
  sed -i '' "s|^TWS_PATH=.*|TWS_PATH=\"$TWS_PARENT\"|" "$SCRIPT"
  echo "Patched TWS_PATH in $SCRIPT"
fi

# Env vars consumed by IBC. JAVA_PATH must be the bin folder, not JAVA_HOME.
export IBC_INI="$IBC_DIR/config.ini"
export IBC_PATH="$IBC_DIR"
export TWS_PATH="$TWS_PARENT"
export LOG_PATH="$LOG_DIR"
export JAVA_PATH="$JAVA_HOME_PATH/bin"
export JAVA_HOME="$JAVA_HOME_PATH"

echo "Launching Gateway $TWS_MAJOR_VRSN..."
nohup bash "$SCRIPT" "$TWS_MAJOR_VRSN" >> "$LOG_DIR/gateway.log" 2>&1 &

echo "Waiting for Gateway to accept API connections on port $PORT..."
for i in {1..120}; do
  if nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
    echo "Gateway is up."
    exit 0
  fi
  sleep 1
done

echo "Gateway did not come up within 120 seconds."
echo "Check $LOG_DIR/gateway.log for details."
echo "If a 2FA prompt appeared on your phone, approve it then re-run."
exit 1
