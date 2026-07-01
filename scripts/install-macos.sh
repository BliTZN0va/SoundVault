#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
APP_NAME_LOWER="soundvault"
VERSION="$(cat "$(cd "$(dirname "$0")" && pwd)/../VERSION" 2>/dev/null || echo "1.0.3")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/Applications/${APP_NAME}.app"
BIN_LINK="/usr/local/bin/${APP_NAME_LOWER}"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCH_AGENT_PLIST="${LAUNCH_AGENT_DIR}/com.${APP_NAME_LOWER}.app.plist"
ZSHRC="$HOME/.zshrc"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [[ "$(uname -s)" != "Darwin" ]]; then
    error "This installer is for macOS only (detected: $(uname -s))"
    exit 1
fi

if [[ "${1:-}" == "--uninstall" ]]; then
    echo ""; echo -e "${BOLD}=== Uninstalling ${APP_NAME} ===${NC}"; echo ""
    if [[ -d "$INSTALL_DIR" ]]; then info "Removing ${INSTALL_DIR}..."; rm -rf "$INSTALL_DIR"; ok "Removed ${INSTALL_DIR}"; else warn "${INSTALL_DIR} not found"; fi
    if [[ -f "$LAUNCH_AGENT_PLIST" ]]; then info "Unloading and removing LaunchAgent..."; launchctl unload "$LAUNCH_AGENT_PLIST" 2>/dev/null || true; rm -f "$LAUNCH_AGENT_PLIST"; ok "LaunchAgent removed"; fi
    if [[ -f "$BIN_LINK" ]]; then info "Removing symlink ${BIN_LINK}..."; rm -f "$BIN_LINK"; ok "Symlink removed"; fi
    if grep -q "alias ${APP_NAME_LOWER}=" "$ZSHRC" 2>/dev/null; then info "Removing alias from ${ZSHRC}..."; sed -i '' "/alias ${APP_NAME_LOWER}=/d" "$ZSHRC"; ok "Alias removed from ${ZSHRC}"; fi
    echo ""; echo -e "${GREEN}${BOLD}${APP_NAME} has been uninstalled.${NC}"; exit 0
fi

echo ""; echo -e "${BOLD}=== Installing ${APP_NAME} v${VERSION} ===${NC}"; echo ""

if [[ -d "$INSTALL_DIR" ]]; then
    warn "${APP_NAME} is already installed at ${INSTALL_DIR}"
    read -p "Overwrite? [y/N] " -n 1 -r; echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then info "Installation cancelled."; exit 0; fi
    rm -rf "$INSTALL_DIR"
fi

LOCAL_APP="${PROJECT_DIR}/dist/${APP_NAME}.app"
if [[ -d "$LOCAL_APP" ]]; then
    info "Copying local .app bundle..."
    cp -R "$LOCAL_APP" "$INSTALL_DIR"
    ok "Copied to ${INSTALL_DIR}"
else
    REPO="https://github.com/$(git config --get remote.origin.url 2>/dev/null | sed 's/.*:\(.*\)\.git/\1/' || echo "soundvault/soundvault")"
    DOWNLOAD_URL="${REPO}/releases/download/v${VERSION}/${APP_NAME}-${VERSION}.dmg"
    DMG_PATH="/tmp/${APP_NAME}-${VERSION}.dmg"
    MOUNT_POINT="/tmp/${APP_NAME}_mount"
    info "Downloading ${APP_NAME} v${VERSION} from GitHub..."
    info "  ${DOWNLOAD_URL}"
    curl -L --progress-bar -o "$DMG_PATH" "$DOWNLOAD_URL"
    ok "Download complete"
    info "Mounting disk image..."
    hdiutil attach "$DMG_PATH" -mountpoint "$MOUNT_POINT" -nobrowse -quiet
    ok "Mounted at ${MOUNT_POINT}"
    info "Installing to ${INSTALL_DIR}..."
    cp -R "${MOUNT_POINT}/${APP_NAME}.app" "$INSTALL_DIR"
    info "Ejecting disk image..."
    hdiutil detach "$MOUNT_POINT" -quiet
    rm -f "$DMG_PATH"
    ok "Installed to ${INSTALL_DIR}"
fi

if [[ ! -d "/usr/local/bin" ]]; then mkdir -p "/usr/local/bin"; fi
if [[ ! -f "$BIN_LINK" ]]; then
    ln -s "$INSTALL_DIR/Contents/MacOS/${APP_NAME}" "$BIN_LINK"
    ok "Created symlink: ${BIN_LINK}"
fi

ALIAS_LINE="alias ${APP_NAME_LOWER}='open \"${INSTALL_DIR}\"'"
if ! grep -q "alias ${APP_NAME_LOWER}=" "$ZSHRC" 2>/dev/null; then
    echo "" >> "$ZSHRC"
    echo "# ${APP_NAME} CLI" >> "$ZSHRC"
    echo "$ALIAS_LINE" >> "$ZSHRC"
    ok "Added alias to ${ZSHRC} (run 'source ${ZSHRC}' to activate)"
else
    warn "Alias already exists in ${ZSHRC}"
fi

echo ""; echo -e "${BOLD}Optional: Auto-start ${APP_NAME} on login?${NC}"
read -p "Create LaunchAgent? [y/N] " -n 1 -r; echo
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    mkdir -p "$LAUNCH_AGENT_DIR"
    cat > "$LAUNCH_AGENT_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.${APP_NAME_LOWER}.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/${APP_NAME}.app/Contents/MacOS/${APP_NAME}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
    launchctl load "$LAUNCH_AGENT_PLIST"
    ok "LaunchAgent created and loaded"
fi

echo ""; echo -e "${GREEN}${BOLD}=== Installation complete! ===${NC}"
echo "  ${APP_NAME} v${VERSION} installed to: ${INSTALL_DIR}"
echo "  Run: open /Applications/${APP_NAME}.app"
echo "  CLI: ${APP_NAME_LOWER}  (run 'source ~/.zshrc' first)"
