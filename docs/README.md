# 앱 문서 홈

이 `docs` 폴더는 코드를 열지 않아도 앱의 구조, 화면, API, 데이터, 환경 변수, 외부 연동, 운영 방법을 파악할 수 있게 정리한 문서입니다.

## 먼저 읽는 순서

1. 전체 그림: `docs/architecture.md`
2. 실제 route/model/env 색인: `docs/inventory.md`
3. 프론트 구조와 화면 흐름: `docs/frontend.md`
4. 백엔드 구조와 책임 분리: `docs/backend.md`
5. 데이터 모델과 저장소: `docs/data-model.md`
6. API 공통 규칙과 모듈별 계약: `docs/api/README.md`, `docs/api/*.md`
7. 모듈별 업무 흐름: `docs/modules/*.md`
8. 환경 변수와 로컬/운영 설정: `docs/configuration.md`
9. 외부 시스템 연동: `docs/integrations.md`
10. 실행, 검증, management command: `docs/operations.md`

## 문서 지도

| 문서 | 설명 |
| --- | --- |
| `docs/architecture.md` | 전체 앱 구조, 모듈 경계, 핵심 데이터 흐름 |
| `docs/inventory.md` | 실제 backend API route, frontend route, model, command, env 색인 |
| `docs/frontend.md` | React SPA 구조, route tree, feature facade, 상태 관리 원칙 |
| `docs/backend.md` | Django app 구조, view/selector/service 책임, URL prefix, command |
| `docs/data-model.md` | 주요 DB 모델, 저장소, 외부 observer DB, 파일 저장소 |
| `docs/configuration.md` | env 파일, 설정 그룹, 로컬/운영 차이 |
| `docs/api/README.md` | API 공통 호출 규칙, 인증 방식, 오류 규칙 |
| `docs/api/*.md` | 모듈별 endpoint 계약 |
| `docs/modules/*.md` | 모듈별 기능, 권한, 화면, 데이터, 동작 흐름 |
| `docs/operations.md` | 로컬 실행, 테스트, 관리 명령, 점검 절차 |
| `docs/integrations.md` | ADFS, RAG, LLM, Mail, Jira, Messenger, MinIO, Airflow 연동 |
| `docs/agent/ai-feature-workflow.md` | 브랜치에서 AI가 작업할 때 지켜야 할 feature 독립성 지침 |

## 모듈 목록

| 모듈 | 기능 문서 | API 문서 | 주요 화면/route |
| --- | --- | --- | --- |
| Auth | `docs/modules/auth.md` | `docs/api/auth.md` | `/login`, OIDC callback |
| Account | `docs/modules/account.md` | `docs/api/account.md` | `/settings/account`, `/settings/members` |
| Emails | `docs/modules/emails.md` | `docs/api/emails.md` | `/emails/inbox`, `/emails/sent`, `/emails/members` |
| Assistant/RAG | `docs/modules/assistant.md` | `docs/api/assistant.md` | `/assistant` |
| Line Dashboard/Drone | `docs/modules/line-dashboard.md` | `docs/api/line-dashboard.md` | `/ESOP_Dashboard/**` |
| Observer | `docs/modules/observer.md` | `docs/api/observer.md` | `/observer`, `/observer/:eqpId` |
| AppStore | `docs/modules/appstore.md` | `docs/api/appstore.md` | `/appstore` |
| VOC | `docs/modules/voc.md` | `docs/api/voc.md` | `/voc` |
| Activity/Health | `docs/modules/activity-health.md` | `docs/api/activity-health.md` | API only |

## 문서 완성 기준

- 신규 사용자가 `docs/README.md`에서 시작해 앱 실행, 화면 구조, API 호출, 데이터 흐름, 운영 점검까지 추적할 수 있어야 합니다.
- 각 feature는 “화면 route → frontend API client/hook → backend endpoint → selector/service/model → 외부 연동 또는 DB” 흐름으로 추적 가능해야 합니다.
- API 문서는 method, path, auth, query/body, response, error, side effect를 설명해야 합니다.
- 모듈 문서는 목적, 권한, 주요 상태, 동작 흐름, 운영 포인트, 관련 코드 경로를 포함해야 합니다.
- route/model/env/command 같은 변경 가능성이 큰 항목은 `docs/inventory.md`와 검증 스크립트로 drift를 줄입니다.

## 문서 작성 원칙

- 코드 동작과 다른 내용을 문서에 쓰지 않습니다.
- 내부 파일 경로는 설명을 보강하는 색인으로 사용하고, 업무 개념 설명을 먼저 둡니다.
- 외부 URL, token, credential은 env 이름과 역할만 문서화하고 실제 비밀값을 반복 기재하지 않습니다.
- 새 API나 route를 추가하면 `docs/inventory.md`, 해당 `docs/api/*.md`, 해당 `docs/modules/*.md`를 함께 갱신합니다.
