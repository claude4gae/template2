---
name: product-ui-design-system
description: |
  React/Tailwind/shadcn 업무형 프론트엔드 화면을 일관된 제품 UI로 만드는 스킬.
  색상 토큰, 타이포그래피, density, 상태 표현, table/form/card/dialog 패턴,
  접근성, dark mode를 현재 프로젝트 규칙에 맞게 적용한다.
---

# product-ui-design-system

## 목적
이 스킬은 화면이 같은 제품처럼 보이도록 시각 규칙과 상호작용 상태를 통일한다.

대상:
- `apps/web/src`의 React JSX 화면
- shadcn/Radix 기반 컴포넌트 조합
- dashboard, admin, table, settings, list-detail, assistant/workbench UI

비대상:
- `apps/web/src/components/ui/**` 직접 수정
- 브랜드/마케팅 landing page
- SVG 일러스트/차트 라이브러리 내부 구현

## 사용할 때
- 새 page/component/dialog/form/table/card를 만들 때
- 기존 화면의 “제각각인 느낌”을 정리할 때
- empty/loading/error/disabled/selected 상태가 빠진 UI를 보완할 때
- 색상/간격/타이포그래피/버튼 위계가 불명확할 때
- `compose-frontend-layout` 적용 후 시각 디자인을 마무리할 때

## 기본 원칙
1. shadcn/Radix primitive를 먼저 조합한다.
2. Tailwind semantic token을 우선 사용한다.
3. 화면 구조는 `compose-frontend-layout`이 소유하고, 이 skill은 시각/상태/상호작용을 소유한다.
4. 업무형 UI는 절제된 대비, 명확한 계층, 낮은 장식 밀도를 기본값으로 둔다.
5. 사용자에게 필요한 상태 정보를 색상만으로 전달하지 않는다.

## 토큰 규칙
우선 사용:
- Surface: `bg-background`, `bg-card`, `bg-popover`, `bg-muted`
- Text: `text-foreground`, `text-muted-foreground`, `text-card-foreground`
- Border/Input: `border-border`, `border-input`, `ring-ring`
- Action: `bg-primary`, `text-primary-foreground`, `text-destructive`
- State: `bg-accent`, `text-accent-foreground`, `bg-secondary`, `text-secondary-foreground`

금지:
- 임의 HEX 색상
- `text-gray-*`, `bg-slate-*` 같은 raw palette 남발
- 토큰으로 표현 가능한 inline color style
- dark mode에서 대비를 확인하지 않은 커스텀 색상

예외:
- 외부 라이브러리 차트/타임라인/테이블 column width
- CSS variable 기반 split pane, measured layout, library integration
- SVG mask/path 같은 브라우저 API 요구사항

## 타이포그래피
- Page title: `text-2xl font-semibold tracking-tight`
- Section title: `text-base font-semibold`
- Card title: `text-sm font-semibold`
- Body: `text-sm text-foreground`
- Secondary text: `text-sm text-muted-foreground`
- Metadata: `text-xs text-muted-foreground`
- Numeric/KPI: `tabular-nums`, 필요 시 `font-mono`

규칙:
- 한 화면에서 heading depth를 3단계 이하로 유지한다.
- label과 helper text를 분리한다.
- 긴 설명은 `text-muted-foreground`와 `leading-6`으로 읽기성을 확보한다.

## Density와 Spacing
기본 density:
- Page padding: `px-6 py-4`
- Card padding: `p-4` 또는 큰 form에서 `p-6`
- Toolbar height: compact한 `h-9` control 기준
- Form field gap: `gap-2`
- Section gap: `gap-4`, 큰 구획은 `gap-6`

규칙:
- 같은 depth의 card는 같은 radius/padding/border를 사용한다.
- `rounded-lg`, `rounded-xl`, `rounded-2xl`을 한 영역에서 섞지 않는다.
- 업무형 화면은 큰 shadow보다 `border bg-card`를 우선한다.
- 시각 구획은 border, spacing, muted surface 순서로 해결하고 과한 배경색을 피한다.

## 컴포넌트 패턴
### Button
- Primary action: 한 영역에 하나만 둔다.
- Secondary action: `variant="outline"` 또는 `variant="secondary"`를 우선한다.
- Destructive action: `variant="destructive"` 또는 별도 destructive section으로 분리한다.
- Icon-only button: accessible label을 제공한다.

