# Eval: Frontend Feature Boundary

## Task
frontend feature의 route, public facade, cross-feature import를 추가/수정한다.

## Success Criteria
- 다른 feature 내부 경로를 직접 import하지 않는다.
- cross-feature import는 `@/features/<feature>` facade만 사용한다.
- feature는 `index.js`와 `routes.jsx`를 유지한다.
- feature `index.js`에서 `export *`를 사용하지 않는다.
- 허용되지 않은 feature 하위 폴더를 만들지 않는다.
- `npm run agent:audit:web-boundary`가 통과한다.

## Regression Notes
- legacy 예외가 있으면 수정 범위 밖에서 고치지 말고 경로와 이유를 보고한다.
