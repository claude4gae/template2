# Agent Decisions

이 문서는 반복 설명 비용을 줄이기 위한 확정 결정만 기록한다.

## 확정된 운영 결정
- 프로젝트 전용 skill은 `.codex/skills/*/SKILL.md`에 둔다.
- `.codex/skills/.system/**`은 로컬 시스템 skill로 보고 추적/공유 대상에서 제외한다.
- frontend UI 변경 후에는 `npm run agent:audit:ui` 또는 `scripts/agent/check_ui_consistency.sh`를 실행한다.
- frontend feature import/export/routing 변경 후에는 `npm run agent:audit:web-boundary` 또는 `scripts/agent/check_frontend_boundaries.sh`를 실행한다.
- 큰 작업은 `docs/agent/PLANS.md`의 ExecPlan 기준을 따른다.
- eval은 `docs/agent/evals/*`의 작업/성공 기준을 기준으로 누적한다.

## 보류된 결정
- backend boundary audit은 단순 grep이 아니라 AST 기반으로 별도 설계한다.
- multi-agent orchestration은 eval에서 병렬 검토 효과가 확인될 때까지 도입하지 않는다.
