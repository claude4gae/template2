# ExecPlan: FDC Trend UI

## 목표
- 라인 탭, 분임조 탭, 스텝별 이상 Trend 리스트, scatter chart 상세를 한 화면에서 탐색하는 React UI를 구현한다.

## 현재 상태
- `apps/web/src/features/*`는 feature별 `routes.jsx`와 `index.js` public facade를 사용한다.
- 업무형 화면은 Tailwind/shadcn 토큰과 `AppShellLayout`/`LineDashboardShell` 패턴을 따른다.
- FDC Trend용 API/DB 계약은 아직 확인되지 않았다.

## 범위
- 수정할 영역: `apps/web/src/features/fdc-trend`, 전역 라우터, navigation config, 기존 shell의 선택 layout prop.
- 수정하지 않을 영역: backend API, DB schema, auth/permission, 기존 Line Dashboard 동작.

## 설계
- `features/fdc-trend`를 새 public route feature로 만든다.
- route는 기존 `LineDashboardShell` facade를 재사용해 같은 앱 shell 안에 표시한다.
- 화면 데이터는 `utils/fdcTrendMockData.js`에 두고, page는 line/team/step 선택 상태와 시각화만 담당한다.
- scatter chart는 기존 의존성인 `recharts`와 `components/ui/chart` wrapper를 사용한다.
- API/env/auth contract 변경은 없다.

## 실행 단계
- [x] FDC Trend mock data와 selector 유틸 작성
- [x] FDC Trend page 구현
- [x] feature route/facade 추가
- [x] 전역 route와 navigation에 연결
- [x] lint/audit 검증

## 검증
- `npm run lint --workspace apps/web` 또는 repo에서 지원하는 web lint 명령을 실행한다.
- 가능하면 `npm run agent:audit:ui`, `npm run agent:audit:web-boundary`를 실행한다.

## 위험과 대응
- 위험: 실제 API 계약이 없어 데이터 필드명이 나중에 바뀔 수 있다.
- 대응: mock data와 selector를 page에서 분리해 교체 범위를 줄인다.

## 진행 기록
- 2026-05-28: FDC Trend UI 구현 계획 작성.
- 2026-05-28: `features/fdc-trend` 화면, route/facade, navigation 연결 추가.
- 2026-05-28: 의존성 설치 후 `web:lint`, `web:build`, `agent:audit:web-boundary`, `agent:audit:ui` 통과. `recharts` build resolve를 위해 누락된 `react-is` dependency를 추가.
