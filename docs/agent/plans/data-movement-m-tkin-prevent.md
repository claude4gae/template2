# ExecPlan: data_movement m_tkin_prevent

## 목표
- 파일 기반 DB 적재 코드를 `api.data_movement.<table_name>` 중첩 Django app 구조로 정리한다.
- 첫 대상 테이블 `m_tkin_prevent`의 model, migration, service, management command를 추가한다.
- 향후 다른 테이블이 같은 구조를 반복할 수 있도록 공통 적재 유틸을 분리한다.

## 현재 상태
- 기존 backend 규칙은 `apps/api/api/<feature>` 단일 depth app을 전제한다.
- 사용자와 합의한 새 방향은 `apps/api/api/data_movement/<table_name>` 아래에 테이블별 Django app을 두는 구조다.
- `apps/api/requirements.txt`에는 `psycopg[binary]`는 있으나 `polars`는 없다.

## 범위
- 수정할 영역:
  - `apps/api/AGENTS.md`
  - `apps/api/config/settings.py`
  - `apps/api/requirements.txt`
  - `apps/api/api/data_movement/**`
- 수정하지 않을 영역:
  - Airflow DAG 구현
  - HTTP API endpoint
  - 기존 feature app의 데이터 모델

## 설계
- `api.data_movement.m_tkin_prevent`를 독립 Django app으로 등록한다.
- `m_tkin_prevent` model과 `m_tkin_prevent_load_job` 이력 model을 같은 app에 둔다.
- `api.data_movement.common.services`에는 deflate CSV 읽기, 파일 반복, PostgreSQL COPY 유틸만 둔다.
- `m_tkin_prevent/services/spec.py`에는 컬럼/타입/경로/교체 기준을 둔다.
- `m_tkin_prevent/services/loader.py`는 common 유틸을 조합하고 load job 이력을 기록한다.
- `load_m_tkin_prevent` management command를 Airflow 호출 진입점으로 둔다.

## 실행 단계
- [x] data_movement 중첩 app 규칙을 `apps/api/AGENTS.md`에 추가
- [x] ExecPlan 작성
- [x] settings/requirements 수정
- [x] common 적재 유틸 추가
- [x] `m_tkin_prevent` app/model/service/command/migration/test 추가
- [x] syntax/test/migration 검증

## 검증
- `python -m compileall apps/api/api/data_movement`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.m_tkin_prevent`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`

## 위험과 대응
- 위험: psycopg3 COPY API가 Django cursor wrapper와 다를 수 있다.
- 대응: wrapper 내부 cursor의 `copy()`를 사용하고 테스트 가능한 경계를 command/service로 분리한다.
- 위험: 외부 파일의 문자열 길이를 미리 알 수 없다.
- 대응: 원본 문자열 컬럼은 `TextField`로 둔다.

## 진행 기록
- 2026-05-29: `data_movement/<table_name>` 중첩 app 구조로 진행하기로 결정했다.
- 2026-05-29: `m_tkin_prevent` app, 공통 적재 유틸, migration, command, tests를 추가하고 검증을 통과했다.
- 2026-05-29: `m_tkin_prevent` 기본 적재 경로를 `/data/data_movement/m_tkin_prevent`로 변경했다.
- 2026-05-29: dev, OIDC dev, prod compose 모두에 `/data/data_movement` mount를 추가했다.
- 2026-05-29: FTP 수신 중 파일 읽기를 피하기 위해 `incoming/processing` lifecycle을 추가했고 처리 후 파일은 항상 삭제한다.
- 2026-05-29: `ctttm_workorder_list`는 source_type 단위 교체와 선택 컬럼 적재 방식으로 추가한다.
- 2026-05-29: `ct_process_comment`는 workorder_id incremental upsert, USE_YN=N 제외, CREATE_DATE 180일, workorder 목록 기준 정리 방식으로 추가한다.
