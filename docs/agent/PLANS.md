# Codex ExecPlan 규칙

## 목적
복잡한 작업에서 agent가 요구사항, 위험, 검증 방법을 잃지 않도록 실행 계획을 문서화한다.

## 사용할 때
아래 중 하나에 해당하면 구현 전에 ExecPlan을 작성하거나 갱신한다.

- 3개 이상 파일을 수정하는 기능/리팩터링
- API contract, DB schema, auth/permission, env contract 변경
- frontend/backend를 함께 건드리는 변경
- migration, data backfill, 외부 연동, mock/dev wiring 변경
- 기존 실패를 재현하고 단계적으로 고치는 작업

아래 작업에는 사용하지 않는다.

- 단일 파일의 작은 오타/문구/style 수정
- 명백한 lint/import 정리
- 이미 사용자가 구체적인 수정 위치와 내용을 지정한 작은 변경

## 저장 위치
- 작업별 계획은 `docs/agent/plans/<slug>.md`에 둔다.
- `<slug>`는 feature 또는 문제 이름을 kebab-case로 작성한다.
- 완료 후에도 중요한 의사결정이 있으면 `docs/agent/decisions.md`에 요약한다.

## 형식
ExecPlan은 아래 섹션을 유지한다.

```markdown
# ExecPlan: <작업명>

## 목표
- 사용자가 원하는 최종 상태

## 현재 상태
- 관련 파일/모듈
- 이미 확인한 사실

## 범위
- 수정할 영역
- 수정하지 않을 영역

## 설계
- 데이터 흐름
- public API/facade 영향
- migration/env/auth 영향

## 실행 단계
- [ ] 단계 1
- [ ] 단계 2

## 검증
- 실행할 명령
- 기대 결과

## 위험과 대응
- 위험:
- 대응:

## 진행 기록
- YYYY-MM-DD: 변경/결정 요약
```

## 운영 규칙
- ExecPlan은 살아있는 문서로 취급한다.
- 구현 중 사실이 바뀌면 계획을 먼저 갱신한다.
- 완료 전 `검증` 섹션의 명령을 실행하거나, 실행하지 못한 이유를 남긴다.
- 사용자 요청 범위 밖 리팩터링을 계획에 끼워 넣지 않는다.
