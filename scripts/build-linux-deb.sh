#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
APP_NAME_LOWER="soundvault"
VERSION="${1:-$(cat "$(cd "$(dirname "$0")" && pwd)/../VERSION" 2>/dev/null || echo "1.0.3")}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="${PROJECT_DIR}/dist"

DEB_DIR="/tmp/${APP_NAME}_deb"
DEB_PKG_DIR="${DEB_DIR}/${APP_NAME_LOWER}_${VERSION}_amd64"
DEB_PATH="${DIST_DIR}/${APP_NAME_LOWER}_${VERSION}_amd64.deb"

echo "=== Building ${APP_NAME} .deb ==="

echo "Step 1: Building AppImage (via build-linux.sh)..."
bash "${SCRIPT_DIR}/build-linux.sh" "$VERSION"

if [[ ! -d "${DIST_DIR}/${APP_NAME}" ]]; then
    echo "ERROR: PyInstaller build not found at dist/${APP_NAME}/"
    exit 1
fi

echo "Step 2: Preparing .deb package structure..."
rm -rf "$DEB_DIR"
mkdir -p "${DEB_PKG_DIR}/DEBIAN"
mkdir -p "${DEB_PKG_DIR}/usr/bin"
mkdir -p "${DEB_PKG_DIR}/usr/share/applications"
mkdir -p "${DEB_PKG_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${DEB_PKG_DIR}/usr/share/${APP_NAME_LOWER}"

cp -r "${DIST_DIR}/${APP_NAME}/"* "${DEB_PKG_DIR}/usr/share/${APP_NAME_LOWER}/"

cat > "${DEB_PKG_DIR}/usr/bin/${APP_NAME_LOWER}" << 'SCRIPT'
#!/bin/sh
exec /usr/share/soundvault/SoundVault "$@"
SCRIPT
chmod +x "${DEB_PKG_DIR}/usr/bin/${APP_NAME_LOWER}"

DESKTOP_SRC="${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.desktop"
if [[ -f "$DESKTOP_SRC" ]]; then
    cp "$DESKTOP_SRC" "${DEB_PKG_DIR}/usr/share/applications/${APP_NAME_LOWER}.desktop"
fi

ICON_SRC="${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.png"
if [[ -f "$ICON_SRC" ]]; then
    cp "$ICON_SRC" "${DEB_PKG_DIR}/usr/share/icons/hicolor/128x128/apps/${APP_NAME_LOWER}.png"
fi

cat > "${DEB_PKG_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME_LOWER}
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.17)
Recommends: python3 (>= 3.8)
Maintainer: SoundVault Team
Description: SoundVault Audio Tag Library Manager
 SoundVault is a desktop application for managing audio file tags,
 organizing music libraries, and creating episode playlists.
EOF

echo "Step 3: Building .deb package..."
fakeroot dpkg-deb --build "${DEB_PKG_DIR}" "${DEB_PATH}"

rm -rf "$DEB_DIR"

echo ""
echo "=== Build complete ==="
echo "  .deb: ${DEB_PATH}"
ls -lh "$DEB_PATH"
