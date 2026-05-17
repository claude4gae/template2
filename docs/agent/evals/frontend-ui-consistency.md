# Eval: Frontend UI Consistency

## Task
`apps/web/src/features/<feature>`에 업무형 page 또는 dialog를 추가/수정한다. 기존 디자인 토큰, shadcn/Radix primitive, layout skill을 사용하고 loading/empty/error 상태를 명시한다.

## Success Criteria
- `product-ui-design-system`과 `compose-frontend-layout` 기준을 따른다.
- raw HEX, 불필요한 raw gray/slate/zinc palette, 불필요한 inline style을 추가하지 않는다.
- loading, empty, error, disabled/selected 상태 중 해당되는 상태가 명시되어 있다.
- 접근 가능한 label/focus/keyboard 동작이 유지된다.
- `npm run agent:audit:ui`에서 새 위반이 없다.

## Regression Notes
- 새 예외가 필요하면 `scripts/agent/ui-audit-allowlist.txt`에 추가하기 전에 이유를 설명한다.
