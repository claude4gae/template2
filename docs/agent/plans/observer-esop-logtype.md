# ExecPlan: Observer ESOP 명칭 통일

## 목표
- observer의 ESOP 로그 기능에서 사용자 표시명, API 응답, API route, 프론트 내부 타입 키를 `ESOP`로 통일한다.

## 현재 상태
- 실제 데이터 원천은 기본 DB의 `drone_sop` 테이블이다.
- `DRONE_CTTTM_BASE_URL`, `api.drone` 등은 observer 외부 운영/도메인 계약이다.

## 범위
- 수정할 영역: observer ESOP selector 응답값, 관련 selector 테스트, observer 프론트 타입 키/컴포넌트/훅/라벨, observer 문서.
- 수정하지 않을 영역: DB schema, `drone_sop` 물리 테이블명, `api.drone` 도메인명, `DRONE_*` env 계약, auth/env 계약.

## 설계
- API 응답의 `logType`은 `ESOP`로 반환한다.
- API route는 `/logs/esop`를 사용한다.
- 프론트 타입 키, 필터 키, observer group, legend key는 `ESOP`를 사용한다.
- migration/env/auth 변경은 없다.

## 실행 단계
- [x] API selector `logType` 변경
- [x] selector 테스트 추가
- [x] API route/log key를 `esop`로 변경
- [x] 프론트 필터/상세/배지/Observer 키를 `ESOP`로 정리
- [x] ESOP 상세의 Lot ID/EQP-CB 표시 반영
- [x] 관련 검증 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.observer`
- `npm run agent:audit:api-boundary`
- `npm run agent:audit:web-boundary`
- `npm run agent:audit:ui`

## 위험과 대응
- 위험: 기존 `/logs/drone` 호출자가 있으면 route 변경으로 깨질 수 있다.
- 대응: 사용자 요청에 맞춰 observer의 공개 route를 `/logs/esop`로 통일했다. 외부 호출자 호환이 필요하면 별도 alias 추가를 검토한다.

## 진행 기록
- 2026-06-19: API 응답과 사용자 표시명을 `ESOP`로 맞췄다.
- 2026-06-19: API/web boundary audit은 통과했다. UI audit은 기존 pm-comparison/l3-spider 후보로 실패했다. Django test는 기존 test DB extension 문제로 실행되지 않아 selector smoke check로 `ESOP` 반환을 확인했다.
- 2026-06-19: ESOP 상세 표시용 `lotId`, `eqpCb` 응답 필드를 추가하고 상세 패널의 `Sample Type`/`EQP` 표시를 `Lot ID`/`EQP-CB`로 바꿨다. Selector smoke check로 `ESOP LOT-1 EQP-ALPHA-1` 반환을 확인했다.
- 2026-06-19: 사용자 혼동 방지를 위해 observer 내부 API route/log key/frontend key를 `ESOP`로 통일했다. 물리 테이블명과 외부 env 계약명은 유지했다.
- 2026-06-19: `npm run web:build`와 `/api/v1/observer/logs/esop` reverse smoke check가 통과했다. docs inventory audit은 `logs/esop`는 통과했지만 기존 app-access/seed_dummy_emails inventory 누락으로 실패했다. `npm run web:lint`는 기존 `portalNavigation.js` unused import와 pm-comparison hook dependency warning으로 실패했다.
- 2026-06-19: ESOP 상세 하단에 defect map 링크 목록을 추가했다. `defect_url`은 `defectMaps` 응답으로 정규화하고, 값이 없으면 UI에서 렌더링하지 않는다. `npm run web:build`, api/web boundary audit, selector smoke check가 통과했다.
