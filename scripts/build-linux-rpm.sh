#!/usr/bin/env bash
set -euo pipefail

APP_NAME="SoundVault"
APP_NAME_LOWER="soundvault"
VERSION="${1:-$(cat "$(cd "$(dirname "$0")" && pwd)/../VERSION" 2>/dev/null || echo "1.0.3")}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="${PROJECT_DIR}/dist"
RPM_BUILD_DIR="/tmp/${APP_NAME}_rpm"
RPM_PATH="${DIST_DIR}/${APP_NAME_LOWER}-${VERSION}-1.x86_64.rpm"

echo "=== Building ${APP_NAME} .rpm ==="

if [[ ! -d "${DIST_DIR}/${APP_NAME}" ]]; then
    echo "WARNING: PyInstaller build not found at dist/${APP_NAME}/"
    echo "Running build-linux.sh first..."
    bash "${SCRIPT_DIR}/build-linux.sh" "$VERSION"
fi

echo "Preparing build root..."
BUILDROOT="${RPM_BUILD_DIR}/BUILDROOT/${APP_NAME_LOWER}-${VERSION}-1.x86_64"
mkdir -p "${BUILDROOT}/usr/share/${APP_NAME_LOWER}"
mkdir -p "${BUILDROOT}/usr/bin"
mkdir -p "${BUILDROOT}/usr/share/applications"
mkdir -p "${BUILDROOT}/usr/share/icons/hicolor/128x128/apps"

cp -r "${DIST_DIR}/${APP_NAME}/"* "${BUILDROOT}/usr/share/${APP_NAME_LOWER}/"

cat > "${BUILDROOT}/usr/bin/${APP_NAME_LOWER}" << 'SCRIPT'
#!/bin/sh
exec /usr/share/soundvault/SoundVault "$@"
SCRIPT
chmod +x "${BUILDROOT}/usr/bin/${APP_NAME_LOWER}"

DESKTOP_SRC="${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.desktop"
if [[ -f "$DESKTOP_SRC" ]]; then
    cp "$DESKTOP_SRC" "${BUILDROOT}/usr/share/applications/${APP_NAME_LOWER}.desktop"
fi

ICON_SRC="${PROJECT_DIR}/scripts/AppDir/${APP_NAME_LOWER}.png"
if [[ -f "$ICON_SRC" ]]; then
    cp "$ICON_SRC" "${BUILDROOT}/usr/share/icons/hicolor/128x128/apps/${APP_NAME_LOWER}.png"
fi

echo "Creating .spec file..."
mkdir -p "${RPM_BUILD_DIR}/SPECS"
SPEC_FILE="${RPM_BUILD_DIR}/SPECS/${APP_NAME_LOWER}.spec"
cat > "$SPEC_FILE" << EOF
Name: ${APP_NAME_LOWER}
Version: ${VERSION}
Release: 1
Summary: SoundVault Audio Tag Library Manager
License: MIT
URL: https://soundvault.app
Group: Applications/Multimedia
BuildArch: x86_64
AutoReqProv: no

%description
SoundVault is a desktop application for managing audio file tags,
organizing music libraries, and creating episode playlists.

%install
rm -rf %{buildroot}
cp -a "${BUILDROOT}"/* %{buildroot}

%files
/usr/share/${APP_NAME_LOWER}
/usr/bin/${APP_NAME_LOWER}
/usr/share/applications/${APP_NAME_LOWER}.desktop
/usr/share/icons/hicolor/128x128/apps/${APP_NAME_LOWER}.png

%changelog
* $(date '+%a %b %d %Y') SoundVault Team - ${VERSION}-1
- Initial RPM release
EOF

echo "Building .rpm package..."
rpmbuild -bb \
    --define "_topdir ${RPM_BUILD_DIR}" \
    --define "_rpmdir ${DIST_DIR}" \
    --define "_builddir ${RPM_BUILD_DIR}/BUILD" \
    --define "_sourcedir ${RPM_BUILD_DIR}" \
    --define "_specdir ${RPM_BUILD_DIR}/SPECS" \
    --define "_buildrootdir ${RPM_BUILD_DIR}/BUILDROOT" \
    "$SPEC_FILE"

rm -rf "$RPM_BUILD_DIR"

RPM_OUTPUT=$(ls "${DIST_DIR}/x86_64/"*.rpm 2>/dev/null || ls "${DIST_DIR}/"*.rpm 2>/dev/null || true)
RPM_FINAL=""
while IFS= read -r f; do
    case "$f" in
        *debug*|*debuginfo*) ;;
        *) RPM_FINAL="$f"; break ;;
    esac
done <<< "$RPM_OUTPUT"

if [[ -n "$RPM_FINAL" && "$RPM_FINAL" != "$RPM_PATH" ]]; then
    mv "$RPM_FINAL" "$RPM_PATH"
fi

echo ""
echo "=== Build complete ==="
echo "  .rpm: ${RPM_PATH}"
ls -lh "$RPM_PATH"
