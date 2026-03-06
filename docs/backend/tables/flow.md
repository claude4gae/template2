# Line Dashboard Tables 백엔드 문서

## 개요
- `tables` 도메인은 `drone` 도메인으로 통합되었습니다.
- 라인 대시보드에서 지정 테이블을 조회/부분 업데이트하는 API를 제공합니다.

## 엔드포인트
- `GET /api/v1/line-dashboard/tables`
- `PATCH /api/v1/line-dashboard/tables/update`

## 핵심 구성 요소
- `apps/api/api/drone/views.py`의 `DroneTablesView`, `DroneTableUpdateView`
- `apps/api/api/drone/services/table_ops.py`
- `apps/api/api/drone/services/table_schema.py` (테이블 정규화/스키마/필터 보조)
- `apps/api/api/drone/selectors.py` (라인 히스토리 집계/조회 보조)

## 주요 규칙/정책
- 기본 테이블: `DEFAULT_TABLE = drone_sop`
- 식별자 검증: `sanitize_identifier`
- 업데이트 허용 컬럼: `comment`, `needtosend`, `instant_inform`, `status`
- 조회 응답은 DB 원본 컬럼명만 반환하며, 레거시 camelCase 별칭은 제공하지 않음

## 주요 흐름

### 1) 테이블 조회
`GET /api/v1/line-dashboard/tables`
1. `resolve_table_schema`로 테이블/컬럼/타임스탬프 컬럼 확인
2. `lineId`, `from/to`, `recentHours` 조건 조합
3. raw SQL 조회 결과 반환

### 2) 테이블 부분 업데이트
`PATCH /api/v1/line-dashboard/tables/update`
1. JSON 파싱 → `table`, `id`, `updates` 검증
2. 테이블 컬럼 조회 후 허용 컬럼만 UPDATE 대상 선택
3. UPDATE 후 변경 전/후 row 조회
4. ActivityLog에 변경 내용 기록

## 관련 코드 경로
- `apps/api/api/drone/urls.py`
- `apps/api/api/drone/views.py`
- `apps/api/api/drone/services/table_ops.py`
- `apps/api/api/drone/selectors.py`
- `apps/api/api/drone/tests.py`
