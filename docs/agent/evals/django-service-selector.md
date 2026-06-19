# Eval: Django Service/Selector Boundary

## Task
Django domain feature의 business logic, read query, serializer/view를 수정한다.

## Success Criteria
- view는 HTTP orchestration만 담당한다.
- read ORM query는 selector에 둔다.
- write/business orchestration은 service에 둔다.
- public service/selector에는 type hint와 한국어 docstring이 있다.
- business logic 변경 시 service/selector 중심 테스트를 추가하거나 수정한다.
- `npm run agent:audit:api-boundary`가 통과한다.
- Docker Compose `api` 컨테이너 기준 테스트 명령을 실행하거나 실행 불가 사유를 보고한다.

## Regression Notes
- migration/schema 변경이 있다면 새 migration만 생성하고 applied migration은 수정하지 않는다.
