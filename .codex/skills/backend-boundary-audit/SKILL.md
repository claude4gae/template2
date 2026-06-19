---
name: backend-boundary-audit
description: |
  Django domain app boundary와 service/selector/view 책임 분리를 deterministic script로 점검하는 스킬.
  cross-domain internal import, test import boundary, view 직접 ORM, selector write, backend app 구조 위반 후보를 찾는다.
---

# backend-boundary-audit

## 목적
`apps/api/api/*`의 domain app 독립성과 backend 책임 분리 규칙을 빠르게 검증한다.

## 사용할 때
- backend domain feature를 생성/수정한 뒤
- cross-domain import를 추가/수정한 뒤
- `views.py`, `selectors.py`, `services/*` 책임 경계를 바꾼 뒤
- 큰 backend 리팩터링 후 boundary 회귀를 점검할 때

## 실행
아래 명령을 실행한다.

```bash
npm run agent:audit:api-boundary
```

또는 직접 실행한다.

```bash
python3 scripts/agent/check_backend_boundaries.py
```

## 해석 규칙
- 출력은 우선 review 대상 후보로 본다.
- legacy 예외가 있으면 수정하지 말고 파일 경로와 이유를 요약한다.
- legacy 예외는 `scripts/agent/backend-boundary-allowlist.txt`에 path + 구체 패턴으로만 둔다.
- 요청 범위 밖 구조 변경은 하지 않는다.
- 이 audit은 현재 CI 신호를 안정적으로 유지하기 위해 service direct read ORM 후보를 실패 처리하지 않는다.

## 점검 관점
- 다른 domain 내부 모듈 직접 import 금지
- cross-domain import는 `services` facade 또는 `selectors`만 사용
- 테스트도 다른 domain 내부 모듈을 직접 import하지 않는지 확인
- `views.py` 직접 ORM 사용 금지
- `selectors.py` write ORM 사용 금지
- backend app 하위 파일/폴더가 허용 목록을 따르는지 확인
