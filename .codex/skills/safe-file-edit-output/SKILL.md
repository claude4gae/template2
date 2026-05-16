---
name: safe-file-edit-output
description: |
  파일 생성/수정 시 경로, 변경 요약, import 정합성, 변경 범위 통제를
  일관되게 적용하는 스킬.
---

# safe-file-edit-output

## 목적
파일 생성/수정 시 출력 형식과 변경 범위를 안정적으로 유지한다.

## 사용할 때
- 새 파일을 생성할 때
- 여러 파일을 함께 수정할 때
- import 경로와 export surface를 함께 맞춰야 할 때

## 핵심 원칙
- 항상 실제 경로 기준으로 설명한다.
- 응답에서 전체 파일 내용을 출력하지 않는다(사용자 명시 요청 시 예외).
- 수정 파일은 기존 구조와 공개 export surface를 보존한다.
- 요청 범위 밖 리팩터링을 하지 않는다.
- 모든 import는 실제 파일로 resolve 가능해야 한다.
- `AGENTS.md`와 다른 skill의 출력 규칙이 충돌하면 이 skill의 “전체 파일 미출력” 원칙을 우선한다.

## 새 파일 생성 규칙
항상 아래를 포함한다.

1. 전체 파일 경로
2. 파일 역할 한 줄 설명
3. 변경/구성 요약
4. 핵심 부분 스니펫(필요할 때만)

## 기존 파일 수정 규칙
- 기존 공개 export를 함부로 바꾸지 않는다.
- 기존 alias style을 유지한다.
- 불필요한 rename/move/refactor 금지
- 요청과 직접 관련 없는 코드 정리는 하지 않는다.
- 변경된 핵심 부분만 간결히 보여준다.

## import/export 점검 규칙
Frontend:
- project-internal absolute import 허용 범위:
  - `@/components/ui/*` 또는 `components/ui/*`
  - `@/components/layout/*` 또는 `components/layout/*`
  - `@/components/common/*` 또는 `components/common/*`
  - `@/lib/*`
  - `@/features/<otherFeature>` (facade only)
- cross-feature import는 `@/features/<feature>` 형식만 사용
- `@/features/<feature>/index.js` 명시 import 금지(항상 facade 경로만 사용)
- `@/features/<feature>/components/*`, `pages/*`, `api/*` 직접 import 금지
- `index.js`에서 `export *` 금지
- JSX 파일은 `.jsx`
- `components/ui/**`는 shadcn CLI 흐름 또는 명시 요청 없이 직접 수정하지 않는다.
- frontend UI 변경은 `product-ui-design-system`과 `compose-frontend-layout`의 적용 여부를 함께 점검한다.

Backend:
- cross-feature import는 facade 또는 selector 경유
- `views.py`에 business logic 금지
- `selectors.py`에 side effect 금지

## 출력 형식 예시
```text
Path: apps/api/api/emails/services/__init__.py
Role: 이메일 도메인의 쓰기/오케스트레이션 파사드

Changes:
- 핵심 변경 요약 1
- 핵심 변경 요약 2

Snippet:
<changed snippet only>
```

여러 파일이면 파일별로 같은 형식을 반복한다.

## 변경 범위 통제 체크
- 요청한 파일만 수정했는가
- public surface가 불필요하게 바뀌지 않았는가
- folder structure 규칙을 어기지 않았는가
- naming rule을 지켰는가

## 금지사항
- "이 부분도 같이 리팩터링" 같은 확장 작업
- unresolved import
- facade 우회 import
- 사용자 요청 없이 전체 파일 내용을 출력
