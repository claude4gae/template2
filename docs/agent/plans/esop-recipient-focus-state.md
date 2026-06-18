# ExecPlan: ESOP recipient focus state

## 목표
- `ESOP_Dashboard/settings/recipients` 페이지가 브라우저 포커스 복귀 또는 백그라운드 인증 갱신 시 선택 Target, 수신자 draft, picker 상태를 초기화하지 않도록 한다.
- 수동 새로고침과 명시적인 Target/Line 변경은 기존처럼 최신 서버 데이터를 반영한다.

## 현재 상태
- `AuthProvider`는 window focus 또는 interval refresh 때 `loadUser()`를 호출하고, 호출 시작 시 `isLoading=true`로 바꾼다.
- `RequireAuth`는 `isLoading || !user`일 때 children 대신 Loading 화면을 렌더링해 보호 라우트를 언마운트할 수 있다.
- `LineSettingsPage`는 `selectedUserSdwtProd`를 local state로만 보관하고, target 목록이 빈 배열이면 선택값을 즉시 비운다.
- recipients draft는 서버 recipients 응답이 올 때마다 local draft로 복사되어, background refetch가 미저장 draft를 덮을 수 있다.

## 범위
- 수정할 영역: `apps/web/src/features/auth/**`, `apps/web/src/features/line-dashboard/**`
- 수정하지 않을 영역: API contract, DB schema, backend permission logic, route public facade

## 설계
- 인증 갱신은 initial loading과 background refreshing을 분리한다.
- 이미 인증된 사용자가 있을 때는 background refresh 중에도 `RequireAuth` children을 유지한다.
- 수신인 설정의 선택 Target은 URL search param `target`에 저장해 재마운트에도 복원 가능하게 한다.
- target 목록이 일시적으로 비어도 기존 선택값을 유지하고, 로드 완료 후 유효하지 않을 때만 fallback을 적용한다.
- recipients draft는 dirty flag를 두어 사용자가 편집 중인 draft를 서버 refetch가 덮지 않게 한다.

## 실행 단계
- [x] AuthProvider background refresh 상태 분리
- [x] RequireAuth 렌더 조건 변경
- [x] selected Target URL 보존 및 fallback 로직 추가
- [x] recipients draft dirty guard 추가
- [x] 관련 refresh side effect 점검 및 필요한 범위만 수정
- [x] audit/test 실행

## 검증
- `npm run agent:audit:ui`
- 가능하면 관련 frontend test 또는 lint 실행
- 수동 검증: recipients 페이지에서 Target 선택 후 브라우저 focus 복귀 시 선택값과 draft가 유지되는지 확인

## 위험과 대응
- 위험: background refresh 실패 때 만료된 세션을 오래 유지할 수 있다.
- 대응: `/auth/me`가 401/403을 반환한 경우에는 기존처럼 `user=null`로 전환한다.
- 위험: URL `target`이 더 이상 존재하지 않는 Target을 가리킬 수 있다.
- 대응: target 목록 로드 완료 후 유효하지 않으면 fallback Target으로 replace한다.
- 위험: dirty guard가 서버 저장 결과 반영을 막을 수 있다.
- 대응: 저장 성공 시 dirty flag를 false로 낮추고 저장 응답을 draft에 반영한다.

## 진행 기록
- 2026-06-18: 포커스 복귀 시 초기화 원인 후보를 인증 refresh 언마운트와 recipients local state 동기화로 정리하고 계획 수립.
- 2026-06-18: 인증 background refresh, `RequireAuth` children 유지, URL `target` 복원, recipients draft dirty guard를 구현.
- 2026-06-18: `agent:audit:ui`, `agent:audit:web-boundary`, 수정 파일 ESLint, `web:build` 통과. 전체 `web:lint`는 기존 `portalNavigation.js` 미사용 import로 실패. `agent:audit:docs`는 기존 inventory/operations 누락 항목으로 실패.
