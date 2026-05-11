#!/usr/bin/env bash
# One time IBC installer for macOS.
# Downloads IBC, lays out ~/ibc/, and writes a config.ini you fill in once.
# Run this once: bash scripts/install_ibc.sh

set -e

IBC_DIR="$HOME/ibc"
LOG_DIR="$HOME/ibc/logs"
# Optional. If not set, config.ini is written with an empty IbLoginId and
# you fill it in once before launching Gateway via IBC.
USERNAME_DEFAULT="${IBKR_USERNAME:-}"

# Ask the GitHub API for the latest IBC macOS asset URL. This avoids
# hardcoding a version that may not exist. Falls back to a known good
# URL if the API call fails.
echo "Looking up latest IBC release..."
RELEASE_JSON=$(curl -fsSL https://api.github.com/repos/IbcAlpha/IBC/releases/latest)

# Match any macOS asset, regardless of naming style (IBCMacos, IBC-Macos, etc).
IBC_URL=$(printf '%s\n' "$RELEASE_JSON" \
  | grep -Eo '"browser_download_url"[[:space:]]*:[[:space:]]*"[^"]+"' \
  | grep -iE 'mac' \
  | head -n1 \
  | sed -E 's/.*"(https[^"]+)".*/\1/')

if [ -z "$IBC_URL" ]; then
  # No macOS specific asset; some IBC releases ship a single cross platform zip.
  IBC_URL=$(printf '%s\n' "$RELEASE_JSON" \
    | grep -Eo '"browser_download_url"[[:space:]]*:[[:space:]]*"[^"]+\.zip"' \
    | head -n1 \
    | sed -E 's/.*"(https[^"]+)".*/\1/')
fi

if [ -z "$IBC_URL" ]; then
  echo "Could not find an IBC release asset via the GitHub API."
  echo "Open https://github.com/IbcAlpha/IBC/releases/latest in a browser, download the macOS zip,"
  echo "and unzip it into $IBC_DIR yourself, then re-run this script."
  exit 1
fi
echo "Using $IBC_URL"

echo "IBC Installer"
echo "============="

# 1. Find IB Gateway install path. IBKR may put it in /Applications (system)
# or ~/Applications (user). We check both.
GATEWAY_PATH=""
for root in /Applications "$HOME/Applications"; do
  for candidate in "$root"/"IB Gateway"*/; do
    if [ -d "$candidate" ]; then
      GATEWAY_PATH="$candidate"
    fi
  done
done

# Fallback: ask Spotlight
if [ -z "$GATEWAY_PATH" ]; then
  found=$(mdfind -name "IB Gateway" 2>/dev/null | grep -E '/IB Gateway [0-9]+\.[0-9]+$' | head -n1)
  if [ -n "$found" ]; then
    GATEWAY_PATH="$found"
  fi
fi

if [ -z "$GATEWAY_PATH" ]; then
  echo "Could not find IB Gateway under /Applications or ~/Applications. Install Gateway first, then re-run."
  exit 1
fi

GATEWAY_PATH="${GATEWAY_PATH%/}"
echo "Found Gateway: $GATEWAY_PATH"

# 2. Make ~/ibc and download IBC if not present
mkdir -p "$IBC_DIR" "$LOG_DIR"
if [ ! -f "$IBC_DIR/IBController.jar" ] && [ ! -f "$IBC_DIR/IBC.jar" ]; then
  echo "Downloading IBC ${IBC_VERSION}..."
  TMP_ZIP="$(mktemp).zip"
  curl -fL "$IBC_URL" -o "$TMP_ZIP"
  unzip -o "$TMP_ZIP" -d "$IBC_DIR" >/dev/null
  rm -f "$TMP_ZIP"
  chmod +x "$IBC_DIR"/*.sh 2>/dev/null || true
  echo "IBC unpacked into $IBC_DIR"
else
  echo "IBC already installed in $IBC_DIR"
fi

# 3. Detect Gateway Jts directory (used in IBC config)
JTS_DIR="$GATEWAY_PATH/Jts"
if [ ! -d "$JTS_DIR" ]; then
  # Newer Gateway packs it differently
  JTS_DIR="$GATEWAY_PATH"
fi

# 4. Write config.ini if it doesn't exist or is the unmodified IBC default.
# The IBC zip ships its own config.ini, which we want to replace with one
# tailored to this project (read only API, our username, etc).
CONFIG_FILE="$IBC_DIR/config.ini"
if [ -f "$CONFIG_FILE" ] && ! grep -q "IbLoginId=${USERNAME_DEFAULT}" "$CONFIG_FILE"; then
  echo "Backing up IBC default config to ${CONFIG_FILE}.ibc-default"
  mv "$CONFIG_FILE" "${CONFIG_FILE}.ibc-default"
fi
if [ ! -f "$CONFIG_FILE" ]; then
  cat > "$CONFIG_FILE" <<EOF
# IBC config for IB Gateway, read only API mode.
# Fill in IbPassword below and save. Plaintext is required by IBC.
# Your Mac disk should be encrypted (FileVault) and the file is chmod 600.

# Credentials
IbLoginId=${USERNAME_DEFAULT}
IbPassword=

# Live (4001) or paper (4002). You're on live based on your .env.
TradingMode=live

# Read only API. The Python tracker only reads positions, never trades.
ReadOnlyApi=yes
ReadOnlyLogin=no

# Auto answer dialogs that would otherwise stall the login
AcceptIncomingConnectionAction=accept
AllowBlindTrading=no
DismissPasswordExpiryWarning=yes
DismissNSEComplianceNotice=yes
SuppressInfoMessages=yes

# Behaviour around the daily restart and 2FA
ExistingSessionDetectedAction=primary
ReloginAfterSecondFactorAuthenticationTimeout=yes
SecondFactorAuthenticationExitInterval=

# Where Gateway is installed
IbDir=${JTS_DIR}

# Auto restart Gateway daily so the session stays fresh
AutoRestartTime=11:50 PM
ClosedownAt=
EOF
  chmod 600 "$CONFIG_FILE"
  echo "Wrote $CONFIG_FILE (chmod 600). Edit it and set IbPassword."
else
  echo "config.ini already exists at $CONFIG_FILE; left untouched."
fi

echo ""
echo "Next:"
echo "  1. Open $CONFIG_FILE and set IbPassword=<your IBKR password>"
echo "  2. Save the file"
echo "  3. Run scripts/launch_gateway.sh once to verify, or just double click start.command"
