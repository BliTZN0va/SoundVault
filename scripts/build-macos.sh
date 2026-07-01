#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
VERSION="${1:-1.0.2}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"

echo "=== Building ${APP_NAME} .app bundle ==="
cd "$PROJECT_DIR"

python -m PyInstaller SoundVault.spec --noconfirm

APP_BUNDLE="dist/${APP_NAME}.app"
if [ ! -d "$APP_BUNDLE" ]; then
  echo "ERROR: .app bundle not found at $APP_BUNDLE"
  exit 1
fi

echo "=== Codesigning .app (if certificate available) ==="
if security find-identity -v -p codesigning &>/dev/null 2>&1; then
  CODESIGN_IDENTITY=$(security find-identity -v -p codesigning | head -1 | grep -o '"[^"]*"' | tr -d '"' || true)
  if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Signing with identity: $CODESIGN_IDENTITY"
    codesign --deep --force --verify --verbose --sign "$CODESIGN_IDENTITY" "$APP_BUNDLE"
  else
    echo "No signing identity found, skipping codesign"
  fi
else
  echo "No codesigning identities available, skipping codesign"
fi

echo "=== Creating .dmg ==="
DMG_DIR="dist"
DMG_PATH="${DMG_DIR}/${DMG_NAME}"

if command -v create-dmg &>/dev/null; then
  echo "Using create-dmg..."
  create-dmg \
    --volname "${APP_NAME}" \
    --volicon "${PROJECT_DIR}/icon.ico" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 150 200 \
    --app-drop-link 450 200 \
    "${DMG_PATH}" \
    "${APP_BUNDLE}" || true
else
  echo "create-dmg not found, using hdiutil..."
  STAGING_DIR="${DMG_DIR}/dmg-staging"
  mkdir -p "${STAGING_DIR}"
  cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"
  ln -s /Applications "${STAGING_DIR}/Applications"

  hdiutil create -volname "${APP_NAME}" -srcfolder "${STAGING_DIR}" \
    -ov -format UDZO -size 512m "${DMG_PATH}"
  rm -rf "${STAGING_DIR}"
fi

echo "=== Signing .dmg ==="
if [ -n "${CODESIGN_IDENTITY:-}" ]; then
  codesign --verify --verbose --sign "$CODESIGN_IDENTITY" "${DMG_PATH}" || true
fi

echo ""
echo "=== Build complete ==="
echo "  .app:  ${APP_BUNDLE}"
echo "  .dmg:  ${DMG_PATH}"
echo "  dist/ contents:"
ls -lh "${DMG_DIR}"
