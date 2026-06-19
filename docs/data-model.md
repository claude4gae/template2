# 데이터 모델과 저장소

이 앱은 기본 업무 DB, observer 전용 DB, MinIO, 외부 시스템을 함께 사용합니다.

## 저장소 개요

| 저장소 | 설정 | 사용 모듈 | 역할 |
| --- | --- | --- | --- |
| 기본 PostgreSQL | `DJANGO_DB_*` | Account, Emails, Drone, AppStore, VOC, Activity | 업무 데이터, 권한, 로그, 알림 상태 |
| Observer PostgreSQL | `OBSERVER_DB_*` | Observer | line/SDWT/공정/설비/log 조회 |
| MinIO | `MINIO_*` | Emails/Common | 메일 asset 파일 저장/조회 |
| Dummy 외부계 memory/file | `apps/adfs_dummy` | 로컬 Auth/RAG/LLM/Mail/Jira | 외부 시스템 대체 |
| 외부 RAG/LLM/Mail/Jira/Messenger | env 기반 URL/token | Emails, Assistant, Drone | 검색, 답변, 알림, 메일 전송 |

## 기본 DB 모델

| App | 모델 | 목적 |
| --- | --- | --- |
| Account | `User` | 로그인 사용자와 OIDC claim 기반 사용자 정보 |
| Account | `UserProfile` | 사용자 부가 profile |
| Account | `Affiliation` | line, SDWT, product 기준 소속 단위 |
| Account | `UserCurrentAffiliation` | 사용자의 현재 소속 |
| Account | `UserSdwtProdAccess` | 접근 가능한 SDWT/product 권한 |
| Account | `UserSdwtProdChange` | 소속/권한 변경 요청과 승인 상태 |
| Account | `ExternalAffiliationSnapshot` | 외부 예측 소속 snapshot |
| Activity | `ActivityLog` | 사용자/시스템 활동 로그 |
| Emails | `Email` | 수집/작성/분류된 메일 본문과 metadata |
| Emails | `EmailOutbox` | RAG insert/delete 비동기 작업 |
| Emails | `EmailAsset` | 메일 첨부/이미지/OCR 대상 asset metadata |
| Drone | `DroneSOP` | SOP 이벤트 본문과 기준 상태 |
| Drone | `DroneSopTarget` | 알림 대상 line/소속 단위 |
| Drone | `DroneSopTargetChannelConfig` | target별 channel 설정 |
| Drone | `DroneSopNeedToSendRule` | 전송 필요 여부 rule |
| Drone | `DroneSopTargetMapping` | SOP와 target 매핑 |
| Drone | `DroneSopTargetRecipient` | target별 수신자 |
| Drone | `DroneSopTargetDispatch` | target dispatch 실행 단위 |
| Drone | `DroneSopDelivery` | channel별 전송 결과 |
| Drone | `DroneEarlyInform` | 조기 알림/라인 대시보드 데이터 |
| AppStore | `AppStoreApp` | 내부 앱 등록 정보 |
| AppStore | `AppStoreLike` | 앱 좋아요 |
| AppStore | `AppStoreComment` | 앱 댓글 |
| AppStore | `AppStoreCommentLike` | 댓글 좋아요 |
| VOC | `VocPost` | VOC 게시글 |
| VOC | `VocReply` | VOC 답변 |

## 모델이 없는 app

| App | 데이터 위치 |
| --- | --- |
| `api.auth` | `api.account.User`와 session/OIDC claim 사용 |
| `api.assistant` | RAG/LLM 외부 응답을 runtime에서 조립 |
| `api.rag` | 외부 RAG API client |
| `api.observer` | observer 전용 DB read-only 조회 |
| `api.health` | runtime 상태 계산 |
| `api.common` | 공통 service/helper |

## 주요 관계

- `User`는 현재 소속(`UserCurrentAffiliation`)과 접근 권한(`UserSdwtProdAccess`)을 통해 업무 데이터 접근 범위를 얻습니다.
- Emails는 mailbox/소속 접근 범위를 기준으로 메일 목록과 상세 접근을 제한합니다.
- `EmailOutbox`는 RAG 등록/삭제 작업을 보관하고 `process_email_outbox`가 처리합니다.
- Drone SOP는 target, channel config, recipient, dispatch, delivery로 분리되어 알림 설정과 발송 결과를 추적합니다.
- AppStore와 VOC는 작성자와 댓글/답변 관계를 기본 DB에 저장합니다.
- Observer는 기본 DB model 없이 별도 DB의 line/equipment/log 데이터를 selector에서 조회합니다.

## 변경 시 확인 항목

- migration이 필요한 기본 DB schema 변경인지 확인합니다.
- observer DB는 외부/별도 schema이므로 Django migration 대상이 아닙니다.
- 모델 추가/삭제/필드 변경 시 `docs/data-model.md`, 해당 모듈 문서, API response 문서를 함께 갱신합니다.
- 파일 저장 정책 변경 시 `docs/integrations.md`의 MinIO와 `docs/configuration.md`의 `MINIO_*`를 갱신합니다.
