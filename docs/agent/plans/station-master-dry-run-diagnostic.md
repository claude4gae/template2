# ExecPlan: Station Master dry-run 원본 파일 진단

## 목표
- `station_master` dry-run에서 deflate 해제 후 원본 row의 delimiter와 컬럼 수를 함께 진단한다.
- delimiter 불일치나 컬럼 수 불일치가 있으면 dry-run 실패로 보고해 실제 적재 전 원인을 확인할 수 있게 한다.

## 현재 상태
- `station_master` loader는 `--dry-run`에서 파일 이동과 DB 테이블 반영 없이 Polars 파싱만 수행한다.
- 기존 Polars 읽기는 `truncate_ragged_lines=True`라 원본 컬럼 수 불일치를 명확히 드러내지 못할 수 있다.

## 범위
- 수정할 영역: `station_master` loader, management command 출력, station_master 테스트.
- 수정하지 않을 영역: 실제 적재 경로, DB schema/migration, Airflow DAG, 다른 data movement 테이블.

## 설계
- dry-run 시작 시 deflate 파일을 직접 해제하고 `spec.FILE_SEPARATOR` 기준으로 row별 컬럼 수를 센다.
- 기대 컬럼 수는 `len(spec.COLUMNS)`를 사용한다.
- 불일치 row가 있으면 `LoadFileOutcome.status=failed`와 `raw_diagnostic`으로 반환한다.
- 정상 dry-run도 `raw_diagnostic`을 포함해 API 응답과 command 출력에서 확인 가능하게 한다.
- migration/env/auth 영향은 없다.

## 실행 단계
- [x] `station_master` loader에 raw diagnostic dataclass와 진단 함수를 추가한다.
- [x] dry-run outcome과 command 출력에 `raw_diagnostic`을 포함한다.
- [x] 정상 dry-run과 컬럼 수 불일치 dry-run 테스트를 추가한다.
- [x] 컨테이너 기준 검증을 실행한다.

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py check`
- `docker compose -f docker-compose.dev.yml exec -T api python -m compileall -q api/data_movement/station_master`
- DB를 mock 처리한 경량 dry-run 스크립트로 정상/실패 진단 결과 확인

## 위험과 대응
- 위험: 실제 테스트 DB migration이 `gin_trgm_ops` 확장 부재로 막혀 station_master DB 테스트를 직접 실행하지 못한다.
- 대응: Django system check, compileall, DB write mock 기반 dry-run 검증을 수행하고 블로커를 결과에 명시한다.

## 진행 기록
- 2026-06-22: dry-run 원본 delimiter/컬럼 수 진단을 추가하고 정상/실패 경량 검증을 통과했다.
