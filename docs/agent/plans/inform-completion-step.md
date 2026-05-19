# ExecPlan: Inform Completion Step

## 목표
- `Process Flow`의 `Inform 완료` 라벨을 예약 종료 step이 아니라 실제 발송 성공 step에 표시한다.

## 현재 상태
- `apps/web/src/features/line-dashboard/utils/dataTableFormatters.jsx`는 완료 라벨 위치를 `inform_step || endStep`로 계산한다.
- `apps/api/api/drone/services/table_delivery.py`는 `inform_step`을 Jira 성공 delivery의 `sentStep`에서만 채운다.
- Mail/Teams 성공 처리 경로는 `sent_comment`와 `sent_at`만 저장하고 `sent_step`은 저장하지 않는다.

## 범위
- 수정할 영역: Drone SOP delivery 상태 저장, 테이블 delivery enrichment, line-dashboard Process Flow 렌더링.
- 수정하지 않을 영역: DB schema, API endpoint shape, auth/env contract, unrelated POP3/refactor 변경.

## 설계
- 성공 delivery 저장 시 현재 `metro_current_step`을 `sent_step` snapshot으로 함께 저장한다.
- 테이블 row의 `inform_step`은 visible 성공 delivery 중 실제 `sentStep`이 있는 값으로 보강한다.
- 프론트는 `inform_step` 또는 성공 delivery의 `sentStep`만 완료 라벨 위치로 사용하고 `endStep` fallback은 사용하지 않는다.
- public API/facade 영향: 기존 필드 의미 보강만 수행하며 새 필드는 추가하지 않는다.
- migration/env/auth 영향: 없음.

## 실행 단계
- [x] Backend delivery status helper에 `sent_step` 저장 경로 추가
- [x] Mail/Teams 성공 경로에서 현재 step snapshot 전달
- [x] 테이블 enrichment의 `inform_step` 선택 기준 확장
- [x] Process Flow 완료 라벨 fallback 제거 및 delivery fallback 추가
- [x] service/API regression 테스트 추가

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.drone`
- `npm run agent:audit:ui`

## 위험과 대응
- 위험: 기존 Jira 성공 경로의 `sent_step` 저장 순서가 깨질 수 있다.
- 대응: 기존 Jira 상태 테스트를 유지하고, 새 optional 인자는 기존 호출의 기본 동작을 바꾸지 않는다.
- 위험: 오래된 성공 row에 `sent_step`이 없으면 완료 라벨 위치를 확정할 수 없다.
- 대응: 잘못된 endStep fallback을 제거해 오표시를 막고, 신규 성공 row부터 정확한 step을 저장한다.

## 진행 기록
- 2026-05-19: 원인 분석 및 백엔드/프론트 보정 설계 확정.
- 2026-05-19: 구현 완료. `api.drone --keepdb` 테스트와 UI audit 통과.
