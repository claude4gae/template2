#!/usr/bin/env bash
set -euo pipefail

# 원하는 버전
AIRFLOW_IMG="apache/airflow:2.11.0-python3.11"
POSTGRES_IMG="postgres:16"
CS_VER="4.105.1"

# 현재 스크립트 기준 경로
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="$ROOT/vendor"
IMGDIR="$VENDOR/images"
mkdir -p "$IMGDIR"

echo "[1/3] Pull docker images"
docker pull "$AIRFLOW_IMG"
docker pull "$POSTGRES_IMG"

echo "[2/3] Save docker images to tar"
docker save "$AIRFLOW_IMG"   -o "$IMGDIR/apache-airflow-2.11.0.tar"
docker save "$POSTGRES_IMG"  -o "$IMGDIR/postgres-16.tar"

echo "[3/3] Download code-server tarball"
mkdir -p "$VENDOR"
curl -fL "https://github.com/coder/code-server/releases/download/v${CS_VER}/code-server-${CS_VER}-linux-amd64.tar.gz" \
  -o "$VENDOR/code-server-${CS_VER}-linux-amd64.tar.gz"

echo "Done! 이제 'airflow-offline' 폴더를 폐쇄망으로 옮기세요."
