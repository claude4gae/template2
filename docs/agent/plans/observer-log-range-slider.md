# ExecPlan: Observer Log Range Slider

## 목표
- Observer Log Viewer 헤더에 최근 로그 조회 기간 slider를 추가한다.
- 기본 조회 기간은 7일, 최대 조회 기간은 90일로 제한한다.
- 선택 기간을 기존 observer 로그 API의 `from`/`to` query에 반영한다.
- 양쪽 thumb로 최근 90일 안의 특정 구간만 조회할 수 있게 한다.

## 현재 상태
- `apps/web/src/features/observer/hooks/useObserverLogs.js`는 `logQueryOptions`를 받을 수 있다.
- `apps/api/api/observer/views.py`는 `from`/`to` 날짜 query를 이미 파싱한다.
- `apps/web/src/features/observer/components/LogViewerSection.jsx` 헤더 오른쪽에는 EQPID 직접 조회 토글이 있다.

## 범위
- 수정할 영역: `apps/web/src/features/observer` 내부 UI, 상태, 날짜 query option 유틸.
- 수정하지 않을 영역: backend API contract, DB schema/index, auth/env 설정.

## 설계
- page state에서 `logRange`를 `{ startDaysAgo, endDaysAgo }` 형태로 관리한다.
- 선택 상대 구간으로 `from`/`to` 날짜 문자열을 생성해 `useObserverLogs`에 전달한다.
- slider는 shadcn `Slider`를 사용하고 기존 Log Viewer 헤더 컨트롤과 함께 배치한다.
- public facade 영향은 없다.
- migration/env/auth 영향은 없다.

## 실행 단계
- [x] 날짜 범위 상수와 query option 생성 유틸을 추가한다.
- [x] Log Viewer 헤더 slider 컴포넌트를 추가한다.
- [x] page state와 `useObserverLogs` 호출을 연결한다.
- [x] 나머지 병목 후보를 코드 기준으로 점검한다.
- [x] 단일 thumb 기간 선택을 양쪽 thumb 구간 선택으로 확장한다.

## 검증
- `npm run agent:audit:ui`
- `npm run agent:audit:web-boundary`
- 가능하면 관련 frontend lint/build 또는 테스트 명령을 확인한다.

## 위험과 대응
- 위험: slider 변경마다 API 요청이 과도하게 발생할 수 있다.
- 대응: slider drag 중 로컬 표시만 갱신하고 commit 시 query 기간을 반영한다.
- 위험: 날짜 포함 범위 해석이 사용자 기대와 다를 수 있다.
- 대응: 선택 일수를 오늘 포함 N일 범위로 명시하고 label에 기간을 표시한다.

## 진행 기록
- 2026-06-19: 기본 7일/최대 90일 slider를 기존 observer 로그 query option에 연결하는 계획을 작성했다.
- 2026-06-19: slider UI, 날짜 query option 연결, 변경 파일 eslint, frontend build 검증을 완료했다.
- 2026-06-19: 양쪽 thumb로 `-90 days`부터 `-1 day` 사이 특정 구간을 선택하도록 확장했다.
