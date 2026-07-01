#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
APP_NAME_LOWER="soundvault"
VERSION="$(cat "$(cd "$(dirname "$0")" && pwd)/../VERSION" 2>/dev/null || echo "1.0.3")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
BIN_PATH="${BIN_DIR}/${APP_NAME_LOWER}"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/${APP_NAME_LOWER}.desktop"
ICON_DIR="${HOME}/.local/share/icons/hicolor/128x128/apps"
ICON_PATH="${ICON_DIR}/${APP_NAME_LOWER}.png"
BASHRC="${HOME}/.bashrc"
ZSHRC="${HOME}/.zshrc"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [[ "$(uname -s)" != "Linux" ]]; then
    error "This installer is for Linux only (detected: $(uname -s))"
    exit 1
fi

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release; DISTRO_ID="${ID,,}"; DISTRO_LIKE="${ID_LIKE,,}"
    elif [[ -f /etc/debian_version ]]; then DISTRO_ID="debian"
    elif [[ -f /etc/redhat-release ]]; then DISTRO_ID="fedora"
    elif command -v pacman &>/dev/null; then DISTRO_ID="arch"
    else DISTRO_ID="unknown"; fi
}
detect_distro
info "Detected distro: ${DISTRO_ID}${DISTRO_LIKE:+ (like: ${DISTRO_LIKE})}"

if [[ "${1:-}" == "--uninstall" ]]; then
    echo ""; echo -e "${BOLD}=== Uninstalling ${APP_NAME} ===${NC}"; echo ""
    if command -v dpkg &>/dev/null && dpkg -l "${APP_NAME_LOWER}" &>/dev/null 2>&1; then info "Removing .deb package..."; sudo dpkg -r "${APP_NAME_LOWER}" || sudo apt-get remove -y "${APP_NAME_LOWER}" || true; ok "Package removed via dpkg"; fi
    if command -v rpm &>/dev/null && rpm -q "${APP_NAME_LOWER}" &>/dev/null 2>&1; then info "Removing .rpm package..."; sudo rpm -e "${APP_NAME_LOWER}" || sudo dnf remove -y "${APP_NAME_LOWER}" || true; ok "Package removed via rpm"; fi
    if [[ -d "$INSTALL_DIR" ]]; then info "Removing ${INSTALL_DIR}..."; rm -rf "$INSTALL_DIR"; ok "Removed ${INSTALL_DIR}"; fi
    if [[ -f "$BIN_PATH" ]]; then rm -f "$BIN_PATH"; ok "Removed ${BIN_PATH}"; fi
    if [[ -f "$DESKTOP_FILE" ]]; then rm -f "$DESKTOP_FILE"; ok "Removed desktop file"; fi
    if [[ -f "$ICON_PATH" ]]; then rm -f "$ICON_PATH"; ok "Removed icon"; fi
    for RC in "$BASHRC" "$ZSHRC"; do
        if [[ -f "$RC" ]] && grep -q "alias ${APP_NAME_LOWER}=" "$RC" 2>/dev/null; then sed -i "/alias ${APP_NAME_LOWER}=/d" "$RC"; ok "Removed alias from ${RC}"; fi
    done
    echo ""; echo -e "${GREEN}${BOLD}${APP_NAME} has been uninstalled.${NC}"; exit 0
fi

echo ""; echo -e "${BOLD}=== Installing ${APP_NAME} v${VERSION} ===${NC}"; echo ""

DEB_FILE=$(ls "${PROJECT_DIR}/dist/"${APP_NAME_LOWER}_*.deb 2>/dev/null | head -1 || true)
RPM_FILE=$(ls "${PROJECT_DIR}/dist/"${APP_NAME_LOWER}-*.rpm 2>/dev/null | head -1 || true)
APPIMAGE_FILE=$(ls "${PROJECT_DIR}/dist/"${APP_NAME_LOWER}-*.AppImage 2>/dev/null || ls "${PROJECT_DIR}/dist/"${APP_NAME}-*.AppImage 2>/dev/null | head -1 || true)

INSTALLED=false

