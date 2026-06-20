# ExecPlan: station_master 파일 적재

## 목표
- `/data/data_movement/station_master/incoming/*_STATION_MASTER_*.csv.deflate` 파일을 `station_master` 테이블에 적재한다.
- 새 파일 처리 시 기존 `station_master` 데이터를 전체 삭제하고 파일 전체를 새로 적재한다.

## 현재 상태
- `api.data_movement`는 테이블별 중첩 app 구조를 사용한다.
- `mes_eqp_mapping_info`에서 전체 snapshot 교체 적재 패턴과 공통 `copy_full_replace_rows` helper가 추가되어 있다.
- Airflow DAG는 테이블별 load API를 주기 호출한다.

## 범위
- `api.data_movement.station_master` app, model, migration, loader, command, tests를 추가한다.
- settings/env/API trigger/Airflow/docs에 새 테이블을 등록한다.
- 기존 테이블 loader 동작은 변경하지 않는다.

## 설계
- Django app 경로는 물리 테이블명과 동일한 `apps/api/api/data_movement/station_master`로 둔다.
- 파일 root 기본값은 `/data/data_movement/station_master`로 둔다.
- CSV 구분자는 백틱(`)으로 지정한다.
- `number` 컬럼은 `FloatField`로 변환하고, DDL상 `varchar2(8)`인 date-like 컬럼은 문자열로 유지한다.
- loader는 transaction 안에서 temp table COPY 후 대상 테이블 전체 삭제 및 insert를 실행한다.

## 실행 단계
- [x] 기존 전체 교체 적재 패턴 확인
- [x] `station_master` app/model/migration/service/command/test 추가
- [x] settings/env/API/Airflow/docs 등록
- [x] focused test와 boundary audit 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement.station_master --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.data_movement --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run`
- `npm run agent:audit:api-boundary`
- `scripts/agent/check_docs_inventory.sh`

## 위험과 대응
- 위험: 전체 삭제 후 insert 중 실패하면 데이터가 사라질 수 있다.
- 대응: 삭제와 insert를 같은 `transaction.atomic()` 안에서 수행한다.
- 위험: Airflow data_movement task가 계속 늘어나면 API/DB 부하가 커질 수 있다.
- 대응: 운영에서는 Airflow pool 또는 worker 분리를 별도 개선으로 검토한다.

## 진행 기록
- 2026-06-20: 기존 전체 교체 적재 패턴을 재사용하는 방식으로 구현 계획을 작성했다.
- 2026-06-20: station_master app, loader, command, migration, tests, API trigger, Airflow task, env/docs를 추가했다.
- 2026-06-20: focused test, data_movement test, migration check, backend boundary audit, docs inventory 검증이 통과했다.
