# ExecPlan: observer lookup index optimization

## 목표
- observer 기준정보/로그 조회에서 대소문자 변환 조건을 제거하고, 정규화 lookup 컬럼과 복합 인덱스로 빠르게 조회한다.

## 현재 상태
- `api.observer.selectors`는 `upper(...)` raw SQL과 `__iexact` selector를 함께 사용한다.
- 로그 원천 일부는 `(eqp_cb, 시간)` 인덱스가 있으나 `__iexact` 때문에 최적 활용이 제한될 수 있다.
- CTTTM과 ESOP observer 조회는 시간 정렬을 포함한 설비 lookup 복합 인덱스가 없다.

## 범위
- 수정: observer가 직접 조회하는 data movement 모델/loader/selector, `DroneSOP` 모델, observer raw SQL selector.
- 수정: lookup 컬럼 추가 migration과 backfill/index 추가.
- 제외: API response contract, auth/permission, frontend 화면, unrelated domain refactor.

## 설계
- 원본 표시 컬럼은 유지하고 `*_lookup` 컬럼에 `strip().upper()` 값을 저장한다.
- 조회는 `upper(...)`, `__iexact` 대신 `*_lookup = normalize_id(...)`를 사용한다.
- 최신순 timeline 조회는 `(lookup, -time)` 복합 인덱스를 사용한다.
- migration은 nullable lookup 컬럼 추가, 기존 데이터 backfill, 인덱스 추가 순서로 작성한다.
- env/auth contract 영향은 없다.

## 실행 단계
- [x] 관련 loader/model/selector 구조 확인
- [x] lookup 컬럼과 인덱스 추가
- [x] loader/service에서 lookup 값 저장
- [x] observer/data movement selector를 lookup 기준으로 변경
- [x] migration 생성 또는 수동 작성
- [x] 테스트/감사 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.observer api.data_movement.eqp_status_chg api.data_movement.mi_tip_update_hist api.data_movement.racb_list api.data_movement.ctttm_workorder_list api.data_movement.station_master api.data_movement.mes_line_mapping_info api.drone`
- `npm run agent:audit:api-boundary`

## 위험과 대응
- 위험: 대용량 테이블 backfill/index 생성으로 migration 시간이 길어질 수 있다.
- 대응: lookup 컬럼은 nullable로 추가하고, 인덱스는 조회 패턴에 맞는 최소 복합 인덱스로 제한한다.
- 위험: loader 경로에서 lookup 값을 누락하면 신규 row가 조회되지 않을 수 있다.
- 대응: row 생성 지점에 정규화 helper를 추가하고 selector 테스트로 조회를 검증한다.

## 진행 기록
- 2026-06-22: observer 조회 성능 최적화 방향을 lookup 컬럼 + 복합 인덱스로 결정.
- 2026-06-22: 로그/기준정보/ESOP 조회 모델에 lookup 컬럼과 복합 인덱스를 추가하고 selector/loader를 lookup 기준으로 변경.
- 2026-06-22: `makemigrations --check --dry-run`, 관련 backend 테스트 345개, backend boundary audit 통과.
