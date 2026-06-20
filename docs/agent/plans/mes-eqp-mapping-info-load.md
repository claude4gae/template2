# ExecPlan: mes_eqp_mapping_info 파일 적재

## 목표
- `/data/data_movement/mes_line_mapping_info/incoming/*_MES_MAPPING_INFO_*.csv.deflate` 파일을 `mes_eqp_mapping_info` 테이블에 적재한다.
- 새 파일 처리 시 기존 `mes_eqp_mapping_info` 데이터를 전체 삭제하고 파일 전체를 새로 적재한다.

## 현재 상태
- `api.data_movement`는 테이블별 중첩 app 구조를 사용한다.
- 공통 deflate CSV 파서와 PostgreSQL COPY helper가 있다.
- 기존 helper는 기준 컬럼 단위 부분 교체만 지원한다.
- Airflow DAG는 테이블별 load API를 주기 호출한다.

## 범위
- `api.data_movement.mes_eqp_mapping_info` app, model, migration, loader, command, tests를 추가한다.
- 공통 PostgreSQL COPY helper에 전체 교체 적재 함수를 추가한다.
- settings/env/API trigger/Airflow/docs에 새 테이블을 등록한다.
- 기존 테이블 loader 동작은 변경하지 않는다.

## 설계
- Django app 경로는 물리 테이블명과 동일한 `apps/api/api/data_movement/mes_eqp_mapping_info`로 둔다.
- 파일 root 기본값은 사용자 지정 경로인 `/data/data_movement/mes_line_mapping_info`로 둔다.
- CSV 구분자는 백틱(`)으로 지정한다.
- 날짜 컬럼은 `insert_date`, `update_date`, 숫자 컬럼은 `fdc_eqp_index_no`, `fdc_unit_index_no`로 변환한다.
- loader는 transaction 안에서 temp table COPY 후 대상 테이블 전체 삭제 및 insert를 실행한다.

## 실행 단계
- [x] 기존 data_movement loader와 공통 helper 패턴 확인
- [x] 전체 교체 COPY helper 추가
- [x] `mes_eqp_mapping_info` app/model/migration/service/command/test 추가
- [x] settings/env/API/Airflow/docs 등록
- [x] focused test와 boundary audit 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.mes_eqp_mapping_info --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement --keepdb`
- `npm run agent:audit:api-boundary`

## 위험과 대응
- 위험: 원천 파일 경로명과 테이블명이 다르다.
- 대응: app/table은 `mes_eqp_mapping_info`, 기본 파일 root는 `/data/data_movement/mes_line_mapping_info`로 분리해 문서화한다.
- 위험: 전체 삭제 후 insert 중 실패하면 데이터가 사라질 수 있다.
- 대응: 삭제와 insert를 같은 `transaction.atomic()` 안에서 수행한다.

## 진행 기록
- 2026-06-20: 기존 data_movement 구조와 전체 교체 요구사항을 확인하고 구현 계획을 작성했다.
- 2026-06-20: mes_eqp_mapping_info app, 전체 교체 COPY helper, command, API trigger, Airflow task, env/docs를 추가했다.
- 2026-06-20: focused test, data_movement test, migration check, backend boundary audit, docs inventory 검증이 통과했다.
