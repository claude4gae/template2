# ExecPlan: Agent Boundary Guardrails

## 목표
- agent가 modular monolith 구조와 앱 독립성을 더 일관되게 지키도록 자동 검증을 강화한다.
- 기존 legacy 후보 때문에 기본 검증 신호가 흐려지지 않도록, 현재 코드에서 통과 가능한 경계 규칙부터 CI에 연결한다.

## 현재 상태
- frontend feature boundary audit은 `scripts/agent/check_frontend_boundaries.sh`에 있다.
- UI/docs audit은 존재하지만 현재 legacy 후보로 실패한다.
- backend 경계 규칙은 `apps/api/AGENTS.md`에 있으나 자동 audit은 없다.
- CI는 frontend boundary/lint/build와 backend Python compile만 실행한다.

## 범위
- 수정 영역:
  - agent audit script
  - package script
  - AGENTS/skill/decision 문서
  - GitHub Actions guardrail
- 제외 영역:
  - 기존 UI/docs audit 실패 후보 대량 정리
  - backend service direct read ORM 리팩터링
  - 앱 기능 코드 변경

## 설계
- backend audit은 Python AST 기반으로 구현한다.
- 1차 실패 항목은 현재 규칙과 현재 코드 상태를 함께 만족하는 항목으로 제한한다.
  - cross-domain internal import 금지
  - test cross-domain internal import 금지
  - `views.py` 직접 ORM 사용 금지
  - `selectors.py` write ORM 사용 금지
  - backend app 허용 파일/폴더 구조 점검
- service direct read ORM은 후보가 많으므로 이번 CI 실패 기준에 넣지 않는다.
- frontend audit은 `components/<group>`의 허용 그룹 및 추가 중첩 금지를 보강한다.

## 실행 단계
- [x] backend boundary audit script 추가
- [x] `package.json`에 `agent:audit:api-boundary` 추가
- [x] frontend boundary script의 components depth 규칙 보강
- [x] root/scoped AGENTS와 audit skill 문서 갱신
- [x] CI workflow에 backend boundary audit 추가
- [x] 검증 명령 실행

## 검증
- `npm run agent:audit:web-boundary`
- `npm run agent:audit:api-boundary`
- `python3 -m py_compile scripts/agent/check_backend_boundaries.py`
- `git diff --check`

## 위험과 대응
- 위험: backend audit이 기존 legacy 후보를 대량 실패시켜 CI 신호를 약화할 수 있다.
- 대응: 1차 실패 기준을 구조/import/test import/view/selector write로 제한하고 service read ORM은 별도 후속 debt로 둔다.

## 진행 기록
- 2026-06-19: backend boundary audit과 frontend depth guardrail을 1차 적용 대상으로 결정했다.
- 2026-06-19: backend audit script, npm script, CI, AGENTS/skill/docs 연결을 적용했다.
- 2026-06-19: 재점검 중 test import boundary 누락을 발견해 audit에 추가하고 기존 legacy 테스트 후보는 allowlist로 고정했다.
- 2026-06-19: `npm run agent:audit:api-boundary`, `npm run agent:audit:web-boundary`, `python3 -m py_compile scripts/agent/check_backend_boundaries.py`, `git diff --check` 통과를 확인했다.
- 2026-06-19: `npm run agent:audit:ui`와 `npm run agent:audit:docs`는 기존 pm-comparison UI 후보와 문서 inventory 누락으로 실패함을 확인했다.
