# ExecPlan: Observer Rename

## 목표
- 저장소의 내부 도메인 명칭, route, env key, 문서 표기를 `observer`로 교체한다.

## 현재 상태
- Backend domain app은 `apps/api/api/observer`로 이동 대상이다.
- Frontend feature는 `apps/web/src/features/observer`로 이동 대상이다.
- Env 계약과 Django database alias를 `observer` 계열로 변경한다.
- `vis-timeline`은 외부 npm 패키지명이므로 변경 대상에서 제외한다.
- 작업 전 미커밋 변경이 `PortalNavbar.jsx`, `EsopDetail.jsx`, `Field.jsx`, `portalBranding.js`에 있다.

## 범위
- 수정할 영역: backend `api.observer`, frontend `features/observer`, route/import/env/docs/agent inventory references.
- 수정하지 않을 영역: 외부 패키지명 `vis-timeline`, lockfile의 dependency metadata, 사용자 미커밋 변경의 동작.

## 설계
- Backend app path/import/name을 `api.observer`로 변경하고 URL name prefix를 `observer-*`로 통일한다.
- Frontend feature path/import/export를 `features/observer`로 변경하고 public route를 `/observer`로 통일한다.
- Env key는 `OBSERVER_DB_*`, `OBSERVER_QUERY_DAYS`로 변경하고 문서를 동기화한다.
- UI/component 내부의 도메인성 `Observer` 명칭은 `Observer`로 바꾸되 `vis-timeline` adapter/package contract는 유지한다.

## 실행 단계
- [x] 기존 변경과 발생 위치 확인
- [x] ExecPlan 작성
- [x] 파일/폴더명 변경
- [x] 코드/문서/env 문자열 교체
- [x] import/export/API route 정합성 점검
- [x] 검증 실행

## 검증
- `npm run agent:audit:web-boundary`
- `npm run agent:audit:api-boundary`
- `npm run agent:audit:docs-inventory`
- `npm run web:build`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.observer`

## 위험과 대응
- 위험: 외부 dependency `vis-timeline`까지 바꾸면 빌드가 깨진다.
- 대응: package metadata와 import specifier는 유지하고 adapter/helper의 내부 도메인명만 교체한다.
- 위험: 기존 미커밋 변경을 덮어쓸 수 있다.
- 대응: 파일 내용을 현재 working tree 기준으로 수정하고 revert성 변경을 하지 않는다.

## 진행 기록
- 2026-06-19: 기존 도메인명 발생 위치, nested AGENTS, 기존 미커밋 변경을 확인했다.
- 2026-06-19: backend app과 frontend feature path를 `observer`로 이동하고 route/env/docs 명칭을 1차 교체했다.
- 2026-06-19: `npm run agent:audit:web-boundary`, `npm run agent:audit:api-boundary`, `npm run web:build`, `docker compose -f docker-compose.dev.yml exec -T api python manage.py check`가 통과했다.
- 2026-06-19: `npm run agent:audit:docs`는 기존 inventory 누락(app-access, app-access-stats, filter-candidates, seed_drone_dummy_data, seed_dummy_emails)으로 실패했다.
- 2026-06-19: `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.observer --keepdb`는 기존 테스트 DB의 `gin_trgm_ops` operator class 누락으로 migration 단계에서 실패했다.
