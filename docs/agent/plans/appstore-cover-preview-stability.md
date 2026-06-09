# ExecPlan: AppStore Cover Preview Stability

## 목표
- AppStore 카드 미리보기 스크린샷이 새로고침 때 `/cover` 요청 지연/취소로 간헐적으로 깨지는 현상을 줄인다.

## 현재 상태
- 목록 API는 base64 커버 이미지를 `/api/v1/appstore/apps/<id>/cover` 절대 URL로 내려준다.
- 커버 엔드포인트 응답에는 명시적 캐시 헤더가 없다.
- 프론트 카드 이미지는 실패 시 짧게 재시도하지만, 새로고침 때마다 모든 커버 요청이 다시 몰릴 수 있다.

## 범위
- 수정 대상: `api.appstore` 목록/커버 응답, AppStore 카드 이미지 URL 처리.
- 제외: DB schema, migration, auth/permission, 앱 등록/수정 contract 변경.

## 설계
- 목록 API의 `screenshotUrl`에 `updated_at` 기반 `v` query를 붙여 이미지 변경 시 캐시가 자연스럽게 무효화되게 한다.
- 커버 이미지 바이너리 응답에 `Cache-Control`과 `ETag`를 설정해 새로고침 시 재다운로드를 줄인다.
- 프론트 재시도 URL 생성은 기존 `v` query를 유지하고 `_retry`만 추가한다.

## 실행 단계
- [x] 커버 URL 생성에 version query 추가
- [x] 커버 응답 캐시 헤더 추가
- [x] 관련 테스트 업데이트
- [x] lint/test/audit 검증

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.appstore`
- `npm --workspace web run lint -- src/features/appstore/components/AppList.jsx src/features/appstore/pages/AppstorePage.jsx src/features/appstore/components/AppDetail.jsx`
- `npm run agent:audit:ui`

## 위험과 대응
- 위험: 이미지 수정 후 오래된 캐시가 보일 수 있다.
- 대응: `updated_at` 기반 `v` query로 앱 수정 시 URL을 바꾼다.

## 진행 기록
- 2026-06-09: 간헐적 `/cover` 실패 대응을 위한 캐시/버전 URL 설계 작성.
- 2026-06-09: 커버 URL 버전 query와 커버 응답 Cache-Control/ETag를 추가하고 테스트를 갱신.
- 2026-06-09: AppStore backend test, frontend lint, UI audit 검증 완료.
