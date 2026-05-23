# ExecPlan: ESOP table refresh stability

## 목표
- ESOP Dashboard 테이블이 polling 또는 수동 refresh 중 page/scroll을 초기화하지 않고 기존 화면 위치를 유지한다.
- 도넛차트 refresh 동작은 이번 범위에서 변경하지 않는다.

## 현재 상태
- `useTableQuery`는 10초 polling을 수행하며 `isFetching`을 row loading 상태로 반환한다.
- `useDataTablePresentation`은 page count가 줄면 즉시 page index를 clamp한다.
- `DataTable`은 refresh 시작/완료 기준으로 scroll snapshot을 복원하지만 loading 상태가 background refresh와 초기 loading을 구분하지 않는다.

## 범위
- 수정: `apps/web/src/features/line-dashboard/hooks/useTableQuery.js`
- 수정: `apps/web/src/features/line-dashboard/hooks/useDataTable.js`
- 수정: `apps/web/src/features/line-dashboard/hooks/useDataTablePresentation.js`
- 수정: `apps/web/src/features/line-dashboard/components/DataTable.jsx`
- 제외: `StatusDistributionCard` 및 도넛차트 동작

## 설계
- React Query v5 방식의 `placeholderData: keepPreviousData`로 key 전환 중 기존 rows를 유지한다.
- 초기 loading과 background refresh를 분리해 polling refresh가 empty/loading UI로 전환되지 않게 한다.
- page clamp는 filter/sort/dataset 전환 시에만 수행하고, background refresh 완료로 rows 수가 흔들리는 경우에는 기존 page를 유지한다.
- scroll snapshot은 background refresh 시작 시 저장하고 완료 후 복원한다.
- public facade, API, DB, auth, env contract 영향은 없다.

## 실행 단계
- [x] `useTableQuery`의 query 옵션과 loading 반환값을 분리한다.
- [x] `useDataTableState`가 새 loading 상태를 전달하게 한다.
- [x] `useDataTablePresentation`의 page reset/clamp 조건을 dataset/filter/sort 전환 중심으로 조정한다.
- [x] `DataTable`의 refresh snapshot 조건을 background refresh 기준으로 맞춘다.

## 검증
- `npm run web:lint`
- `npm run agent:audit:ui`
- `git diff --check`

## 위험과 대응
- 위험: 실제 row count가 줄었을 때 현재 page가 비어 보일 수 있다.
- 대응: 사용자 필터/정렬/라인 변경에는 page clamp를 유지하고, polling refresh에만 page 유지 정책을 적용한다.

## 진행 기록
- 2026-05-23: 도넛차트 제외, 테이블 page/scroll refresh 안정화 범위로 계획 작성.
- 2026-05-23: 초기 loading과 background refresh를 분리하고 polling refresh 중 page/scroll 유지 흐름을 적용.
- 2026-05-23: `npm run web:lint`, `npm run agent:audit:ui`, `npm run web:build`, `git diff --check` 통과 확인.
