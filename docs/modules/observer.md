# Observer 모듈

Observer는 설비 Observer 화면에 필요한 기준 정보와 로그를 조회합니다.

## 기능 요약

- 라인 목록 조회
- 라인별 SDWT 조회
- 공정 그룹 조회
- 설비 목록/상세 조회
- 설비별 통합 로그 조회
- EQP, TIP, CTTTM, RACB, ESOP 유형별 로그 조회
- URL의 `eqpId`를 기준으로 설비 상세와 observer item 동기화

## 화면과 route

| Route | 설명 |
| --- | --- |
| `/observer` | 라인/SDWT/공정/설비를 선택해 observer 조회 |
| `/observer/:eqpId` | 특정 설비를 URL에서 바로 선택 |

프론트 feature는 `apps/web/src/features/observer`이며, 외부 공개는 `apps/web/src/features/observer/index.js`의 `observerRoutes`입니다.

## 데이터 소스

대부분 observer 전용 PostgreSQL DB를 조회합니다. 일부 ESOP 관련 로그는 기본 DB를 함께 사용할 수 있습니다.

| 데이터 | Backend source | 설명 |
| --- | --- | --- |
| Line | observer DB | 선택 가능한 line 목록 |
| SDWT | observer DB | line별 SDWT 목록 |
| Process group | observer DB | line/SDWT별 공정 그룹 |
| Equipment | observer DB | 설비 목록과 상세 |
| EQP/TIP/CTTTM/RACB log | observer DB | 유형별 설비 로그 |
| ESOP log | 기본 DB 또는 observer 연계 | ESOP 관련 로그 |

## 조회 흐름

1. 요청 query를 정리합니다.
2. `lineId`, `sdwtId`, `prcGroup` 등 식별자를 대문자로 정규화합니다.
3. 필수 query가 없으면 400을 반환합니다.
4. `from`, `to`, `limit` 로그 옵션을 검증합니다.
5. observer DB 또는 ESOP 데이터를 조회합니다.
6. 프론트가 사용하기 쉬운 형태로 반환합니다.

## 로그 조회 정책

| 항목 | 정책 |
| --- | --- |
| 기본 기간 | `from` 생략 시 `OBSERVER_QUERY_DAYS` 기준 최근 기간 |
| 현재 기본값 | 90일 |
| 최대 limit | 5000 |
| 날짜 형식 | `YYYY-MM-DD` 또는 datetime 문자열 |
| 정렬/변환 | backend selector가 유형별 raw row를 공통 payload로 변환 |

## 프론트 구조

| 경로 | 역할 |
| --- | --- |
| `apps/web/src/features/observer/pages/ObserverPage.jsx` | observer route page |
| `apps/web/src/features/observer/api/observerApi.js` | backend API 호출 |
| `apps/web/src/features/observer/hooks/useObserverLogs.js` | 로그 query orchestration |
| `apps/web/src/features/observer/hooks/useObserverLogQuery.js` | 유형별 로그 query 공통화 |
| `apps/web/src/features/observer/store/useObserverStore.js` | 선택/필터 UI 상태 |
| `apps/web/src/features/observer/utils/visObserverItems.js` | vis-timeline item 변환 |
| `apps/web/src/features/observer/components/*Detail.jsx` | 로그 유형별 상세 패널 |

## 운영 포인트

- observer DB 접속 문제는 `/api/v1/observer/lines` 같은 기준 정보 API부터 확인합니다.
- 기본 조회 기간은 `OBSERVER_QUERY_DAYS`로 조정합니다.
- 화면이 느리면 로그 API의 `from`, `to`, `limit` 조합과 응답 건수를 먼저 확인합니다.
- ESOP 로그가 누락되면 `api.drone` 데이터와 observer 로그 결합 지점을 함께 확인합니다.

## 관련 API

- `docs/api/observer.md`
- `docs/inventory.md`
- `docs/configuration.md`
- `docs/data-model.md`

## 관련 코드

- `apps/api/api/observer/views.py`
- `apps/api/api/observer/selectors.py`
- `apps/web/src/features/observer`
