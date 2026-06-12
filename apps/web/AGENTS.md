# AGENTS.md

## Scope
These rules apply to `apps/web/**`.

## Frontend Feature Boundary
- Feature path: `apps/web/src/features/<feature>`
- Allowed subpaths only:
  - `pages/`
  - `components/`
  - `hooks/`
  - `api/`
  - `store/`
  - `utils/`
  - `routes.jsx`
  - `index.js`
- Folder depth rule:
  - Default: max depth 2
  - One extra level under `components/` only when:
    - the feature already has 12+ component files, or grouping is explicitly requested
    - subfolder name is one of: `list`, `detail`, `form`, `dialog`, `table`, `chart`, `filters`, `cards`, `sections`
    - no further nesting
  - If another subfolder name is needed, ask first.

## Public Facade
- `apps/web/src/features/<feature>/index.js` is the only public surface.
- Named exports only.
- `export *` is forbidden.
- Feature-internal files must not import another feature, including another feature's facade.
- Cross-feature composition is allowed only from non-feature orchestration layers such as `routes/*`, `components/layout/*`, or `lib/*`.
- When a non-feature orchestration layer imports a feature, it must use `import { something } from "@/features/<otherFeature>"`.
- Explicit `@/features/<otherFeature>/index.js` import is forbidden.
- Direct imports to another feature's internals are forbidden (`components/*`, `pages/*`, `api/*`, etc.).

## Import Rules
- Prefer `@/` for project-internal absolute imports.
- `components/*` alias is allowed only for `components/...` paths.
- Do not mix `@/components/...` and `components/...` in one file.
- Keep existing alias style when editing.
- Project-internal absolute imports must resolve under:
  - `apps/web/src/components/ui/*`
  - `apps/web/src/components/layout/*`
  - `apps/web/src/components/common/*`
  - `apps/web/src/lib/*`
  - `apps/web/src/features/<otherFeature>` (facade only from non-feature orchestration layers)

## UI, Route, and Data Rules
- Do not manually edit `apps/web/src/components/ui/**` unless explicitly requested via shadcn CLI flow.
- Every feature must expose `routes.jsx`.
- Global routes only in `apps/web/src/routes/*`.
- Routes may compose `components/layout/*`, but must not define layout components in `routes/*`.
- Routes must not contain business logic/data logic/derived UI logic.
- React Query is the single source of truth for server data.
- Use array query keys, avoid redundant keys, and invalidate minimum scope.
- Never mirror server data to Zustand.
- Zustand is only for feature-local UI/interaction flow state.

## Styling, React, and Layout
- Tailwind only; use design tokens; use `dark:` for dark mode.
- Use shadcn/Radix primitives from `apps/web/src/components/ui/*` before creating custom primitives.
- Product UI decisions must follow `product-ui-design-system` skill.
- Use semantic tokens (`bg-card`, `text-muted-foreground`, `border-border`, `text-destructive`, `bg-primary`, etc.) before raw colors.
- Arbitrary HEX and inline style are forbidden unless strictly necessary; CSS variable-based dynamic sizing/coloring is allowed when library integration requires it.
- Avoid premature optimization (`useMemo`, `useCallback`, `React.memo` only when required).
- UI states must be explicit: loading, empty, error, disabled, selected, hover/focus, and dark mode when applicable.
- Interactive controls must keep accessible labels, keyboard reachability, and visible focus states.
- Layout core constraints:
  - one scroll container per axis per region
  - scrollable elements require `min-h-0`
  - page skeleton: `h-screen flex flex-col` + fixed header + `flex-1 min-h-0 overflow-hidden`
- Detailed layout recipes are in `compose-frontend-layout` skill.

## Verification
- After frontend UI changes, run or recommend `npm run agent:audit:ui`.
- After feature import/export/routing changes, run or recommend `npm run agent:audit:web-boundary`.
- For broad frontend changes, run or recommend `npm run agent:audit`.
- Audit script findings are review candidates; do not fix legacy findings outside the requested scope.
