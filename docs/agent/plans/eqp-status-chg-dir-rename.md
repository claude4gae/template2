# ExecPlan: eqp_status_chg 디렉터리명 변경

## 목표
- `eqp_status_chg` 데이터 디렉터리 계약을 `data/data_movement/m_eqp_status_chg`로 변경한다.

## 현재 상태
- API 컨테이너의 data movement root는 `/data/data_movement`로 mount된다.
- `eqp_status_chg` loader의 테이블명, Django app 이름, API endpoint는 `eqp_status_chg`를 사용한다.
- 파일명 패턴은 이미 `*m_eqp_status_chg*.csv.deflate`를 사용한다.

## 범위
- 수정할 영역: Django settings 기본값, 공통 env, data movement 문서, 로컬 data 디렉터리명.
- 수정하지 않을 영역: DB 테이블명, Django app/module 경로, management command, API endpoint, Airflow task/table name.

## 설계
- `DATA_MOVEMENT_EQP_STATUS_CHG_DIR` 값만 `/data/data_movement/m_eqp_status_chg`로 변경한다.
- host mount root인 `DATA_MOVEMENT_HOST_PATH`는 유지하고, 하위 테이블 디렉터리만 rename한다.
- API/DB/auth contract 변경은 없고 env file path contract만 변경된다.

## 실행 단계
- [x] ExecPlan 작성
- [x] settings/env/docs의 eqp_status_chg 디렉터리 경로를 m_eqp_status_chg로 변경
- [x] 로컬 eqp_status_chg 데이터 디렉터리를 `data/data_movement/m_eqp_status_chg`로 rename
- [x] 경로 참조 검색과 문서 audit 실행

## 검증
- `rg`로 기존 eqp_status_chg 데이터 디렉터리 경로 참조가 남지 않았는지 확인한다.
- `npm run agent:audit:docs`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py check`

## 위험과 대응
- 위험: `eqp_status_chg` 테이블명까지 바꾸면 API endpoint와 DB contract가 깨질 수 있다.
- 대응: 디렉터리 경로만 변경하고 테이블/app/endpoint 이름은 유지한다.

## 진행 기록
- 2026-06-20: `eqp_status_chg` 데이터 디렉터리명을 `m_eqp_status_chg`로 변경하기로 범위를 확정했다.
- 2026-06-20: settings/env/docs 경로를 변경하고 로컬 data 디렉터리를 rename했다. 이전 경로 검색, 문서 audit, Django system check가 통과했다.
