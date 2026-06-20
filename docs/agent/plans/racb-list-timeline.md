# ExecPlan: racb_list timeline 전환

## 목표
- `/data/data_movement/racb_list/incoming/*racb_list*.csv.deflate` 파일을 기본 DB의 `racb_list` 테이블에 적재한다.
- Observer RACB log 조회가 기존 observer DB `racb_list` 대신 새 Django data movement 테이블을 사용하게 한다.

## 현재 상태
- `apps/api/api/observer/selectors.py`의 `_fetch_racb_logs`는 observer DB `racb_list`를 직접 SQL 조회한다.
- `eqp_status_chg`, `mi_tip_update_hist`는 data movement nested app으로 기본 DB 테이블, loader, command, selector를 가진다.
- data movement 공통 mount는 `/data/data_movement`이고, 테이블별 root 하위 `incoming/processing`을 사용한다.

## 범위
- 수정할 영역: `api.data_movement.racb_list`, observer RACB selector, settings/env/data movement trigger, Airflow DAG, 관련 문서와 테스트.
- 수정하지 않을 영역: frontend timeline UI, 기존 observer 기준 정보 조회, EQP/TIP/CTTTM/ESOP selector 동작.

## 설계
- 새 Django app: `api.data_movement.racb_list`.
- 물리 테이블: `racb_list`.
- source file pattern: `*racb_list*.csv.deflate`.
- source file root: `/data/data_movement/racb_list`.
- 전처리:
  - 원천 row 중복 제거
  - `update_date`가 가장 최신인 row를 `c_racb_id`별로 1개 선택
  - 선택 row의 `eqp_ids`를 comma split/trim 후 row explode
  - target에는 exploded 설비 값을 `eqp_cb`로 저장
- observer RACB 응답 매핑: `eventTime=create_date`, `eventType=racb_type_cd`, `operator=user_name`, `comment=title`, `eqpId=eqp_cb`.
- migration/env/auth 영향:
  - 새 migration 필요.
  - `DATA_MOVEMENT_RACB_LIST_DIR` setting/env 추가.
  - public Observer API route는 그대로 유지한다.

## 실행 단계
- [x] 기존 data movement loader/selector/test 패턴 확인
- [x] ExecPlan 작성
- [x] `racb_list` app/model/migration/loader/command/selector/test 추가
- [x] data movement trigger/settings/env/Airflow 연결
- [x] observer RACB selector 전환과 테스트 보강
- [x] 문서 inventory/API/module/configuration 갱신
- [x] 검증 명령 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.racb_list api.observer --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `npm run agent:audit:api-boundary`
- `npm run agent:audit:docs`

## 위험과 대응
- 위험: 원천 `update_date`가 비어 있거나 파싱 불가하면 최신 row 선별 기준이 깨질 수 있다.
- 대응: 파싱 불가 row는 latest 선별에서 제외하고, `c_racb_id`와 `eqp_cb`, `create_date`가 있는 row만 저장한다.
- 위험: 원천 CSV delimiter가 comma가 아닐 가능성이 있다.
- 대응: 사용자 전처리 예시가 pandas 기본 CSV 흐름이므로 comma를 기본으로 적용하고, 필요 시 `FILE_SEPARATOR`만 조정 가능하게 spec에 둔다.

## 진행 기록
- 2026-06-20: 기존 observer RACB 조회와 data movement 패턴을 확인하고 구현 계획을 작성했다.
- 2026-06-20: `api.data_movement.racb_list` app/model/migration/loader/command/selector/test를 추가하고 observer RACB selector를 새 테이블 selector 위임으로 전환했다.
- 2026-06-20: `DATA_MOVEMENT_RACB_LIST_DIR`, data movement trigger registry, Airflow `load_racb_list` task, 관련 문서를 갱신했다.
- 2026-06-20: `python manage.py test api.data_movement.racb_list api.observer --keepdb`, `python manage.py test api.data_movement --keepdb`, `python manage.py makemigrations --check --dry-run`, `npm run agent:audit:api-boundary`, `npm run agent:audit:docs`, `git diff --check`가 통과했다.
- 2026-06-20: RACB 응답을 기존 예시와 맞춰 `eventType=racb_type_cd_status_code`, `eventTime=update_date`, `url=RACB_REPORT_BASE_URL` 기반으로 변경했고, stable ID는 `RACB-{c_racb_id}-{eqp_cb}`로 유지했다. focused test, migration check, api-boundary/docs audit, diff check가 통과했다.
