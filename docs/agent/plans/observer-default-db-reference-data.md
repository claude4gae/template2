# ExecPlan: observer default DB reference data

## 목표
- Observer 기준정보와 timeline 조회가 외부 `observer` DB 없이 기본 DB만 사용하게 한다.
- line/SDWT/PRC/equipment/equipment-info 조회를 `mes_line_mapping_info`, `station_master` 기준으로 전환한다.

## 현재 상태
- `api.observer.selectors`의 line/SDWT/PRC/equipment/equipment-info는 기본 DB 조회로 전환 대상이다.
- timeline 로그 중 EQP/TIP/CTTTM/RACB/ESOP는 기본 DB 또는 data movement selector 기준으로 전환되어 있다.
- `mes_line_mapping_info`와 `station_master`는 `api.data_movement` 앱의 기본 DB 테이블이다.
- `mes_line_mapping_info` model/spec는 사용자 제공 `MES_LINE_MAPPING_INFO` DDL 기준으로 `gbm_name`, `use_yn`, `del_yn`을 포함한다.

## 범위
- 수정: `apps/api/api/observer/selectors.py`, observer selector tests, `apps/api/config/settings.py`, `env/api.common.env`, observer/backend/configuration/data-model docs.
- 수정하지 않음: frontend API contract, DB schema/migration, data movement loader 구조.

## 설계
- line 목록은 `mes_line_mapping_info`에서 `gbm_name='MEMORY'`, `use_yn='Y'`, `del_yn='N'` 조건의 `gpm_line_name`을 `id/name`으로 반환한다.
- SDWT 목록은 선택한 `gpm_line_name`의 `msg_line_id`를 `station_master.floor_line_id`와 연결해 `sdwt_prod` distinct를 반환한다.
- PRC group 목록은 `station_master.sdwt_prod` 기준으로 `prc_group` distinct를 반환한다.
- equipment 목록은 `station_master.prc_group` 기준으로 `station`을 반환하며, line/SDWT가 있으면 함께 제한한다.
- equipment-info는 `station_master.station` 기준으로 찾아 `floor_line_id -> mes_line_mapping_info.msg_line_id -> gpm_line_name`을 `lineId`로 반환한다.
- `OBSERVER_DB_*`는 runtime 조회에서 제거하고 기본 DB만 사용한다.

## 실행 단계
- [x] 현재 모델 컬럼과 프론트 사용처 확인
- [x] observer 기준정보 selector를 default DB SQL로 전환
- [x] observer tests를 새 SQL source/매핑에 맞게 갱신
- [x] 외부 observer DB 설정과 문서 정리
- [x] 테스트, migration check, backend boundary audit 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.observer --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `npm run agent:audit:api-boundary`
- `git diff --check`

## 위험과 대응
- 위험: `gpm_line_name`이 중복이면 line 선택값이 여러 `msg_line_id`로 확장된다.
- 대응: SDWT 조회에서 선택 line의 모든 `msg_line_id`를 join 대상으로 사용한다.
- 위험: station 이름 컬럼 표시 기준이 불명확하다.
- 대응: 기존 API shape를 유지해 `id=station`, `name=station`으로 반환한다.

## 진행 기록
- 2026-06-20: 사용자 확인에 따라 `lineId`를 `mes_line_mapping_info.gpm_line_name` 기준으로 정하고 기본 DB 전환 계획을 작성했다.
- 2026-06-20: observer 기준정보 selector를 기본 DB `mes_line_mapping_info`/`station_master` 기준으로 전환하고 `OBSERVER_DB_*` 설정/문서를 제거했다.
- 2026-06-20: `api.observer` 테스트, migration dry-run, backend boundary audit, docs audit, diff whitespace 검증이 통과했다.
- 2026-06-20: 정정된 `MES_LINE_MAPPING_INFO` DDL에 맞춰 매핑 테이블 명칭과 스키마를 `mes_line_mapping_info`로 정리했다.
