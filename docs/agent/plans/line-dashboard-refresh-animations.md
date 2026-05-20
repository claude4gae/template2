# ExecPlan: line-dashboard refresh animations

## 목표
- `row.id`를 기준으로 테이블 행 식별을 통일하고, 30초 자동 갱신 중 스크롤을 유지한다.
- 수동/자동 갱신으로 신규 row 또는 status 진행 변화가 들어오면 짧은 애니메이션으로 갱신 사실을 표시한다.

## 현재 상태
- `DataTable.jsx`는 TanStack 내부 `row.id`를 렌더 key로 사용한다.
- 편집/재시도 로직은 API record id로 원본 row의 `id`를 사용한다.
- `useTableQuery.js`에는 자동 refetch interval이 없다.

## 범위
- 수정 대상은 `line-dashboard` 테이블 쿼리, 테이블 렌더링, status cell 표시로 제한한다.
- API contract, backend, public facade, 라우팅은 변경하지 않는다.
- 기존 staged 변경은 보존한다.

## 설계
- `getRecordId(row)`를 `useReactTable.getRowId`에 연결해 렌더/비교 기준을 `row.id`로 통일한다.
- `useQuery`에 `refetchInterval: 30_000`을 추가해 같은 queryKey를 주기적으로 갱신한다.
- `lineId`, `lineFilterMode`, 최근시간 필터가 바뀌면 새 데이터셋으로 보고 스크롤/애니메이션 snapshot을 초기화한다.
- 수동 Refresh 또는 같은 데이터셋의 자동 refetch만 이전 rows snapshot과 비교해 신규 row/status 진행 변화를 표시한다.
- `prefers-reduced-motion` 환경에서는 강조 애니메이션을 최소화한다.

## 실행 단계
- [x] `useTableQuery.js`에 30초 자동 refetch를 추가한다.
- [x] `DataTable.jsx`에 stable row id, refresh snapshot, 스크롤 복원, row animation 상태를 추가한다.
- [x] `DataTableColumnRenderers.jsx` status cell에 변경 highlight 입력을 연결한다.
- [x] 관련 lint/audit 또는 targeted check를 실행한다.

## 검증
- `npm run agent:audit:ui`
- `npm run agent:audit:web-boundary`

## 위험과 대응
- 위험: queryKey 변경 refetch에도 이전 스크롤/애니메이션이 적용될 수 있다.
- 대응: 데이터셋 key 변경 시 pending snapshot과 animation 상태를 초기화한다.
- 위험: staged 사용자 변경과 충돌할 수 있다.
- 대응: 기존 변경을 유지하고 필요한 line-dashboard 영역만 patch한다.

## 진행 기록
- 2026-05-21: `row.id` 기준 자동 refetch/애니메이션 설계를 문서화했다.
- 2026-05-21: 30초 자동 refetch, scroll snapshot 복원, 신규 row/status 변경 animation을 구현했다.
- 2026-05-21: `npm run web:lint -- --quiet`, `npm run agent:audit:ui`, `npm run agent:audit:web-boundary`, `git diff --check` 통과를 확인했다.
