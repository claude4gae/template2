---
name: ui-consistency-audit
description: |
  프론트엔드 UI 일관성 위반 후보를 deterministic script로 점검하는 스킬.
  raw color, inline style, route-level h-screen, facade export 패턴 등
  product-ui-design-system/compose-frontend-layout 규칙 위반 후보를 찾는다.
---

# ui-consistency-audit

## 목적
React/Tailwind/shadcn UI 작업 후 일관성 위반 후보를 빠르게 찾는다.

## 사용할 때
- frontend UI를 새로 만들거나 수정한 뒤
- 화면 간 디자인 일관성을 점검할 때
- `product-ui-design-system` 또는 `compose-frontend-layout` 적용 여부를 검증할 때

## 실행
아래 명령을 실행한다.

```bash
scripts/agent/check_ui_consistency.sh
```

## 해석 규칙
- 출력은 “확정 오류”가 아니라 review 대상 후보이다.
- `apps/web/src/components/ui/**`의 shadcn 내부 구현과 외부 라이브러리 연동 코드는 예외일 수 있다.
- 기존 위반 후보를 발견해도 요청 범위 밖이면 고치지 말고 요약만 한다.

## 점검 관점
- raw HEX 또는 raw gray/slate/zinc palette 사용
- 불필요한 inline style
- route/page 내부 `h-screen`
- `export *` facade 위반
- feature 내부 직접 import 후보