### Card
- 정보 묶음의 기본 surface는 `rounded-2xl border bg-card`.
- card header/body가 있으면 header는 `border-b px-4 py-3`, body는 `p-4`.
- card 안에 card를 중첩하기보다 section/divider/list row를 사용한다.

### Table/List
- Header는 compact하고 sticky가 필요하면 배경과 border를 반드시 둔다.
- Row hover는 `hover:bg-muted/50`.
- 선택 상태는 `bg-accent text-accent-foreground` 또는 명확한 left border/icon을 함께 사용한다.
- 숫자/날짜/상태 column은 정렬과 폭을 일관되게 유지한다.

### Form
- Label, input, helper/error text를 한 field group으로 둔다.
- Validation error는 `text-destructive`와 설명 텍스트를 함께 제공한다.
- 저장/취소 action은 form 하단 또는 sticky action bar에 모은다.
- 위험한 설정은 별도 section으로 분리한다.

### Dialog/Sheet
- Dialog는 하나의 의사결정 또는 짧은 form에만 사용한다.
- 긴 편집/탐색은 page 또는 sheet를 우선한다.
- Footer action 순서는 cancel/secondary 왼쪽, primary/destructive 오른쪽을 기본으로 한다.

## 상태 UX
모든 데이터 UI는 아래 상태를 고려한다.

- Loading: skeleton/spinner와 현재 작업 문구
- Empty: 원인 + 다음 행동 1개
- Error: 실패 원인 요약 + 재시도/복구 행동
- Disabled: 비활성 이유가 불명확하면 helper text 제공
- Selected: 색상 외에 border/icon/font weight 등 보조 단서 제공
- Pending mutation: 중복 클릭 방지와 진행 중 label 제공

금지:
- loading 중 빈 흰 화면
- empty와 error를 같은 문구로 처리
- toast만 띄우고 화면 상태를 갱신하지 않는 처리

## 접근성
- interactive element는 keyboard focus가 보여야 한다.
- icon-only action은 `aria-label` 또는 screen reader text를 둔다.
- form input은 label과 연결한다.
- 색상만으로 상태를 구분하지 않는다.
- modal/dialog는 제목과 설명을 제공한다.
- hover-only 정보는 keyboard/focus에서도 접근 가능해야 한다.

## Dark Mode
- 새 UI는 `dark:`를 직접 남발하기보다 semantic token으로 먼저 해결한다.
- 커스텀 surface를 만들면 light/dark 대비를 함께 확인한다.
- chart/status 색은 `--chart-*`, `--primary`, `--destructive` 등 토큰 기반을 우선한다.

## 아이콘과 시각 장식
- 기본 아이콘은 `lucide-react` 또는 기존 파일의 icon library를 유지한다.
- 한 화면에서 icon size는 `size-4`를 기본으로 하고, 주요 KPI/empty state만 크게 쓴다.
- decorative icon은 정보 계층을 방해하지 않게 `text-muted-foreground`를 우선한다.
- 애니메이션은 상태 전환 이해를 돕는 경우에만 사용한다.

## 작업 순서
1. 화면 목적과 primary action을 식별한다.
2. `compose-frontend-layout`으로 layout/scroll owner를 먼저 확정한다.
3. surface/card/table/form/dialog 패턴을 고른다.
4. token, typography, spacing, state UX를 적용한다.
5. accessibility와 dark mode를 점검한다.
6. import/export 경계는 `safe-file-edit-output` 기준으로 확인한다.

## 최종 점검 체크리스트
- shadcn/Radix primitive를 우선 사용했는가?
- raw color/inline style 없이 token으로 표현 가능한가?
- primary action이 명확하고 과도하게 많지 않은가?
- loading/empty/error/disabled/selected 상태가 있는가?
- 같은 depth의 card/table/form spacing이 일관적인가?
- keyboard focus와 accessible label이 유지되는가?
- dark mode에서 대비가 무너지지 않는가?
- layout/scroll 문제를 시각 patch로 우회하지 않았는가?

## 검증
UI 변경 후 가능하면 `ui-consistency-audit` skill을 사용해 아래 명령을 실행한다.

```bash
scripts/agent/check_ui_consistency.sh
```
