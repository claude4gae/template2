#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_SRC="$ROOT_DIR/apps/web/src"
FEATURES_DIR="$WEB_SRC/features"

if [[ ! -d "$FEATURES_DIR" ]]; then
  echo "Missing feature directory: apps/web/src/features" >&2
  exit 2
fi

status=0

echo "== Cross-feature internal imports =="
if rg -n '@/features/[^"'\'';]+/(components|pages|api|hooks|store|utils)|@/features/[^"'\'';]+/index\.js' "$WEB_SRC" -g '*.jsx' -g '*.js'; then
  status=1
else
  echo "OK"
fi
echo

echo "== Feature index export-star usage =="
facade_status=0
while IFS= read -r facade_file; do
  if rg -n 'export \*' "$facade_file"; then
    facade_status=1
  fi
done < <(find "$FEATURES_DIR" -mindepth 2 -maxdepth 2 -type f -name 'index.js' | sort)
if [[ "$facade_status" -eq 1 ]]; then
  status=1
else
  echo "OK"
fi
echo

echo "== Missing feature routes.jsx or index.js =="
missing_status=0
while IFS= read -r feature_dir; do
  feature_name="$(basename "$feature_dir")"
  if [[ ! -f "$feature_dir/index.js" ]]; then
    echo "$feature_name: missing index.js"
    missing_status=1
  fi
  if [[ ! -f "$feature_dir/routes.jsx" ]]; then
    echo "$feature_name: missing routes.jsx"
    missing_status=1
  fi
done < <(find "$FEATURES_DIR" -mindepth 1 -maxdepth 1 -type d | sort)
if [[ "$missing_status" -eq 1 ]]; then
  status=1
else
  echo "OK"
fi
echo

echo "== Disallowed feature subdirectories =="
allowed_subdirs='^(pages|components|hooks|api|store|utils)$'
subdir_status=0
while IFS= read -r subdir; do
  subdir_name="$(basename "$subdir")"
  if [[ ! "$subdir_name" =~ $allowed_subdirs ]]; then
    echo "${subdir#$ROOT_DIR/}"
    subdir_status=1
  fi
done < <(find "$FEATURES_DIR" -mindepth 2 -maxdepth 2 -type d | sort)
if [[ "$subdir_status" -eq 1 ]]; then
  status=1
else
  echo "OK"
fi
echo

if [[ "$status" -eq 0 ]]; then
  echo "Frontend boundary audit passed."
else
  echo "Frontend boundary audit found review candidates."
fi

exit "$status"
