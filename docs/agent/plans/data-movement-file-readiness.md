# ExecPlan: Data Movement 파일 readiness 가드

## 목표
- FTP 등 송신 측이 최종 파일명으로 직접 전송하더라도, data movement 적재가 전송 중 파일을 가능한 한 선점하지 않게 한다.
- 기본 정책은 마지막 수정 후 60초 이상 지난 파일만 적재 대상으로 보고, 짧은 stat 재확인 중 size/mtime이 바뀌면 이번 실행에서 건너뛴다.

## 현재 상태
- Airflow `data_movement_file_load` DAG는 1분 주기로 API 적재 endpoint를 호출한다.
- Django 공통 로더는 `incoming`에서 파일명 패턴에 맞는 파일을 찾고, `processing`으로 atomic move해서 선점한다.
- 송신 측 rename 또는 완료 marker를 강제할 수 없다.

## 범위
- 수정할 영역: data movement 공통 파일 로더, Django settings/env, 운영 문서, 공통 로더 테스트.
- 수정하지 않을 영역: 테이블별 적재 로직, Airflow DAG schedule, DB schema/migration, FTP service 설정.

## 설계
- `DATA_MOVEMENT_FILE_READY_MIN_AGE_SECONDS`로 최소 mtime age를 설정한다. 기본값은 60초다.
- `DATA_MOVEMENT_FILE_READY_STABILITY_SECONDS`로 stat 재확인 대기 시간을 설정한다. 기본값은 1초다.
- 파일 목록 필터와 선점 직전 검증에 같은 readiness 기준을 사용한다.
- public API 응답 형식, DB schema, auth contract는 변경하지 않는다.
- env contract만 추가되며 compose mount contract는 변경하지 않는다.

## 실행 단계
- [x] 공통 로더에 readiness helper와 필터를 추가한다.
- [x] settings/env/docs에 새 `DATA_MOVEMENT_*` 값을 추가한다.
- [x] 공통 로더 테스트에 최근 파일 skip, 안정 파일 포함, stat 변경 skip 케이스를 추가한다.
- [x] Docker Compose `api` 컨테이너에서 대상 테스트를 실행한다.

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.tests.DataMovementFileLoaderTests --keepdb`
- 기대 결과: readiness 필터와 기존 case-insensitive 파일 매칭 테스트가 통과한다.

## 위험과 대응
- 위험: 송신자가 큰 파일 전송 중 60초 이상 멈추면 완료 파일로 오판할 수 있다.
- 대응: 완료 marker/rename을 강제할 수 없는 조건에서는 완전 보장이 불가능하므로, size/mtime 재확인을 함께 수행하고 필요 시 env 값으로 최소 age를 늘릴 수 있게 한다.
- 위험: 1초 stat 재확인 때문에 파일이 많을 때 실행 시간이 늘 수 있다.
- 대응: 기본값을 짧게 두고 `DATA_MOVEMENT_LOAD_LIMIT`로 batch 크기를 제한할 수 있게 기존 옵션을 유지한다.

## 진행 기록
- 2026-06-22: 송신 측 rename 강제 불가 조건을 반영해 수신 측 readiness 가드를 추가하기로 결정했다.
- 2026-06-22: 공통 `list_incoming_files` 경로에 60초 age 필터와 1초 size/mtime 재확인을 추가하고 관련 설정/문서를 갱신했다.
- 2026-06-22: `DataMovementFileLoaderTests`, `manage.py check`, `compileall` 검증이 통과했다. `api.data_movement` 전체 테스트는 테스트 DB migration 중 `gin_trgm_ops` 확장 부재로 실행 전 실패했다.
