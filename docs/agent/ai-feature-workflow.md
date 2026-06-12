# AI Feature Workflow

이 문서는 브랜치에서 AI가 작업할 때 feature 독립성 방향을 유지하기 위한 최소 지침입니다.

## 기본 원칙

1. 작업 전 root `AGENTS.md`와 수정 경로의 scoped `AGENTS.md`를 확인합니다.
2. feature 내부 파일은 다른 feature를 import하지 않습니다.
3. feature 간 조립은 `apps/web/src/routes`, `apps/web/src/components/layout`, `apps/web/src/lib` 같은 non-feature 계층에서만 합니다.
4. frontend 공개면은 `apps/web/src/features/<feature>/index.js` named export로 제한합니다.
5. backend 공개면은 `selectors.py` 또는 `services/__init__.py` facade로 제한합니다.
6. `lib`는 여러 feature에서 쓰는 안정된 계약만 둡니다. 특정 feature의 화면/상태 구현을 `lib`로 옮기지 않습니다.
7. intranet URL, token, credential은 코드에 직접 쓰지 않고 env로 주입합니다.

## AI에게 붙여 넣을 기본 프롬프트

```text
이 repo는 feature 독립성을 우선한다.
작업 전 AGENTS.md와 수정 경로의 scoped AGENTS.md를 확인하라.
feature 내부 파일에서 다른 feature를 import하지 말라.
다른 feature 기능이 필요하면 routes/components/layout/lib 같은 non-feature 계층에서 조립하거나 public facade만 사용하라.
외부 URL, token, credential은 코드에 하드코딩하지 말고 env 기반으로 처리하라.
작업 후 npm run agent:audit:web-boundary, npm run web:lint, npm run web:build를 실행하고 결과를 보고하라.
backend 변경이 있으면 Docker Compose api 컨테이너 기준 테스트를 실행하거나 실행 불가 사유를 남겨라.
```

## 필수 검증

Frontend feature import/export/routing 변경 후:

```bash
npm run agent:audit:web-boundary
npm run web:lint
npm run web:build
```

Backend business logic 변경 후:

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py test api.<feature>
```

Docker Compose `api` 컨테이너가 실행되지 않으면, 실패 원인을 PR에 기록합니다.

## PR에서 확인할 것

- feature 내부에 `@/features/<otherFeature>` import가 없는지 확인합니다.
- `components/layout`, `routes`, `lib`에 들어간 코드가 특정 feature 내부 구현을 과하게 알고 있지 않은지 확인합니다.
- facade export가 불필요하게 넓어지지 않았는지 확인합니다.
- 공통 코드가 새 쓰레기통이 되지 않도록 도메인별 하위 경로를 사용했는지 확인합니다.
