#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
VERSION="${1:-$(cat "$(cd "$(dirname "$0")" && pwd)/../VERSION" 2>/dev/null || echo "1.0.3")}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_BUNDLE="${PROJECT_DIR}/dist/${APP_NAME}.app"
PKG_DIR="/tmp/${APP_NAME}_pkg"
PKG_PATH="${PROJECT_DIR}/dist/${APP_NAME}-${VERSION}.pkg"

echo "=== Building ${APP_NAME} .pkg ==="

if [[ ! -d "$APP_BUNDLE" ]]; then
    echo "ERROR: .app bundle not found at $APP_BUNDLE"
    echo "Run build-macos.sh first."
    exit 1
fi

rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

echo "Creating component package..."
COMPONENT_PKG="${PKG_DIR}/${APP_NAME}.pkg"
pkgbuild --root "$APP_BUNDLE" \
    --identifier "com.soundvault.app" \
    --version "$VERSION" \
    --install-location "/Applications/${APP_NAME}.app" \
    "$COMPONENT_PKG"

echo "Creating distribution definition..."
DIST_FILE="${PKG_DIR}/Distribution.xml"
cat > "$DIST_FILE" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>${APP_NAME}</title>
    <organization>com.soundvault</organization>
    <product id="com.soundvault.app" version="${VERSION}" />
    <pkg-ref id="com.soundvault.app">${APP_NAME}.pkg</pkg-ref>
    <options customize="never" require-scripts="false" hostArchitectures="x86_64,arm64"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.soundvault.app"/>
        </line>
    </choices-outline>
    <choice id="default" title="${APP_NAME}" description="SoundVault Audio Library Manager">
        <pkg-ref id="com.soundvault.app"/>
    </choice>
    <pkg-ref id="com.soundvault.app" onConclusion="none">${APP_NAME}.pkg</pkg-ref>
</installer-gui-script>
EOF

echo "Building final .pkg..."
productbuild --distribution "$DIST_FILE" \
    --package-path "$PKG_DIR" \
    --version "$VERSION" \
    "$PKG_PATH"

if security find-identity -v -p codesigning &>/dev/null 2>&1; then
    CODESIGN_IDENTITY=$(security find-identity -v -p codesigning | head -1 | grep -o '"[^"]*"' | tr -d '"' || true)
    if [[ -n "$CODESIGN_IDENTITY" ]]; then
        echo "Signing .pkg with identity: $CODESIGN_IDENTITY"
        productsign --sign "$CODESIGN_IDENTITY" "$PKG_PATH" "${PKG_PATH}.signed"
        mv "${PKG_PATH}.signed" "$PKG_PATH"
    fi
fi

rm -rf "$PKG_DIR"

echo ""
echo "=== Build complete ==="
echo "  .pkg: ${PKG_PATH}"
ls -lh "$PKG_PATH"