if [[ -n "$DEB_FILE" ]] && (echo "${DISTRO_ID} ${DISTRO_LIKE}" | grep -qiE "debian|ubuntu"); then
    info "Found .deb package: $(basename "$DEB_FILE")"
    if command -v dpkg &>/dev/null; then
        sudo dpkg -i "$DEB_FILE" || true
        sudo apt-get install -f -y || true
        ok "Installed via dpkg"; INSTALLED=true
    fi
fi

if [[ "$INSTALLED" == false && -n "$RPM_FILE" ]] && (echo "${DISTRO_ID} ${DISTRO_LIKE}" | grep -qiE "fedora|rhel|centos|rocky|alma|opensuse"); then
    info "Found .rpm package: $(basename "$RPM_FILE")"
    if command -v dnf &>/dev/null; then sudo dnf install -y "$RPM_FILE" && INSTALLED=true
    elif command -v yum &>/dev/null; then sudo yum install -y "$RPM_FILE" && INSTALLED=true
    elif command -v zypper &>/dev/null; then sudo zypper install -y "$RPM_FILE" && INSTALLED=true
    elif command -v rpm &>/dev/null; then sudo rpm -i "$RPM_FILE" && INSTALLED=true; fi
    if [[ "$INSTALLED" == true ]]; then ok "Installed via rpm"; fi
fi

if [[ "$INSTALLED" == false && -n "$APPIMAGE_FILE" ]]; then
    info "Found AppImage: $(basename "$APPIMAGE_FILE")"
    mkdir -p "$INSTALL_DIR" "$BIN_DIR"
    cp "$APPIMAGE_FILE" "${INSTALL_DIR}/"
    chmod +x "${INSTALL_DIR}/$(basename "$APPIMAGE_FILE")"
    ln -sf "${INSTALL_DIR}/$(basename "$APPIMAGE_FILE")" "$BIN_PATH"
    ok "AppImage installed to ${INSTALL_DIR}"; INSTALLED=true
fi

if [[ "$INSTALLED" == false && -d "${PROJECT_DIR}/dist/${APP_NAME}" ]]; then
    info "Installing from local build (dist/${APP_NAME}/)..."
    mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
    cp -r "${PROJECT_DIR}/dist/${APP_NAME}/"* "$INSTALL_DIR/"
    cat > "$BIN_PATH" << 'SCRIPT'
#!/bin/sh
exec "${HOME}/.local/share/SoundVault/SoundVault" "$@"
SCRIPT
    chmod +x "$BIN_PATH"
    if [[ -f "${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.desktop" ]]; then
        sed "s|Exec=SoundVault|Exec=${BIN_PATH}|" \
            "${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.desktop" > "$DESKTOP_FILE"
        ok "Created desktop file"
    fi
    if [[ -f "${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.png" ]]; then
        cp "${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.png" "$ICON_PATH"
        ok "Installed icon"
    fi
    ok "Installed to ${INSTALL_DIR}"; INSTALLED=true
fi

if [[ "$INSTALLED" == false ]]; then
    error "No build found. Please run scripts/build-linux.sh first or download a release."
    exit 1
fi

ALIAS_LINE="alias ${APP_NAME_LOWER}='${BIN_PATH}'"
for RC in "$BASHRC" "$ZSHRC"; do
    if [[ -f "$RC" ]]; then
        if ! grep -q "alias ${APP_NAME_LOWER}=" "$RC" 2>/dev/null; then
            echo "" >> "$RC"; echo "# ${APP_NAME} CLI" >> "$RC"; echo "$ALIAS_LINE" >> "$RC"
            ok "Added alias to ${RC}"
        fi
    fi
done
if [[ ! -f "$BASHRC" && ! -f "$ZSHRC" ]]; then
    echo "$ALIAS_LINE" > "$BASHRC"; ok "Created ${BASHRC} with alias"
fi

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    warn "${BIN_DIR} is not in your PATH. Add 'export PATH=\"\$PATH:${BIN_DIR}\"' to your shell rc file."
fi

echo ""; echo -e "${GREEN}${BOLD}=== Installation complete! ===${NC}"
echo "  ${APP_NAME} v${VERSION} installed"
echo "  Binary: ${BIN_PATH}"
echo "  Run:    ${APP_NAME_LOWER}"
