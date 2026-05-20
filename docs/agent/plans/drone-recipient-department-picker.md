# ExecPlan: Drone Recipient Department Picker

## 목표
- Drone 수신인 설정의 소속 불러오기 흐름을 `department 선택 → userSdwtProd 선택 → 사용자 불러오기`로 나눈다.
- 불러온 사용자 목록에 가입 여부, department, user_sdwt_prod 정보를 함께 표시한다.

## 현재 상태
- 수신인 picker는 `LineSettingsPage`에서 `fetchAccountUserPool`로 소속 사용자 목록을 바로 불러온다.
- 수신인 저장 구조는 `DroneSopTargetRecipient(target, channel, user/external_knox_id)`이며 department를 저장하지 않는다.
- 사용자/외부 스냅샷 응답에는 department와 userSdwtProd 표시 필드가 이미 있다.

## 범위
- 수정할 영역: account 사용자 풀 조회 필터, line-dashboard 수신인 picker UI/상태.
- 수정하지 않을 영역: Drone 수신인 저장 DB 구조, 발송 대상 해석, Target/Mapping 목록.

## 설계
- account 사용자 풀 API에 `department` 필터와 department facet 목록을 추가한다.
- line-dashboard recipient picker는 department 목록을 먼저 노출하고, 선택된 department 기준으로 userSdwtProd 후보를 좁힌다.
- 사용자가 department와 userSdwtProd를 선택한 뒤 기존 `fetchAccountUserPool` 호출로 사용자 목록을 불러온다.
- 사용자 목록 row에는 가입/외부 여부, department, userSdwtProd 메타를 표시한다.
- migration/env/auth 영향: 없음.

## 실행 단계
- [x] account 사용자 풀 필터/응답 확장
- [x] 프론트 API 정규화 확장
- [x] recipient picker 상태/핸들러 변경
- [x] picker UI 메타 표시 추가
- [x] focused regression 검증

## 검증
- `docker compose -f docker-compose.dev.yml run --rm --entrypoint "" api python manage.py test api.account api.drone --keepdb`
- `npm run agent:audit:ui`
- `npm run agent:audit:web-boundary`

## 위험과 대응
- 위험: 기존 소속 선택 사용자가 department 선택 없이 진행하지 못해 UX가 막힐 수 있다.
- 대응: department 미선택 시 명확한 안내/비활성 상태를 제공한다.
- 위험: account API 응답 계약 확장이 기존 호출에 영향을 줄 수 있다.
- 대응: 기존 필터는 선택 인자로 유지하고, 기본 호출 동작은 변경하지 않는다.

## 진행 기록
- 2026-05-19: 사용자 답변 기준으로 picker 전용 department 계층 적용 범위 확정.
- 2026-05-19: account 사용자 pool에 department facet/filter를 추가하고 recipient picker 계층 선택 UI를 적용함.
- 2026-05-19: account/drone backend 테스트와 frontend UI/boundary audit 통과.
