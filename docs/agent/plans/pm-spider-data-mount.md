# ExecPlan: PM SPIDER 데이터 마운트 경로 변경

## 목표
- PM Comparison API가 PM SPIDER 데이터를 `/data/pm_spider` 컨테이너 경로에서 읽도록 설정과 Docker Compose 마운트를 정렬한다.

## 현재 상태
- `apps/api/config/settings.py`의 `PM_COMPARISON_DATA_ROOT` fallback은 `/appdata/PM_SPIDER/result`이다.
- `env/api.common.env`에는 `PM_COMPARISON_DATA_ROOT`가 명시되어 있지 않다.
- `compose/dev.app.yml`, `compose/prod.app.yml`, `compose/oidc.app.yml`에는 PM SPIDER 전용 volume mount가 없다.
- `apps/api/api/pm_comparison/selectors.py`는 데이터 루트 바로 아래의 `raw_data`, `score_data`를 조회한다.
- 실제 운영 데이터는 단일 mount 아래 `data`, `pm_spider_result` 이름으로 들어올 수 있다.

## 범위
- 수정: API PM Comparison 데이터 루트 기본값, 공통 env, dev/prod/oidc compose volume, 설정 문서.
- 제외: PM Comparison API schema, 프론트엔드, 데이터 파일 구조 변경.

## 설계
- 컨테이너 내부 데이터 루트는 `/data/pm_spider`로 통일한다.
- 호스트 경로는 `PM_COMPARISON_DATA_HOST_PATH`로 override 가능하게 하고 기본값은 `../data/pm_spider`로 둔다.
- 서비스 env는 `PM_COMPARISON_DATA_ROOT=/data/pm_spider`를 사용한다.
- PM Comparison selector는 표준 `raw_data`/`score_data`를 우선하고, 없으면 legacy `data`/`pm_spider_result`를 같은 의미로 해석한다.
- API/DB/auth contract 영향은 없고, env/compose contract만 변경된다.

## 실행 단계
- [x] ExecPlan 작성
- [x] API 설정 fallback과 공통 env 추가
- [x] dev/prod/oidc compose에 read-only mount 추가
- [x] 설정 문서 갱신
- [x] compose config와 Django PM Comparison 테스트 검증
- [x] 단일 mount legacy 폴더명 fallback 구현

## 검증
- `docker compose -f docker-compose.dev.yml config`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.pm_comparison`

## 위험과 대응
- 위험: `../data/pm_spider`가 비어 있거나 없으면 API 조회 시 데이터 경로 오류가 난다.
- 대응: 운영/개발 실행 전 호스트 경로에 `raw_data`, `score_data`가 있는지 확인하거나 `PM_COMPARISON_DATA_HOST_PATH`를 실제 위치로 지정한다.

## 진행 기록
- 2026-06-11: `/data/pm_spider` 컨테이너 경로 기준으로 변경하기로 결정했다.
- 2026-06-11: API fallback, 공통 env, compose read-only mount, 설정 문서를 `/data/pm_spider` 기준으로 갱신했다.
- 2026-06-11: `docker compose -f docker-compose.dev.yml config`와 `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.pm_comparison` 검증을 통과했다.
- 2026-06-11: `/data/pm_spider` 단일 mount 아래 `data`, `pm_spider_result` legacy 폴더명을 지원하도록 selector fallback과 테스트를 추가했다.
