#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APK="$ROOT/watchface/build/outputs/apk/debug/watchface-debug.apk"
[[ -f "$APK" ]] || "$ROOT/gradlew" :watchface:assembleDebug
adb install -r "$APK"
echo "Installed package. Select Cyberpunk HUD from the watch face picker."
