# ExecPlan: MI TIP update history 내부 테이블 전환

## 목표
- `MI_TIP_UPDATE_HIST` 원천 파일을 Django 기본 DB의 `mi_tip_update_hist` 테이블에 적재한다.
- 적재 전 `eqp_id`가 `E/e`로 시작하지 않는 row를 제외한다.
- 적재 전 `eqp_cb`를 생성하고 `eqp_id`, `tip_chamber_id`는 대상 테이블에 저장하지 않는다.
- `tip_type/tip_chg_type/tip_level` 조합을 timeline용 `event_type` 값으로 매핑한다.
- `gpm_update_date` 기준 최근 180일 row만 유지한다.
- observer timeline TIP 조회가 기존 observer DB `gpm_tip_hist` 대신 새 내부 테이블 selector를 사용하게 한다.

## 현재 상태
- `apps/api/api/observer/selectors.py`의 `_fetch_tip_logs`는 observer DB의 `gpm_tip_hist`를 직접 조회한다.
- `eqp_status_chg`는 data movement nested app으로 기본 DB 테이블, loader, load job, command, selector를 가진다.
- data movement trigger API는 table name별 loader registry를 사용한다.

## 범위
- 수정할 영역: `api.data_movement.mi_tip_update_hist`, observer TIP selector, settings, data movement trigger registry.
- 수정하지 않을 영역: frontend timeline UI, EQP/CTTTM/RACB/ESOP selector, compose mount 구조.

## 설계
- 새 Django app: `api.data_movement.mi_tip_update_hist`.
- 물리 테이블: `mi_tip_update_hist`.
- source file pattern: `*mi_tip_update_hist*.csv.deflate`.
- 조회 인덱스: `(eqp_cb, gpm_update_date)` 및 `gpm_update_date`.
- dedupe/upsert key: `tip_event_key`.
  - 원천 테이블 DDL에 PK가 없으므로 기존 timeline stable ID와 같은 구성요소(`eqp_cb`, `gpm_update_date`, mapped `event_type`, `process_id`, `step_seq`, `ppid`, `tip_comment`)로 md5 key를 만든다.
- 적재 흐름: incoming 파일 선점 -> deflate CSV streaming -> row 필터/파생 컬럼 생성 -> temp CSV -> temp table COPY -> `ON CONFLICT (tip_event_key)` upsert -> retention purge.
- observer TIP 응답 매핑: `eventTime=gpm_update_date`, `eventType=event_type`, `operator=register_name`의 `-` 앞 부분, `comment=tip_comment`, `lineId/process/step/ppid` 유지.

## 실행 단계
- [x] 계획 문서 작성
- [x] 새 data movement app/model/migration 추가
- [x] loader/command/test 구현
- [x] settings 및 data movement trigger registry 등록
- [x] observer TIP selector 전환과 test 보강
- [x] Docker 기준 테스트와 boundary audit 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.mi_tip_update_hist api.observer --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `npm run agent:audit:api-boundary`

## 위험과 대응
- 위험: 원천 DDL에 primary key가 없어 중복 판별 기준이 모호하다.
- 대응: timeline 기존 stable ID 구성과 같은 파생 key를 unique key로 사용한다.
- 위험: `tip_chamber_id`가 `-`를 포함하거나 `MAIN`을 포함하는 경우 chamber suffix를 붙이면 기존 eqp_cb와 불일치한다.
- 대응: 사용자 제공 로직과 동일하게 해당 경우는 `eqp_id`만 저장한다.
- 위험: 이벤트 조합이 mapping에 없으면 timeline 색상/범례와 맞지 않을 수 있다.
- 대응: 사용자 제공 로직과 동일하게 `unknown`으로 저장한다.

## 진행 기록
- 2026-06-20: 사용자 요청에 따라 `MI_TIP_UPDATE_HIST`를 내부 data movement 테이블로 전환하는 설계를 시작했다.
- 2026-06-20: `api.data_movement.mi_tip_update_hist` app/model/migration/loader/command/selector/test를 추가했다.
- 2026-06-20: observer TIP selector를 `mi_tip_update_hist` selector 위임으로 전환했다.
- 2026-06-20: `airflow/dags/data_movement_file_load.py`는 owner가 `50000:root`라 Docker root 컨테이너로 임시 쓰기 권한을 열어 task를 추가했고, 권한은 `644`로 복구했다.
- 2026-06-20: `python manage.py test api.data_movement.mi_tip_update_hist api.observer --keepdb`, `python manage.py makemigrations --check --dry-run`, `npm run agent:audit:api-boundary`가 통과했다.
