# ExecPlan: ct_process_comment update flag

## 목표
- `ct_process_comment` 적재 시 날짜 필터를 제거한다.
- 원천 row 중 `eqp_id`가 `E/e`로 시작하는 row만 사용한다.
- 신규 row와 실제 데이터가 변경된 기존 row에 `update_flag=Y`를 설정한다.
- 동일한 기존 row는 기존 `update_flag`를 유지한다.

## 현재 상태
- `apps/api/api/data_movement/ct_process_comment/services/loader.py`가 deflate CSV를 선별 CSV로 변환한 뒤 PostgreSQL COPY와 upsert를 수행한다.
- 중복 기준은 `workorder_id` unique constraint이다.
- 이전 변경으로 원천 separator는 `\x03`을 사용한다.

## 범위
- 수정: `ct_process_comment` model, migration, spec, loader, tests.
- 제외: 외부 API 호출 구현, flag 처리 완료 API/service, 기존 DB row 중 `eqp_id`가 `E/e`가 아닌 row 삭제.

## 설계
- `CtProcessComment.update_flag` 컬럼을 `CharField(max_length=1, default="N")`로 추가한다.
- 선별 CSV에는 기존 DB 컬럼만 유지하고 `update_flag`는 SQL insert/upsert 단계에서 계산한다.
- 원천 필터는 `eqp_id` 대소문자 무시 prefix 조건으로 적용한다.
- 날짜 필터는 제거하지만 `create_date`, `update_date`, `modify_date` 컬럼은 계속 저장한다.
- `ON CONFLICT (workorder_id)`에서 데이터 컬럼이 `IS DISTINCT FROM`이면 대상 컬럼을 갱신하고 `update_flag=Y`로 설정한다.
- 데이터 컬럼이 동일하면 UPDATE를 수행하지 않아 기존 flag를 보존한다.

## 실행 단계
- [x] 모델에 `update_flag` 추가
- [x] spec에 `eqp_id` prefix 필터와 날짜 필터 제거 반영
- [x] loader upsert SQL에 update flag 계산 추가
- [x] 테스트를 신규/변경/동일/eqp prefix 기준으로 보강
- [x] migration 생성 및 검토

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations ct_process_comment`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.ct_process_comment --keepdb`
- `git diff --check -- <changed files>`

## 위험과 대응
- 위험: 동일 row 재적재 시 아직 처리되지 않은 `update_flag=Y`가 사라질 수 있다.
- 대응: 동일 데이터에는 UPDATE를 수행하지 않고 기존 flag를 보존한다.
- 위험: 날짜 필터 제거로 입력량이 늘어날 수 있다.
- 대응: `eqp_id` prefix 필터를 스트리밍 선별 단계에서 먼저 적용한다.

## 진행 기록
- 2026-06-19: 사용자 결정에 따라 날짜 제한을 제거하고 `eqp_id` `E/e` prefix 필터 및 `update_flag` 추가 설계를 확정했다.
- 2026-06-19: `ct_process_comment` 앱 테스트 9건, migration check, backend boundary audit을 통과했다.
