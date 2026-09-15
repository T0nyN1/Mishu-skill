#!/usr/bin/env bash
# Build demo vaults: 5 goal types + two weeks of simulated history + today's plan and check-in.
# Usage: bash examples/build_demo.sh [en|zh|all]   (default: all)
# Output: examples/demo-vault-en/ and examples/demo-vault-zh/ — your real config is never touched.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CLI="python3 $HERE/../skill/mishu/scripts/mishu.py"
on() { MISHU_TODAY="$1" "${@:2}"; }   # run a command as if it were a given date

build() {
  local lang="$1"
  VAULT="$HERE/demo-vault-$lang"
  export MISHU_CONFIG="$HERE/.demo-config-$lang/config.json"   # isolated config
  export MISHU_VAULT="$VAULT"
  rm -rf "$VAULT" "$HERE/.demo-config-$lang"
  # shellcheck source=/dev/null
  source "$HERE/demo-data/$lang.sh"
  on 2026-09-14 $CLI validate
  echo "✅ $VAULT"
}

case "${1:-all}" in
  en) build en ;;
  zh) build zh ;;
  all) build en; build zh ;;
  *) echo "usage: $0 [en|zh|all]"; exit 1 ;;
esac
