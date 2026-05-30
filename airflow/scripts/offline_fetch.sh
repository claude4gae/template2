#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMGDIR="$ROOT/vendor/images"

echo "[1/2] Load docker images"
docker load -i "$IMGDIR/apache-airflow-2.11.0.tar"
docker load -i "$IMGDIR/postgres-16.tar"

echo "[2/2] Check images"
docker images | grep -E 'apache/airflow|postgres' || true

echo "이미지 로드 완료. 이제 .env 만들고: docker compose up --build -d"
