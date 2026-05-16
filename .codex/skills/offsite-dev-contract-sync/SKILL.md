---
name: offsite-dev-contract-sync
description: |
  외부망(offsite) 개발 환경에서 auth/RAG/assistant/mail contract 변경 시
  docker-compose.dev.yml, env/api.dev.env, apps/adfs_dummy 간 정합성을 유지하는 스킬.
---

# offsite-dev-contract-sync

## 목적
corporate network 없이도 로컬 개발 환경이 계속 동작하도록 mock과 dev wiring을 함께 유지한다.

## 사용할 때
- auth / OIDC / ADFS contract를 변경할 때
- RAG endpoint contract를 변경할 때
- assistant dummy mode 연동을 변경할 때
- mail sandbox endpoint를 변경할 때
- `docker-compose.dev.yml` 기준 로컬 실행 가능성을 유지해야 할 때

## 환경 전제
- offsite 개발은 `docker-compose.dev.yml`을 사용한다.
- dummy service는 `apps/adfs_dummy`에 있다.
- Django `api` 서비스는 `env/api.dev.env`로 external dependency URL을 주입받는다.
- assistant dummy mode는 `ASSISTANT_DUMMY_MODE=1`로 제어한다.
- 외부 Docker network `shared-net`을 사용한다.

dummy 주요 endpoint 예시:
- auth/OIDC: discovery/login/logout/callback 관련 endpoint
- RAG: `/rag/search`, `/rag/insert`, `/rag/delete`, `/rag/index-info`
- Mail sandbox: `/mail/*`

## 점검 대상
contract가 바뀌면 아래를 함께 점검한다.

- `apps/adfs_dummy`
- `env/api.dev.env`
- `docker-compose.dev.yml`
- Django 설정의 env var 참조부
- auth/rag/assistant/mail 호출부

## 작업 절차
1. 변경된 contract 식별
   - request field name
   - response shape
   - endpoint path
   - auth callback path
   - timeout/host/base URL
2. 실제 호출부 확인
   - Django service layer
   - serializer/client wrapper
   - dummy service handler
3. dev wiring 동기화
   - `env/api.dev.env`의 URL/mode flag
   - compose 서비스 env 연결
   - mock endpoint path
4. 로컬 실행 가능성 점검
   - compose 기동 가능 여부
   - corporate resource 없이 fallback 가능 여부
   - URL 하드코딩 여부
   - `shared-net`이 없으면 `docker network create shared-net` 선행 필요 여부

## 핵심 규칙
- intranet URL 하드코딩 금지
- 외부 의존성 URL은 env var 유지
- contract 변경 시 mock도 함께 업데이트
- local dummy flow가 깨지지 않도록 유지

## 출력 방식
관련 변경 제안 시 아래를 포함한다.

- 변경된 contract 요약
- 함께 수정해야 할 파일 목록
- mock 반영 필요 여부
- dev env 반영 필요 여부
- 로컬 실행 위험 포인트

## 금지사항
- corporate network 연결을 전제로 한 설명
- dummy/mocking 경로를 무시한 contract 변경
- env var 대신 URL 하드코딩
