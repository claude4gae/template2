#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_SRC="apps/web/src"
ALLOWLIST="$ROOT_DIR/scripts/agent/ui-audit-allowlist.txt"

cd "$ROOT_DIR"

if [[ ! -d "$WEB_SRC" ]]; then
  echo "Missing frontend source directory: apps/web/src" >&2
  exit 2
fi

status=0
allowlist_patterns="$(mktemp)"
trap 'rm -f "$allowlist_patterns"' EXIT

if [[ -f "$ALLOWLIST" ]]; then
  sed -E '/^[[:space:]]*(#|$)/d' "$ALLOWLIST" > "$allowlist_patterns"
fi

check_pattern() {
  local title="$1"
  local pattern="$2"
  shift 2
  local raw_results
  local filtered_results
  raw_results="$(mktemp)"
  filtered_results="$(mktemp)"

  echo "== $title =="
  if rg --color never -n "$pattern" "$WEB_SRC" "$@" -g '*.jsx' -g '*.js' -g '*.css' > "$raw_results"; then
    if [[ -s "$allowlist_patterns" ]]; then
      grep -Ev -f "$allowlist_patterns" "$raw_results" > "$filtered_results" || true
    else
      cp "$raw_results" "$filtered_results"
    fi
  fi

  if [[ -s "$filtered_results" ]]; then
    cat "$filtered_results"
    status=1
  else
    echo "OK"
  fi
  rm -f "$raw_results" "$filtered_results"
  echo
}

check_pattern \
  "Raw HEX colors" \
  '(^|[^&])#[0-9A-Fa-f]{3,8}'

check_pattern \
  "Raw gray/slate/zinc palette classes" \
  '(text|bg|border|ring)-(gray|slate|zinc)-[0-9]{2,3}'

check_pattern \
  "Inline style usage" \
  'style=\{'

check_pattern \
  "Route/page h-screen usage" \
  'h-screen' \
  -g '!*components/ui*'

echo "== Feature facade export-star usage =="
facade_status=0
while IFS= read -r facade_file; do
  if rg --color never -n 'export \*' "$facade_file"; then
    facade_status=1
  fi
done < <(find "$WEB_SRC/features" -mindepth 2 -maxdepth 2 -type f -name 'index.js' | sort)
if [[ "$facade_status" -eq 1 ]]; then
  status=1
else
  echo "OK"
fi
echo

if [[ "$status" -eq 0 ]]; then
  echo "UI consistency audit passed."
else
  echo "UI consistency audit found review candidates."
  echo "Review exceptions before changing code: shadcn internals, measured layout, SVG masks, third-party libraries."
fi

exit "$status"
