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

echo "== Cross-feature facade imports inside features =="
facade_import_output="$(
  python3 - "$FEATURES_DIR" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

features_dir = Path(sys.argv[1])
patterns = [
    re.compile(r"\b(?:import|export)\b[\s\S]*?\bfrom\s*[\"']@/features/"),
    re.compile(r"\bimport\s*\(\s*[\"']@/features/"),
]

for path in sorted(features_dir.rglob("*")):
    if path.suffix not in {".js", ".jsx"}:
        continue
    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            line = text.splitlines()[line_no - 1].strip()
            print(f"{path}:{line_no}:{line}")
PY
)"
if [[ -n "$facade_import_output" ]]; then
  echo "$facade_import_output"
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

echo "== Disallowed component group subdirectories =="
allowed_component_groups='^(list|detail|form|dialog|table|chart|filters|cards|sections)$'
component_group_status=0
while IFS= read -r component_group; do
  group_name="$(basename "$component_group")"
  if [[ ! "$group_name" =~ $allowed_component_groups ]]; then
    echo "${component_group#$ROOT_DIR/}"
    component_group_status=1
  fi
done < <(find "$FEATURES_DIR" -mindepth 3 -maxdepth 3 -type d -path '*/components/*' | sort)
if [[ "$component_group_status" -eq 1 ]]; then
  status=1
else
  echo "OK"
fi
echo

echo "== Nested component group depth =="
component_depth_status=0
while IFS= read -r nested_component_dir; do
  echo "${nested_component_dir#$ROOT_DIR/}"
  component_depth_status=1
done < <(find "$FEATURES_DIR" -mindepth 4 -type d -path '*/components/*/*' | sort)
if [[ "$component_depth_status" -eq 1 ]]; then
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
