# ExecPlan: eqp_status_chg timeline 전환

## 목표
- `/data/data_movement/m_eqp_status_chg/incoming/*m_eqp_status_chg*.csv.deflate` 파일을 기본 DB의 `eqp_status_chg` 테이블에 적재한다.
- timeline EQP log 조회가 기존 observer DB `eqp_status_hist` 대신 새 `eqp_status_chg` 테이블을 사용하게 한다.
- 적재 전 `eqp_id`가 `E/e`로 시작하지 않는 row와 `chg_time`이 실행 시점 기준 180일보다 오래된 row를 제외한다.
- 저장 시 `eqp_cb = eqp_id-chamber_id`를 생성하고 `eqp_id`, `chamber_id`는 대상 테이블에 저장하지 않는다.
- 기존 target row도 적재마다 180일 retention 기준으로 삭제한다.

## 현재 상태
- `apps/api/api/observer/selectors.py`의 `_fetch_eqp_logs`는 observer 전용 DB `eqp_status_hist`를 직접 조회한다.
- data movement app들은 `apps/api/api/data_movement/<table_name>` 아래에 table별 model, loader, command, tests를 둔다.
- `ct_process_comment`는 streaming deflate CSV 선별 후 temp table COPY + upsert 패턴을 사용한다.

## 범위
- 수정할 영역: `api.data_movement.eqp_status_chg`, observer EQP selector, settings/env/compose/docs/Airflow data movement wiring.
- 수정하지 않을 영역: frontend timeline UI, 기존 observer DB 기준 정보 조회, TIP/CTTTM/RACB/ESOP selector.

## 설계
- 새 Django data movement table app: `api.data_movement.eqp_status_chg`.
- 물리 테이블: `eqp_status_chg`.
- unique key: `eqp_event_key`.
- 조회 인덱스: timeline 쿼리의 `eqp_cb` equality + `chg_time` range/order에 맞춰 `(eqp_cb, chg_time)` 복합 인덱스 추가.
- 적재 흐름: incoming 파일 선점 -> deflate CSV streaming -> row 필터/`eqp_cb` 생성 -> temp CSV -> temp table COPY -> `ON CONFLICT (eqp_event_key)` upsert -> retention purge.
- observer EQP 응답 매핑: `eventTime=chg_time`, `eventType=eqp_status_type`, `operator=operator_emp_id`, `comment=chg_comment`, `eqpId=eqp_cb`.
- 파일 mount/env: 기존 `DATA_MOVEMENT_HOST_PATH` mount 아래 `/data/data_movement/m_eqp_status_chg`를 사용하고 `DATA_MOVEMENT_EQP_STATUS_CHG_DIR` setting/env를 추가한다.

## 실행 단계
- [x] 계획 문서 작성
- [x] 새 data movement app 파일과 migration 추가
- [x] loader/command/test 구현
- [x] observer selector 전환과 selector test 보강
- [x] settings/env/docs wiring 갱신
- [x] Airflow DAG wiring 갱신
- [x] Django test와 agent audit 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.eqp_status_chg api.observer --keepdb`
- `npm run agent:audit:api-boundary`
- 필요 시 `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`

## 위험과 대응
- 위험: `eqp_event_key`가 비어 있거나 숫자로 변환되지 않으면 upsert key가 없어 적재 실패 또는 skip이 필요하다.
- 대응: loader에서 `eqp_event_key`가 있는 row만 temp CSV로 내보내고, 비어 있으면 empty file로 실패 처리한다.
- 위험: timezone-aware/naive datetime 비교가 섞일 수 있다.
- 대응: 파일 datetime은 naive로 파싱하고 cutoff도 timezone에서 naive UTC로 변환해 비교한다.
- 위험: 새 테이블 전환 후 기존 observer DB의 `eqp_status_hist`와 event type 값이 다를 수 있다.
- 대응: 사용자 확인에 따라 `eqp_status_type`을 `eventType`으로 그대로 반환한다.

## 진행 기록
- 2026-06-20: 사용자 결정에 따라 기본 DB 새 테이블, `eqp_event_key` unique upsert, 180일 retention, `eqp_cb` 파생 저장 설계를 확정했다.
- 2026-06-20: `api.data_movement.eqp_status_chg` app/model/migration/loader/command/test를 추가하고 observer EQP selector를 새 테이블 selector로 전환했다.
- 2026-06-20: `airflow/dags/data_movement_file_load.py`는 파일/디렉터리 owner가 `50000:root`라 Docker root로 임시 쓰기 권한을 열어 `load_eqp_status_chg` task를 추가했고, 권한은 기존 모드로 복구했다.
- 2026-06-20: `python manage.py test api.data_movement.eqp_status_chg api.observer --keepdb`, `python manage.py makemigrations --check --dry-run`, `npm run agent:audit:api-boundary`, `npm run agent:audit:docs`가 통과했다.
