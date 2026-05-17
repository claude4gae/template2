# Agent Evals

## 목적
agent 성능을 “느낌”이 아니라 반복 가능한 작업과 성공 기준으로 평가한다.

## 사용 방법
1. eval 파일에서 `Task`를 agent에게 그대로 요청한다.
2. agent가 수정/검증을 끝낸 뒤 `Success Criteria`를 체크한다.
3. 실패하거나 흔들린 기준은 `Regression Notes`에 기록한다.
4. 반복 실패가 있으면 `AGENTS.md`, skill, script 중 하나로 피드백을 반영한다.

## 작성 규칙
- 실제 프로젝트에서 자주 발생하는 작업만 추가한다.
- 성공 기준은 사람이 판정 가능해야 한다.
- 가능한 경우 실행 명령을 포함한다.
- agent가 건드리면 안 되는 파일/범위를 명시한다.

## 초기 eval 목록
- `frontend-ui-consistency.md`
- `frontend-boundary.md`
- `django-service-selector.md`
- `offsite-contract-sync.md`
- `timeline-refactor-coordination.md`
