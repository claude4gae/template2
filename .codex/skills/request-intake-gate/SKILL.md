---
name: request-intake-gate
description: |
  구현 전에 사용자 요청을 요약하고, 불명확성을 Hard-Block / Soft로 분류해
  진행 가능 여부를 결정하는 입력 게이트 스킬.
---

# request-intake-gate

## 목적
구현 전에 요구사항을 구조적으로 해석하고, correctness에 영향을 주는 불명확성을 먼저 분리한다.

## 사용할 때
- 새로운 기능 구현을 시작할 때
- 기존 기능 수정 요청을 받았을 때
- 파일 생성/수정/이동 위치를 결정해야 할 때
- API, DB, 권한, 도메인 규칙이 얽힌 요청일 때
- 하나 이상의 해석이 가능한 요청일 때

## 바로 진행 가능한 경우(Soft Assumption)
아래만 불명확하면 질문 없이 기본값으로 진행 가능하다.

- 문구/레이블/placeholder
- spacing, icon, minor empty/loading UX
- correctness에 영향 없는 UI 정리
- 명백한 오타 수정
- 기존 패턴을 그대로 따르는 작은 범위 구현

## 절차
### 0) 적용 강도 판단
구현 요청이 아래에만 해당하면 요약/Soft Assumptions를 짧게 출력하고 즉시 진행한다.

- 기존 패턴을 그대로 따르는 작은 UI/문구/스타일 수정
- 명백한 오타, import 정리, lint/test 실패 수정
- correctness에 영향 없는 layout/spacing 조정

아래에 해당하면 반드시 Hard-Block 여부를 점검한다.

- API/DB/auth/permission/business rule 변경
- cross-feature public facade 또는 dependency 방향 변경
- 새 feature/app/page 생성 위치가 불명확한 경우
- migration/schema/index/constraint 변경

### 1) 요청 요약 작성
구현 전 반드시 아래 두 줄을 먼저 출력한다.

```text
Summary (EN): ...
요약 (KR): ...
```

요약은 짧고 구체적으로 작성하며, 기술 스택/대상 feature/예상 변경 범위를 포함한다.

### 2) 불명확성 수집
구현에 영향을 줄 수 있는 미확정 항목을 전부 수집한다.

예시 범주:
- API schema / request / response
- DB schema / migration / unique constraint / index
- auth / permission / role
- billing / coupon / scheduling 등 business rule
- cross-feature dependency direction
- file/folder placement ambiguity
- public facade export 범위

### 3) 질문 분류
모든 질문을 두 그룹으로 분리한다.

Hard-Block Questions:
- 답을 받아야만 구현 가능한 질문
- 예: API contract 부재, migration schema 불명확, 권한 규칙 미정, feature ownership 불명확

Soft Questions:
- 기본값으로 진행 가능한 질문
- 예: 버튼 문구, placeholder, icon choice, 정렬 기본값, minor spacing

### 3-1) Hard-Block 질문 번호 규칙 (필수)
Hard-Block Questions는 사용자가 번호로 바로 답할 수 있게 항상 번호를 붙인다.

- 형식: `1.`, `2.`, `3.` (연속 번호)
- 한 질문에는 한 가지 결정만 담는다.
- 질문 끝에는 가능한 선택 기준 또는 기본값 후보를 짧게 덧붙인다.

### 4) 진행 여부 판단
Hard-Block이 하나라도 있으면 아래 순서로 출력하고 멈춘다.

1. Summary (EN)
2. 요약 (KR)
3. Hard-Block Questions
4. Soft Questions
5. `구현 전 Hard-Block 확인이 필요합니다.` 안내 문구

Hard-Block 출력 예시:

```text
Hard-Block Questions
1. API 응답에 pagination이 필요한가요? (권장: cursor 기반)
2. 생성 권한은 admin만 허용하나요? (후보: admin / owner / authenticated)
3. 저장 위치는 `apps/web/src/features/orders`가 맞나요?

답변은 번호 기준으로 알려주세요.
예: 1) cursor, 2) admin+owner, 3) 네
```

Hard-Block이 없으면 아래 순서로 출력하고 즉시 구현한다.

1. Summary (EN)
2. 요약 (KR)
3. Soft Assumptions

단순 변경에서는 Soft Assumptions를 1~3개 이하로 제한한다.

## 출력 규칙
- 질문은 번호 목록으로 작성한다.
- Hard-Block과 Soft를 반드시 분리한다.
- Soft Assumptions는 구현 전에 명시한다.
- correctness에 영향 주는 항목은 추측하지 않는다.
- Hard-Block Questions 블록에는 반드시 번호 질문 + `답변은 번호 기준으로 알려주세요.` 문구를 포함한다.

## 주의사항
- 사소한 항목까지 Hard-Block으로 과도하게 올리지 않는다.
- 질문을 위한 질문을 만들지 않는다.
- 기존 저장소 패턴이 명확하면 우선 사용한다.
- 우선순위: `user request > AGENTS.md > feature public contract > existing file style`
