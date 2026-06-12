## 변경 요약

-

## Feature 독립성 체크

- [ ] 작업 전 `AGENTS.md`와 관련 scoped `AGENTS.md`를 확인했습니다.
- [ ] feature 내부 파일에서 다른 feature를 import하지 않았습니다.
- [ ] feature 간 조립은 `apps/web/src/routes`, `apps/web/src/components/layout`, `apps/web/src/lib` 계층에서만 했습니다.
- [ ] 외부 공개면은 frontend `features/<feature>/index.js`, backend `selectors.py` 또는 `services/__init__.py`로 제한했습니다.
- [ ] 공통화가 필요한 코드는 `lib`/`common`에 넣기 전에 2개 이상 feature에서 필요한지 확인했습니다.
- [ ] intranet URL, token, credential을 코드에 하드코딩하지 않았습니다.

## 검증

- [ ] `npm run agent:audit:web-boundary`
- [ ] `npm run web:lint`
- [ ] `npm run web:build`
- [ ] backend 변경 시 Docker Compose `api` 컨테이너 기준 테스트 또는 실행 불가 사유 기록

## AI 작업 사용 여부

- [ ] AI가 작업했다면 `docs/agent/ai-feature-workflow.md`의 기본 프롬프트/검증 절차를 따랐습니다.
