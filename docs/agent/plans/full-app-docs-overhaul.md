# ExecPlan: 앱 전체 문서 상세화

## 목표
- 사용자가 코드 파일을 열지 않아도 앱의 구조, 화면, API, 데이터, 운영, 외부 연동, 개발 규칙을 문서만으로 이해할 수 있게 한다.
- 기존 `docs/README.md`, `docs/architecture.md`, `docs/api/*.md`, `docs/modules/*.md` 체계를 유지하면서 누락된 상세 축을 보강한다.
- 실제 코드의 route, model, env, management command와 문서의 불일치를 찾는 검증 스크립트를 추가한다.

## 현재 상태
- 문서 홈은 `docs/README.md`이고, 아키텍처/API/모듈/운영/연동 문서로 분리되어 있다.
- 모듈별 기능 문서와 API 문서는 존재하지만 대부분 요약형이다.
- 프론트 route tree, 백엔드 app 구조, DB 모델, env 계약, management command, 문서 검증 기준이 별도 상세 문서로 정리되어 있지 않다.

## 범위
- 수정/추가 대상은 `docs/**`와 문서 검증용 `scripts/agent/check_docs_inventory.sh`로 제한한다.
- 앱 런타임 코드, API 동작, DB schema, env 값은 변경하지 않는다.
- 기존 모듈 문서 경로와 API 문서 경로는 유지한다.

## 설계
- 문서 홈은 “처음 읽는 순서”와 “문서 완성 기준”을 제공한다.
- 핵심 상세 문서는 `docs/backend.md`, `docs/frontend.md`, `docs/data-model.md`, `docs/configuration.md`로 분리한다.
- 모듈 문서는 공통 템플릿을 따른다: 목적, 화면/route, API, 권한, 데이터, 프론트/백엔드 파일, 외부 연동, 운영 포인트.
- API 문서는 endpoint별 계약과 공통 인증/오류/응답 규칙을 더 명확히 한다.
- 검증 스크립트는 실제 `urls.py`, `routes.jsx`, `models.py`, env 파일의 핵심 항목이 docs에 언급되는지 확인한다.

## 실행 단계
- [x] 현재 route/model/env/command inventory를 정리한다.
- [x] `docs/README.md`, `docs/architecture.md`를 상세 문서 허브로 확장한다.
- [x] `docs/backend.md`, `docs/frontend.md`, `docs/data-model.md`, `docs/configuration.md`를 추가한다.
- [x] 모듈 문서와 API 공통 문서를 상세화한다.
- [x] `docs/operations.md`, `docs/integrations.md`에 운영/연동 확인 흐름을 보강한다.
- [x] 문서 inventory 검증 스크립트를 추가하고 실행한다.

## 검증
- `scripts/agent/check_docs_inventory.sh`
- 기대 결과: 실제 backend API prefix, frontend route, model class, 주요 env group이 docs에 누락 없이 언급된다.

## 위험과 대응
- 위험: 실제 코드와 다른 상세를 문서에 적을 수 있다.
- 대응: route/model/env/command는 코드에서 추출한 이름과 경로를 기준으로 작성한다.
- 위험: 문서가 너무 길어져 읽기 흐름이 깨질 수 있다.
- 대응: 홈/아키텍처는 지도 역할로 유지하고 상세는 주제별 문서로 분리한다.

## 진행 기록
- 2026-05-17: 문서 상세화 범위와 검증 방식을 확정했다.
- 2026-05-17: route/model/env/command 색인 문서와 backend/frontend/data/configuration 상세 문서를 추가했다.
- 2026-05-17: 모듈/API/운영/연동 문서를 보강하고 `scripts/agent/check_docs_inventory.sh` 검증을 통과했다.
