#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

status=0

fail() {
  echo "FAIL: $*"
  status=1
}

ok() {
  echo "OK: $*"
}

require_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    ok "문서 존재: $path"
  else
    fail "문서 누락: $path"
  fi
}

require_text() {
  local file="$1"
  local text="$2"
  local label="$3"
  if grep -Fq "$text" "$file"; then
    ok "$label"
  else
    fail "$label 누락: $text in $file"
  fi
}

normalize_django_path() {
  sed -E 's#<[^:>/]+:([^>]+)>#<\1>#g; s#/$##'
}

DOCS_INDEX="docs/inventory.md"

echo "== 필수 문서 =="
for path in \
  docs/README.md \
  docs/architecture.md \
  docs/inventory.md \
  docs/frontend.md \
  docs/backend.md \
  docs/data-model.md \
  docs/configuration.md \
  docs/api/README.md \
  docs/modules/README.md \
  docs/operations.md \
  docs/integrations.md \
  README.md \
  apps/api/README.md \
  apps/web/README.md; do
  require_file "$path"
done
echo

echo "== README 문서 진입점 링크 =="
for docs_path in \
  docs/README.md \
  docs/architecture.md \
  docs/inventory.md \
  docs/backend.md \
  docs/frontend.md \
  docs/data-model.md \
  docs/configuration.md \
  docs/api/README.md; do
  require_text "README.md" "$docs_path" "root README link $docs_path"
done
require_text "apps/api/README.md" "docs/backend.md" "api README backend link"
require_text "apps/api/README.md" "docs/inventory.md" "api README inventory link"
require_text "apps/web/README.md" "docs/frontend.md" "web README frontend link"
require_text "apps/web/README.md" "docs/inventory.md" "web README inventory link"
echo

echo "== Backend API endpoint 색인 =="
while IFS= read -r route; do
  [[ -z "$route" ]] && continue
  normalized="$(printf '%s' "$route" | normalize_django_path)"
  [[ -z "$normalized" ]] && continue
  require_text "$DOCS_INDEX" "$normalized" "endpoint $normalized"
done < <(
  rg -o 'path\("([^"]*)"' apps/api/api/*/urls.py \
    | sed -E 's#.*path\("([^"]*)"#\1#' \
    | sort -u
)
echo

echo "== Frontend route 색인 =="
for route in \
  "/" \
  "/login" \
  "/settings/account" \
  "/settings/members" \
  "/emails/inbox" \
  "/emails/sent" \
  "/emails/members" \
  "/assistant" \
  "/ESOP_Dashboard" \
  "/timeline" \
  "/timeline/:eqpId" \
  "/appstore" \
  "/voc" \
  "/teamstaff"; do
  require_text "$DOCS_INDEX" "$route" "frontend route $route"
done
echo

echo "== Django model 색인 =="
while IFS= read -r model_name; do
  [[ -z "$model_name" ]] && continue
  [[ "$model_name" == "UserManager" ]] && continue
  require_text "$DOCS_INDEX" "$model_name" "model $model_name"
done < <(
  rg -o '^class ([A-Za-z_][A-Za-z0-9_]*)\(' apps/api/api/*/models.py \
    | sed -E 's#.*class ([A-Za-z_][A-Za-z0-9_]*)\(.*#\1#' \
    | sort -u
)
echo

echo "== Management command 색인 =="
while IFS= read -r command_file; do
  command_name="$(basename "$command_file" .py)"
  [[ "$command_name" == "__init__" ]] && continue
  require_text "$DOCS_INDEX" "$command_name" "command $command_name"
  require_text "docs/operations.md" "$command_name" "operations command $command_name"
done < <(find apps/api/api -path '*/management/commands/*.py' -type f | sort)
echo

echo "== Env group 색인 =="
for env_group in \
  "DJANGO_*" \
  "DJANGO_DB_*" \
  "TIMELINE_DB_*" \
  "OIDC_*" \
  "ADFS_*" \
  "AIRFLOW_TRIGGER_TOKEN" \
  "EMAIL_POP3_*" \
  "DRONE_*" \
  "KNOX_MESSENGER_*" \
  "ASSISTANT_*" \
  "RAG_*" \
  "MAIL_API_*" \
  "MINIO_*" \
  "VITE_*"; do
  require_text "$DOCS_INDEX" "$env_group" "env group $env_group"
  require_text "docs/configuration.md" "$env_group" "configuration env group $env_group"
done
echo

exit "$status"
