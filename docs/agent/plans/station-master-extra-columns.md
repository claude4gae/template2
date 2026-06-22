# ExecPlan: Station Master 추가 컬럼 반영

## 목표
- `station_master` 파일/모델에 `purge_target_yn`, `addr_book_id` 컬럼을 추가한다.
- 컬럼 순서는 `purge_yn` 다음, `eff_loss_type` 앞에 둔다.

## 현재 상태
- `station_master` spec은 현재 53개 컬럼을 기대한다.
- 실제 수신 파일은 55개 컬럼으로 확인되었다.
- 기존 migration `0001`에는 두 컬럼이 있었지만, `0002`에서 제거된 상태다.
- 이전 dry-run preview 정정분이 로컬에 남아 있어 함께 유지해야 한다.

## 범위
- 수정할 영역: `station_master` model, spec, tests, 신규 migration.
- 수정하지 않을 영역: 실제 적재 lifecycle, Airflow DAG, 다른 data movement 테이블.

## 설계
- `purge_target_yn`: `CharField(max_length=1, null=True, blank=True)`
- `addr_book_id`: `CharField(max_length=50, null=True, blank=True)`
- 파일 spec 컬럼 순서를 DB 모델 필드와 맞춘다.
- applied migration은 수정하지 않고 신규 migration을 생성한다.

## 실행 단계
- [x] model/spec/tests 수정
- [x] Docker Compose `api` 컨테이너에서 migration 생성
- [x] 검증 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations station_master`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py check`
- `docker compose -f docker-compose.dev.yml exec -T api python -m compileall -q api/data_movement/station_master`

## 위험과 대응
- 위험: 전체 DB 테스트는 현재 테스트 DB migration 중 `gin_trgm_ops` 확장 부재로 막힐 수 있다.
- 대응: 가능한 container check/compile/migration 검증을 수행하고, DB 테스트 블로커는 결과에 명시한다.

## 진행 기록
- 2026-06-22: 요청 컬럼 두 개를 `purge_yn` 뒤에 추가하기로 결정했다.
- 2026-06-22: `purge_target_yn`, `addr_book_id`를 model/spec에 추가하고 55컬럼 dry-run 검증을 통과했다.
- 2026-06-22: station_master 전용 dry-run 진단/preview 코드를 제거했다. `api.data_movement.station_master.tests`는 테스트 DB migration 중 `gin_trgm_ops` 확장 부재로 실행 전 실패했다.
