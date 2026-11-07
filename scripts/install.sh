#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Usage: scripts/install.sh [watchface|retrowave|wasteland]   (default: watchface)
MODULE="${1:-watchface}"
APK="$ROOT/$MODULE/build/outputs/apk/debug/$MODULE-debug.apk"
[[ -f "$APK" ]] || "$ROOT/gradlew" ":$MODULE:assembleDebug"
adb install -r "$APK"
echo "Installed $MODULE. Select it from the watch face picker."
