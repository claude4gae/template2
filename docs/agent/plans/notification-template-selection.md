# ExecPlan: Notification Template Selection

## 목표
- Line Dashboard 수신인 설정 화면에서 알림 Target별, 채널별 템플릿을 사용자가 선택할 수 있게 한다.
- 템플릿 옵션은 backend registry를 기준으로 내려주고, 메신저의 "새 대화방 생성" UI는 현재 위치에 둔다.

## 현재 상태
- 채널별 템플릿 값은 `DroneSopTargetChannelConfig.template_key`에 이미 저장된다.
- `DroneUserSdwtJiraKeyView`는 Jira용 `templateKey`만 일부 노출한다.
- frontend `AlarmChannelSettingsCard`는 채널 활성화와 Jira project key만 편집한다.
- mail/messenger template registry는 backend 코드에 이미 존재한다.

## 범위
- 수정: Drone API view/url, template option serialization, line-dashboard API wrapper/hook/UI.
- 수정: 관련 backend view 테스트.
- 제외: DB schema/migration, 메신저 "새 대화방 생성" UI 이동, 수신인 카드 구조 변경.

## 설계
- `GET /api/v1/line-dashboard/notification-template-options`를 추가해 registry 기반 옵션을 반환한다.
- 기존 `/api/v1/line-dashboard/jira-keys` GET/POST에 `jiraTemplateKey`, `messengerTemplateKey`, `mailTemplateKey`를 추가한다.
- frontend는 `templateKeys = { jira, messenger, mail }` 형태로 normalize하고, `AlarmChannelSettingsCard`에서 채널별 select를 표시한다.
- auth/permission은 기존 알림 설정 관리 권한을 따른다. 조회는 인증 사용자, 저장은 운영자 권한(`is_staff` 포함) 사용자만 허용한다.
- 저장 시 채널별 template key는 backend registry에 존재하는 값만 허용한다.
- frontend draft에서 template key가 비어 있으면 각 채널 기본값으로 `common`을 자동 선택한다.

## 실행 단계
- [x] backend registry option builder와 endpoint 추가
- [x] 기존 channel settings GET/POST response/request 확장
- [x] frontend API wrapper와 hook state/draft/save 확장
- [x] channel settings UI에 template select 추가
- [x] backend registry key validation 추가
- [x] frontend 기본 template key를 `common`으로 정규화
- [x] backend/frontend 검증 실행

## 검증
- `docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.drone`
- `npm run agent:audit:ui`
- `npm run agent:audit:web-boundary`

## 위험과 대응
- 위험: 기존 `templateKey` 호환 호출이 깨질 수 있다.
- 대응: legacy `templateKey`는 Jira alias로 유지하고 신규 camelCase 필드를 추가한다.
- 위험: registry key label이 부족해 UI가 불친절할 수 있다.
- 대응: backend에서 기본 label map을 제공하고, 알 수 없는 key는 key 자체를 label로 내려준다.
- 위험: API 직접 호출로 registry에 없는 template key가 저장될 수 있다.
- 대응: POST 검증에서 채널별 registry membership을 확인한다.
- 위험: 새 target의 template key draft가 비어 활성 채널이 실제 발송되지 않을 수 있다.
- 대응: frontend 기본값을 `common`으로 채우고, 저장 payload도 빈 값을 `common`으로 정규화한다.

## 진행 기록
- 2026-06-18: 구현 계획 작성. DB migration 없이 HTTP/UI contract 확장으로 진행.
- 2026-06-18: backend template option endpoint와 channel settings template key contract 추가.
- 2026-06-18: frontend API/hook과 알람 채널 설정 카드에 채널별 template select 추가.
- 2026-06-18: `manage.py check`, frontend UI/boundary audit, 변경 파일 eslint, `npm run web:build` 통과. `api.drone` 테스트는 test DB 생성 중 `gin_trgm_ops` 확장 누락으로 중단.
- 2026-06-18: 리뷰 후속으로 backend registry key 검증과 frontend `common` 기본 선택을 추가하기로 결정.
- 2026-06-18: backend registry key 검증과 frontend `common` 기본 선택 적용. `DroneJiraKeyEndpointTests`, `manage.py check`, frontend eslint/audit/build 통과.
