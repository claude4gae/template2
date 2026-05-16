---
name: frontend-boundary-audit
description: |
  React feature boundary와 public facade 규칙을 deterministic script로 점검하는 스킬.
  cross-feature internal import, export-star, routes/index 누락, 허용되지 않은 feature 하위 폴더를 찾는다.
---

# frontend-boundary-audit

## 목적
`apps/web/src/features/*`의 feature boundary 규칙을 빠르게 검증한다.

## 사용할 때
- frontend feature를 생성/수정한 뒤
- cross-feature import 또는 public facade export를 바꾼 뒤
- routing/index export를 정리한 뒤
- 큰 frontend 리팩터링 후 boundary 회귀를 점검할 때

## 실행
아래 명령을 실행한다.

```bash
scripts/agent/check_frontend_boundaries.sh
```

## 해석 규칙
- 출력은 우선 review 대상 후보로 본다.
- legacy 예외가 있으면 수정하지 말고 파일 경로와 이유를 요약한다.
- 요청 범위 밖 구조 변경은 하지 않는다.

## 점검 관점
- 다른 feature 내부 경로 직접 import 금지
- `@/features/<feature>/index.js` 명시 import 금지
- feature `index.js`의 `export *` 금지
- 모든 feature의 `index.js`, `routes.jsx` 존재
- feature 하위 폴더가 허용 목록을 따르는지 확인
