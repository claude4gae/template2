# ExecPlan: Drone Recipient Joined External Save

## 목표
- 메일/메신저 수신인 저장에서 기존 external 수신인이 active account user와 겹치는 상태 때문에 삭제/저장이 막히는 문제를 재현하고 해결한다.

## 현재 상태
- `apps/api/api/drone/services/channels/recipients.py`는 `externalKnoxIds`가 active `account_user.knox_id`와 겹치면 `external recipients must be unregistered users`를 반환한다.
- 빈 `externalKnoxIds`로 전체 삭제하는 API 케이스는 통과한다.
- 기존 external row가 stale 상태로 남아 있으면 프론트 최종 목록에 external로 포함되어 저장 검증에 걸릴 수 있다.

## 범위
- 수정할 영역: account selector, Drone 수신인 교체 서비스, Drone 수신인 테스트.
- 수정하지 않을 영역: DB schema/migration, 프론트 UI, API request/response contract, 권한 정책.

## 설계
- `externalKnoxIds` 중 active account user와 매칭되는 Knox ID는 저장 직전에 `userIds`로 흡수한다.
- 흡수된 사용자는 기존 `userIds`와 동일하게 active/contact 검증을 받는다.
- active user로 흡수되지 않은 값만 기존 external snapshot/unregistered 검증을 받는다.
- public API는 `userIds`/`externalKnoxIds` 그대로 유지한다.

## 실행 단계
- [x] 실패 재현 테스트 추가
- [x] active Knox ID → user id 해석 selector 추가
- [x] 수신인 교체 서비스에서 joined external 값을 user로 흡수
- [x] 관련 테스트 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.drone.tests.DroneSopTargetRecipientTests.test_notification_recipient_endpoint_empty_list_deletes_joined_external_recipient api.drone.tests.DroneSopTargetRecipientTests.test_replace_promotes_joined_external_payload_to_user_recipient --keepdb`
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.drone.tests.DroneSopTargetRecipientTests --keepdb`
- 기대 결과: targeted 재현 테스트와 수신인 테스트 클래스 전체가 통과한다.

## 위험과 대응
- 위험: 실제 미가입 외부 수신인을 잘못 user로 저장할 수 있다.
- 대응: active `account_user.knox_id`와 대소문자 비구분 매칭되는 값만 흡수하고, 나머지는 기존 external 검증을 유지한다.

## 진행 기록
- 2026-06-17: 빈 목록 삭제는 통과함을 확인했고, joined external payload 저장 케이스를 회귀 테스트로 고정하기로 결정했다.
- 2026-06-17: `externalKnoxIds` 중 active user와 겹치는 값을 user 수신인으로 흡수하도록 수정했고, 관련 6개 테스트 통과를 확인했다.
- 2026-06-17: `DroneSopTargetRecipientTests` 전체 45개 테스트 통과를 확인했다.
