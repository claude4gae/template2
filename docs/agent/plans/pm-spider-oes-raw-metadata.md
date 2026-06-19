# ExecPlan: PM Spider OES Raw Metadata

## 목표
- DASHBOARD_SPEC plain OES raw 파일이 score step과 매칭되어 상세 heatmap/line chart를 생성한다.
- OES wide schema(`Time`, wavelength 컬럼들)에서 `날짜`, `rcp_step`, `wavelength`, `value`가 안정적으로 생성된다.

## 현재 상태
- score 파일은 읽히며 step `4d`, wavelength 후보가 반환된다.
- raw 파일은 발견되지만 OES 상세 plot 필수 컬럼이 부족해 heatmap이 `0 x 0`으로 떨어진다.
- 관련 모듈은 `apps/api/api/pm_comparison/selectors.py`, `apps/api/api/pm_comparison/services/__init__.py`, `apps/api/api/pm_comparison/tests.py`다.

## 범위
- plain OES raw 경로와 `#` filename metadata 보강.
- plain dt 폴더가 날짜+시각 형태일 때 raw file glob 매칭 보강.
- 회귀 테스트 추가.
- frontend, DB schema, env/auth contract는 수정하지 않는다.

## 설계
- 파일 경로 `BASE_DATA/{LINE_ID}/{EQP_ID}/{CHAMBER_ID}/{PM_START}/oes/{TYPE}/{STEP_SEQ}/{PPID}/{RECIPE_ID}/{LOT_ID}/{SLOT_NO}/{file}`에서 기본 메타를 읽는다.
- filename `{line_id}#{process_id}#{step_seq}#{rcp_step}#{ppid}#{recipe_id}#{eqp_id}#{chamber_id}#{lot_id}#{slot_no}#{wafer_end_time}.parquet` 값이 있으면 우선 보강한다.
- wide OES의 `Time` 컬럼은 `traj_phase`로 사용해 heatmap y축과 상세 차트 x축을 구성한다.
- public API 필드명은 유지한다.

## 실행 단계
- [x] plain raw file selector의 날짜+시각 dt 매칭 보강
- [x] OES path/filename metadata를 raw frame에 보강
- [x] DASHBOARD_SPEC OES wide layout 회귀 테스트 추가
- [x] py_compile, Django 테스트, diff 검증 실행

## 검증
- `python3 -m py_compile apps/api/api/pm_comparison/services/__init__.py apps/api/api/pm_comparison/selectors.py apps/api/api/pm_comparison/tests.py`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.pm_comparison`
- `git diff --check`

## 위험과 대응
- 위험: 기존 Hive partition layout 동작이 깨질 수 있다.
- 대응: 기존 `parse_partition_values` 결과를 유지하고 plain OES 보강은 누락 컬럼 중심으로만 적용한다.
- 위험: raw `rcp_step`과 score `step` 대소문자가 다르면 필터 후 0건이 될 수 있다.
- 대응: 이번 변경 후에도 row가 0이면 디버그 메시지에서 raw 후보 step 값을 확인해 별도 정규화 여부를 판단한다.

## 진행 기록
- 2026-06-19: score는 존재하지만 OES raw 상세 필수 컬럼이 빠지는 현상을 기준으로 수정 범위를 확정했다.
- 2026-06-19: plain OES path/filename metadata 보강과 wide schema 회귀 테스트를 추가했다.
- 2026-06-19: `py_compile`, `api.pm_comparison` 테스트, backend boundary audit, diff whitespace 검증이 통과했다.
