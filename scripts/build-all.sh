#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$(uname -s)" in
  Darwin)
    echo "Detected macOS"
    exec bash "${SCRIPT_DIR}/build-macos.sh"
    ;;
  Linux)
    echo "Detected Linux"
    exec bash "${SCRIPT_DIR}/build-linux.sh"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "Detected Windows (via bash)"
    exec powershell -File "${SCRIPT_DIR}/build-windows.ps1"
    ;;
  *)
    echo "Unknown OS: $(uname -s)"
    exit 1
    ;;
esac
