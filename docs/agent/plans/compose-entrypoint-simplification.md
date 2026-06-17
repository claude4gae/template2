# ExecPlan: compose entrypoint simplification

## 목표
- 사람이 실행하는 compose 파일을 dev/OIDC/운영 3개로 줄인다.
- infra는 DB, Airflow, FTP만 포함하고 나머지 기능 서비스는 app으로 분리한다.
- 긴 compose 명령 대신 `make` 명령으로 app/infra 각각의 up, build, down을 제공한다.
- 일반 개발용 `make dev`에서는 Airflow/FTP를 제외하고 app과 API DB 의존성만 실행한다.

## 현재 상태
- dev compose는 app/infra 조각으로 분리되어 있다.
- OIDC와 운영 compose도 app/infra 조각으로 분리되어 있다.
- root에는 실행 진입점 compose만 있고 내부 조각은 `compose/` 아래에 있다.

## 범위
- 수정할 영역: compose 파일 배치, root 실행 파일, Makefile, 실행 문서.
- 수정하지 않을 영역: env 변수 값, 앱 코드, DB schema, auth/OIDC/RAG contract.

## 설계
- root 실행 파일은 `docker-compose.dev.yml`, `docker-compose.oidc.yml`, `docker-compose.yml`로 유지한다.
- 내부 조각은 `compose/*.yml`로 이동한다.
- dev/OIDC/운영 모두 `*.infra.yml`과 `*.app.yml` 조각을 둔다.
- Airflow는 `compose/airflow.yml`로 공통화한다.
- Makefile은 app/infra 각각의 up, build, down target을 제공한다.
- dev 기본 실행은 `dev-app-up`만 호출한다. `api`의 `depends_on`으로 DB는 함께 올라가지만 Airflow/FTP는 시작하지 않는다.

## 실행 단계
- [x] 기존 dev/OIDC/운영 compose 구성을 확인한다.
- [x] `compose/` 하위 조각 파일을 추가한다.
- [x] root 실행 compose 파일을 include/extends 조립 파일로 정리한다.
- [x] Makefile 실행 target을 추가한다.
- [x] README와 운영 문서를 새 명령 기준으로 갱신한다.
- [x] compose config 검증을 실행한다.
- [x] `make dev`에서 Airflow/FTP를 제외하고 문서를 갱신한다.

## 검증
- `docker compose -f docker-compose.dev.yml config --services`
- `docker compose -f docker-compose.oidc.yml config --services`
- `docker compose -f docker-compose.yml config --services`
- `docker compose -f compose/dev.infra.yml config --services`
- `make -n dev-app-build`
- `make -n oidc-app-build`
- `make -n prod-app-build`

## 위험과 대응
- 위험: 조각 파일을 `compose/`로 옮기면서 상대 경로가 깨질 수 있다.
- 대응: 조각 파일 내부 경로는 `../apps`, `../env`, `../data`, `../airflow` 기준으로 명시한다.
- 위험: OIDC에 dummy ADFS가 섞이거나 운영 env가 dev env로 바뀔 수 있다.
- 대응: dev/OIDC/운영 app/infra 조각을 분리하고 env 파일 참조를 기존과 동일하게 유지한다.
- 위험: backend 재빌드 시 Airflow까지 재빌드될 수 있다.
- 대응: `*-app-build`는 app 빌드 대상만 빌드하고, `*-infra-build`는 Airflow 빌드 대상만 빌드한다.

## 진행 기록
- 2026-05-30: compose 실행 진입점 단순화와 infra/backend 분리 설계를 정리했다.
- 2026-05-30: dev/OIDC/운영 compose config와 Makefile dry-run 검증을 통과했다.
- 2026-05-30: 사용자 기준에 맞춰 infra를 Airflow/FTP/DB로 제한하고, MinIO/dummy/API/Web/Nginx를 app 그룹으로 이동했다.
- 2026-06-14: 일반 개발에서 Airflow/FTP가 필요 없다는 기준에 맞춰 `make dev`를 app 실행으로 축소하고, Airflow/FTP는 `dev-infra-up`으로 분리했다.
- 2026-06-14: `compose/dev.app.yml`은 DB service를 포함하지 않는 내부 조각이므로 단독 compose 검증 대상에서 제외했다.
