#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
VERSION="${1:-1.0.2}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APPDIR="${SCRIPT_DIR}/AppDir"
DESKTOP_FILE="${APPDIR}/${APP_NAME}.desktop"
APPRUN="${APPDIR}/AppRun"

echo "=== Building ${APP_NAME} with PyInstaller ==="
cd "$PROJECT_DIR"
python -m PyInstaller SoundVault.spec --noconfirm

echo "=== Preparing AppDir structure ==="
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${APPDIR}/usr/share/${APP_NAME}"

cp -r "dist/${APP_NAME}/"* "${APPDIR}/usr/bin/"
cp "${DESKTOP_FILE}" "${APPDIR}/usr/share/applications/"
[ -f "${APPDIR}/soundvault.png" ] && \
  cp "${APPDIR}/soundvault.png" "${APPDIR}/usr/share/icons/hicolor/128x128/apps/"

cat > "${APPRUN}" << 'RUNEOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/SoundVault" "$@"
RUNEOF
chmod +x "${APPRUN}"

cp "${DESKTOP_FILE}" "${APPDIR}/"

if [ ! -f "${APPDIR}/soundvault.png" ]; then
  echo ""
  echo "WARNING: No icon found at ${APPDIR}/soundvault.png"
  echo "Please place a 128x128 PNG icon there for the AppImage."
  echo ""
fi

echo "=== Downloading appimagetool ==="
APPIMAGETOOL="${SCRIPT_DIR}/appimagetool"
if [ ! -f "${APPIMAGETOOL}" ]; then
  if command -v appimagetool &>/dev/null; then
    APPIMAGETOOL=$(command -v appimagetool)
  else
    ARCH=$(uname -m)
    if [ "${ARCH}" = "x86_64" ]; then
      APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    else
      APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    fi
    echo "Downloading appimagetool from ${APPIMAGETOOL_URL}..."
    curl -L -o "${APPIMAGETOOL}" "${APPIMAGETOOL_URL}"
    chmod +x "${APPIMAGETOOL}"
  fi
fi

echo "=== Building .AppImage ==="
OUTPUT="${PROJECT_DIR}/dist/${APP_NAME}-${VERSION}.AppImage"
ARCH=$(uname -m) "${APPIMAGETOOL}" "${APPDIR}" "${OUTPUT}"

echo ""
echo "=== Build complete ==="
echo "  .AppImage: ${OUTPUT}"
ls -lh "${OUTPUT}"
