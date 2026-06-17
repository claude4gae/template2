# ExecPlan: App Access Stats Dashboard

## 목표
- 슈퍼유저가 앱별 접속횟수를 KST 기준으로 확인할 수 있는 관리자 대시보드를 제공한다.
- 기존 `ActivityLog`를 이벤트 로그로 사용해 별도 테이블 없이 앱 접속 이벤트를 기록하고 집계한다.

## 현재 상태
- `api.activity` 도메인에 `ActivityLog` 모델, 최근 로그 조회 API, 서비스/셀렉터 구조가 있다.
- 프론트엔드는 `apps/web/src/features/<feature>` 단위 라우트 파사드 구조를 사용한다.
- 전역 라우터는 feature routes를 `protectedFeatureRoutes`에 합쳐 보호 라우트로 노출한다.

## 범위
- 수정할 영역: `api.activity`의 selector/service/view/url/test, React access-stats feature, 전역 route/navigation, 앱 접속 tracker.
- 수정하지 않을 영역: 새 DB 테이블, 기존 앱스토어/업무 기능 동작, CSV 다운로드.

## 설계
- `POST /api/v1/activity/app-access`가 로그인 사용자 화면 진입을 `ActivityLog(action="APP_ACCESS")`로 기록한다.
- `GET /api/v1/activity/app-access-stats`가 KST 날짜 범위를 UTC boundary로 변환하고 `APP_ACCESS` 이벤트를 앱별로 집계한다.
- 통계 조회 API는 `request.user.is_superuser`만 허용한다.
- 프론트는 라우트 변경 시 known app route를 판별해 앱 접속 이벤트를 기록한다.
- `access-stats` feature는 KPI, 앱별 추이 차트, 앱 순위, 상세 테이블을 제공한다.
- migration/env 변경은 없다.

## 실행 단계
- [x] activity selector/service/view/url/test 추가
- [x] access-stats React feature 추가
- [x] 전역 라우트와 슈퍼유저 내비게이션 연결
- [x] 앱 접속 tracker 연결
- [x] 백엔드/프론트 검증 실행

## 검증
- [x] `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.activity --keepdb`
- [x] `npm --prefix apps/web run lint`
- [x] `npm --prefix apps/web run build`
- [x] `scripts/agent/check_ui_consistency.sh`
- [x] `scripts/agent/check_frontend_boundaries.sh`

## 위험과 대응
- 위험: 기존 API 요청 로그를 접속수로 세면 여러 API 호출 때문에 수치가 부풀 수 있다.
- 대응: 전용 `APP_ACCESS` 이벤트만 집계한다.
- 위험: 기록 API 호출 자체가 미들웨어에 의해 별도 로그로 남는다.
- 대응: 통계 집계는 `APP_ACCESS` action만 대상으로 삼아 중복을 배제한다.

## 진행 기록
- 2026-06-17: 기존 `ActivityLog` 기반으로 앱 접속 이벤트 기록/집계 설계를 확정했다.
- 2026-06-17: 백엔드 APP_ACCESS 기록/집계 API와 React 접속 현황 대시보드/트래커를 추가했다.
- 2026-06-17: activity 테스트, web lint/build, UI/경계 audit 검증을 완료했다.
