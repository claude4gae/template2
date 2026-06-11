# base 이미지는 offline_load.sh로 사전에 docker에 로드되어 있어야 함
FROM apache/airflow:2.11.0

USER root
ARG CS_VER=4.105.1
ARG CODE_SERVER_TARBALL_URL

# code-server 설치 파일은 Compose build arg로 주입해 개발/폐쇄망 경로를 분리합니다.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl tar; \
    test -n "${CODE_SERVER_TARBALL_URL}"; \
    curl -fL "${CODE_SERVER_TARBALL_URL}" -o /tmp/code-server.tar.gz; \
    tar -xzf /tmp/code-server.tar.gz -C /usr/local --strip-components=1 code-server-${CS_VER}-linux-amd64; \
    ln -sf /usr/local/bin/code-server /usr/bin/code-server; \
    rm -f /tmp/code-server.tar.gz; \
    rm -rf /var/lib/apt/lists/*

# airflow 유저 홈/설정 디렉토리 준비 및 권한 부여
RUN install -d -o airflow -g 0 -m 770 \
      /home/airflow/.config/code-server \
      /home/airflow/.local/share/code-server \
      /home/airflow/.local/share/code-server/extensions \
      /home/airflow/.vscode \
      /opt/airflow/logs

USER airflow
WORKDIR /opt/airflow
