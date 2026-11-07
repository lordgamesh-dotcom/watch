#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XSD="$ROOT/tools/wff-schema/watchface.xsd"
MODULES=(watchface retrowave wasteland)
if command -v uv >/dev/null 2>&1; then
  for module in "${MODULES[@]}"; do
    XML="$ROOT/$module/src/main/res/raw/watchface.xml"
    uv run --with 'xmlschema==4.2.0' python -c 'import sys, xmlschema; xmlschema.XMLSchema11(sys.argv[1]).validate(sys.argv[2]); print("WFF XSD validation passed: " + sys.argv[3])' "$XSD" "$XML" "$module"
  done
elif command -v xmllint >/dev/null 2>&1; then
  echo "The vendored official WFF schema uses repeated xs:all groups; use an XSD 1.1 validator (uv is recommended) because libxml2/xmllint cannot compile this schema." >&2
  exit 2
else
  echo "Install uv for XSD 1.1 validation, or validate in Android Studio using its version-aware WFF validator." >&2
  exit 2
fi
if [[ -n "${WFF_MEMORY_EVALUATOR_JAR:-}" ]]; then
  for module in "${MODULES[@]}"; do
    java -jar "$WFF_MEMORY_EVALUATOR_JAR" --watch-face "$ROOT/$module/build/outputs/apk/debug/$module-debug.apk" --schema-version 2 --ambient-limit-mb 10 --active-limit-mb 100
  done
else
  echo "XSD validation passed. Memory evaluator not configured; see README for official evaluator instructions."
fi
