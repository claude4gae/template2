# 전체 아키텍처

이 앱은 React SPA와 Django API가 한 저장소에 있는 업무용 모듈형 모놀리스입니다. 로컬 개발에서는 dummy 외부계를 함께 띄워 ADFS, RAG, LLM, Mail, Jira를 대체합니다.

## 구성 요소

| 영역 | 경로 | 역할 | 상세 문서 |
| --- | --- | --- | --- |
| Web | `apps/web` | React 19 + Vite SPA | `docs/frontend.md` |
| API | `apps/api` | Django 5.1 API 서버 | `docs/backend.md` |
| Dummy 외부계 | `apps/adfs_dummy` | 로컬 ADFS/RAG/LLM/Mail/Jira 대체 서버 | `docs/integrations.md` |
| Env | `env` | 개발/운영 환경 변수 | `docs/configuration.md` |
| Proxy | `deploy/nginx` | 로컬/운영 통합 진입점 | `docs/operations.md` |
| Docs | `docs` | 앱 상세 설명과 검증 기준 | `docs/README.md` |

## 요청 흐름

1. 브라우저가 React SPA route를 렌더링합니다.
2. 화면은 feature-local hook/API client를 통해 `/api/v1/**` Django endpoint를 호출합니다.
3. Django view는 인증, 요청 파싱, 응답 변환을 담당합니다.
4. 읽기 로직은 selector, 쓰기/외부 호출/transaction은 service가 담당합니다.
5. 데이터는 기본 PostgreSQL, timeline 전용 PostgreSQL, MinIO, 외부 시스템 또는 dummy 외부계에서 조회/저장됩니다.

## 백엔드 모듈

| Django app | 역할 | 주요 저장소/연동 |
| --- | --- | --- |
| `api.auth` | OIDC 로그인/로그아웃/현재 사용자 | ADFS/OIDC, `api.account.User` |
| `api.account` | 소속, 권한, 사용자 pool | 기본 DB |
| `api.emails` | 메일 수집/조회/이동/삭제/OCR/RAG Outbox | 기본 DB, POP3, RAG, MinIO |
| `api.assistant` | RAG 기반 채팅 | RAG, LLM |
| `api.rag` | 외부 RAG 서버 공통 client | RAG |
| `api.drone` | Line Dashboard와 Drone SOP 알림 | 기본 DB, POP3, Jira, Mail API, Messenger |
| `api.timeline` | 별도 timeline DB 조회 | timeline DB, 일부 Drone 데이터 |
| `api.appstore` | 내부 앱 등록/댓글/좋아요 | 기본 DB, cover image |
| `api.voc` | VOC 게시판 | 기본 DB |
| `api.activity` | ActivityLog 조회 | 기본 DB |
| `api.health` | 헬스 체크 | runtime 상태 |
| `api.common` | 공통 middleware/helper/client | logging, storage, mail, messenger |

## 프론트엔드 모듈

프론트엔드는 `apps/web/src/features/<feature>` 단위로 구성됩니다. feature 외부 공개는 항상 `index.js` facade를 통합니다.

| Feature | 역할 | 주요 route |
| --- | --- | --- |
| `auth` | 로그인, 온보딩, 소속 재확인 | `/login` |
| `account` | 계정, 소속, 멤버/권한 | `/settings/account`, `/settings/members` |
| `emails` | 메일함과 메일 처리 | `/emails/inbox`, `/emails/sent`, `/emails/members` |
| `assistant` | RAG 기반 채팅 | `/assistant` |
| `line-dashboard` | Drone SOP/라인 대시보드 | `/ESOP_Dashboard/**` |
| `timeline` | 설비/로그 타임라인 | `/timeline`, `/timeline/:eqpId` |
| `appstore` | 내부 앱 공유 | `/appstore` |
| `voc` | VOC 게시판 | `/voc` |
| `home` | 인증 후 홈 shell | `/` |
| `errors` | route error와 404 | `*` |
| `teamstaff` | 팀/인력 보조 화면 | `/teamstaff` |

## 핵심 데이터 흐름

### 인증과 소속

1. 사용자가 OIDC로 로그인합니다.
2. `api.auth`가 OIDC claim을 검증하고 `api.account.User`를 만들거나 갱신합니다.
3. `api.account`가 현재 소속과 접근 가능한 `user_sdwt_prod`를 계산합니다.
4. Emails, Assistant, Drone은 소속/권한 범위를 재사용해 조회와 작업 권한을 제한합니다.

### 메일과 RAG

1. Emails가 POP3 또는 Mail API에서 메일과 asset을 수집합니다.
2. 발신자, 수신자, 소속, mailbox 기준으로 메일 접근 범위를 계산합니다.
3. RAG 등록/삭제가 필요하면 `EmailOutbox`에 작업을 쌓습니다.
4. Outbox 처리기가 RAG insert/delete endpoint를 호출합니다.
5. Assistant는 RAG 검색 결과를 LLM에 전달해 답변을 생성합니다.

### Drone SOP 알림

1. Drone이 SOP 메일을 수집하거나 Airflow trigger로 pipeline을 시작합니다.
2. 대상 소속, line, channel, recipient, need-to-send rule을 계산합니다.
3. Jira, Messenger, Mail 채널별 dispatch와 delivery 상태를 저장합니다.
4. Line Dashboard 화면은 SOP 상태, 이력, 알림 설정을 조회/수정합니다.

### Timeline 조회

1. Timeline 화면이 line, SDWT, 공정, 설비 조건을 선택합니다.
2. API가 query를 정규화하고 timeline 전용 DB를 조회합니다.
3. EQP, TIP, CTTTM, RACB, Drone 로그를 공통 timeline item 형태로 반환합니다.
4. 프론트는 vis-timeline과 상세 패널에 변환된 로그를 표시합니다.

## 경계 규칙

- 프론트 feature 외부 공개는 `apps/web/src/features/<feature>/index.js`를 통합니다.
- React Query는 서버 데이터의 기준이고, Zustand는 feature-local UI 상태만 저장합니다.
- 백엔드 view는 HTTP 처리만 맡고, 비즈니스 로직은 service/selector에 둡니다.
- selector는 읽기 전용, service는 쓰기/transaction/외부 호출을 담당합니다.
- 다른 백엔드 feature 의존은 selector 또는 `services/__init__.py` facade를 사용합니다.
- 외부 시스템 URL과 인증값은 환경 변수로 관리합니다.

## 상세 색인

- 실제 route/model/env/command 목록: `docs/inventory.md`
- API 호출 규칙: `docs/api/README.md`
- 데이터 모델: `docs/data-model.md`
- 환경 설정: `docs/configuration.md`
- 운영 명령: `docs/operations.md`
