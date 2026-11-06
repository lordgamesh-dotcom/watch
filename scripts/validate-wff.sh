#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XML="$ROOT/watchface/src/main/res/raw/watchface.xml"
XSD="$ROOT/tools/wff-schema/watchface.xsd"
if command -v uv >/dev/null 2>&1; then
  uv run --with 'xmlschema==4.2.0' python -c 'import sys, xmlschema; xmlschema.XMLSchema11(sys.argv[1]).validate(sys.argv[2]); print("WFF XSD validation passed")' "$XSD" "$XML"
elif command -v xmllint >/dev/null 2>&1; then
  echo "The vendored official WFF schema uses repeated xs:all groups; use an XSD 1.1 validator (uv is recommended) because libxml2/xmllint cannot compile this schema." >&2
  exit 2
else
  echo "Install uv for XSD 1.1 validation, or validate in Android Studio using its version-aware WFF validator." >&2
  exit 2
fi
if [[ -n "${WFF_MEMORY_EVALUATOR_JAR:-}" ]]; then
  java -jar "$WFF_MEMORY_EVALUATOR_JAR" --watch-face "$ROOT/watchface/build/outputs/apk/debug/watchface-debug.apk" --schema-version 2 --ambient-limit-mb 10 --active-limit-mb 100
else
  echo "XSD validation passed. Memory evaluator not configured; see README for official evaluator instructions."
fi
