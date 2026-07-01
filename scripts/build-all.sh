#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

VERSION="${1:-}"
ARGS=()
if [[ -n "$VERSION" ]]; then
    ARGS+=("$VERSION")
fi

case "$(uname -s)" in
  Darwin)
    echo "Detected macOS"
    echo ""
    echo ">>> Step 1: Build .app and .dmg"
    bash "${SCRIPT_DIR}/build-macos.sh" "${ARGS[@]}"
    echo ""
    echo ">>> Step 2: Build .pkg installer"
    bash "${SCRIPT_DIR}/build-macos-pkg.sh" "${ARGS[@]}"
    ;;
  Linux)
    echo "Detected Linux"
    echo ""
    echo ">>> Step 1: Build PyInstaller binary and .AppImage"
    bash "${SCRIPT_DIR}/build-linux.sh" "${ARGS[@]}"
    echo ""
    echo ">>> Step 2: Build .deb package"
    bash "${SCRIPT_DIR}/build-linux-deb.sh" "${ARGS[@]}"
    echo ""
    echo ">>> Step 3: Build .rpm package"
    bash "${SCRIPT_DIR}/build-linux-rpm.sh" "${ARGS[@]}"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "Detected Windows (via bash)"
    exec powershell -File "${SCRIPT_DIR}/build-windows.ps1" "${ARGS[@]}"
    ;;
  *)
    echo "Unknown OS: $(uname -s)"
    exit 1
    ;;
esac
