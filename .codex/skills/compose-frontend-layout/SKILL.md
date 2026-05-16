---
name: compose-frontend-layout
description: |
  Desktop-first 실무형 React 프론트엔드 레이아웃 스킬.
  page skeleton, fixed+scroll, two-pane/table/dashboard/settings 패턴을
  일관되게 적용하고 스크롤/높이/padding 충돌을 방지한다.
---

# compose-frontend-layout

## 목적
이 스킬은 desktop 중심 업무형 UI를 일관되게 만들기 위한 것이다.

목표:
- 스크롤 충돌 방지
- 높이 구조 안정화
- padding/gap/pane/card 규칙 통일
- list/detail/table/dashboard/settings 화면을 예측 가능한 방식으로 구성
- 임의 레이아웃 생성을 줄이고 승인된 패턴 중심으로 구성

마케팅 페이지가 아니라 실무형 앱 화면 구성을 우선 대상으로 한다.
색상, 타이포그래피, 컴포넌트 상태, empty/loading/error UX는 `product-ui-design-system` skill을 함께 따른다.

## 적용 범위
적용 대상:
- admin page
- dashboard
- data table page
- filter + result page
- list + detail page
- settings/form page
- inspector/explorer/workbench page

비적용 대상:
- landing page
- brochure page
- highly animated showcase UI

## 사용할 때
- 새로운 page를 추가할 때
- 기존 page의 높이/스크롤 구조를 수정할 때
- list-detail, fixed-header, filter+list 패턴을 구현할 때
- nested scroll 문제를 해결할 때

## Desktop-First 규칙
- 기본은 desktop 기준으로 레이아웃을 설계한다.
- 신규 업무형 페이지는 breakpoint 없이 시작하는 것을 우선한다.
- 기존 코드에 breakpoint(`sm:`, `md:`, `lg:`, `xl:`)가 이미 있으면 동작을 유지하고 필요한 범위만 수정한다.
- 반응형 재구성은 사용자의 명시 요청 또는 명확한 요구사항이 있을 때만 추가한다.

## 가장 중요한 실행 순서
1. 페이지 유형을 먼저 식별한다.
2. vertical scroll owner를 먼저 식별한다.
3. fixed area/sticky area/scroll area를 분리한다.
4. 승인된 패턴 중 하나를 선택한다.
5. outer shell부터 JSX를 만든다.
6. 마지막에 nested scroll/padding/height ownership을 점검한다.

이 순서를 바꾸지 않는다.

## 필수 규칙
1) 한 region 안에는 같은 축 스크롤 컨테이너를 하나만 둔다.
- 같은 화면 영역에서 y-scroll은 하나만 둔다.
- pane이 분리된 경우(예: list/detail)는 서로 다른 region으로 취급한다.

2) scrollable element에는 반드시 `min-h-0`
- `flex` 또는 `grid` 하위에서 스크롤되는 요소에는 반드시 `min-h-0`를 둔다.

3) 가로로 줄어드는 pane에는 반드시 `min-w-0`
- split pane, table area, detail area에는 `min-w-0`를 둔다.

4) outer layout이 높이와 구조를 소유한다
- page shell이 전체 높이와 row/column 구조를 담당한다.
- child component는 내부 content만 담당한다.

5) page-level padding은 layout이 담당한다
- page padding
- section gap
- outer spacing
- work-area spacing

6) child component는 내부 padding만 담당한다
- card body padding
- 내부 정렬
- 내부 gap
- 내부 border/divider

7) Flex는 1차원, Grid는 2차원
Flex:
- header row
- toolbar
- button row
- inline controls

Grid:
- page shell
- filter + result
- list + detail
- dashboard
- form sections
- fixed + scroll 구조

8) sticky는 얇은 bar에만 사용한다
허용:
- page sub-header
- filter toolbar
- table toolbar
- detail action bar

금지:
- 큰 본문 전체를 sticky로 만드는 것
- sticky를 여러 겹 겹치는 것
- 배경/경계선 없는 sticky

9) `h-screen`은 app root에서만 사용한다
- app root shell에서는 사용 가능
- route page 내부에서 다시 `h-screen`을 쓰지 않는다
- nested `h-screen`은 금지한다

10) 임의 spacing/width 값을 남발하지 않는다
- 정해진 gap/padding/token을 사용한다.
- 불필요한 arbitrary value를 만들지 않는다.
- 디자인 토큰/CSS 변수 기반의 폭 제어는 필요한 경우 허용한다.

Overlay 예외:
- modal/popover/drawer 내부 스크롤은 허용한다.
- overlay 스크롤은 page 스크롤과 다른 region으로 취급한다.

## 높이 소유 규칙
1) app root

앱 전체 viewport를 소유하는 최상위 shell에서만 `h-screen`을 사용한다.

```jsx
<div className="h-screen flex flex-col">
  <header className="shrink-0 border-b">...</header>
  <main className="flex-1 min-h-0 overflow-hidden">...</main>
</div>
```

2) route page

route 내부 페이지는 `h-full`로 부모 높이를 따른다.

```jsx
<div className="flex h-full min-h-0 flex-col">
  <div className="shrink-0 px-6 py-4">Page Header</div>
  <div className="flex-1 min-h-0 overflow-hidden px-6 pb-6">Work Area</div>
</div>
```

## 기본 토큰
- page shell: `flex h-full min-h-0 flex-col`
- page header: `shrink-0 px-6 py-4`
- work area: `flex-1 min-h-0 overflow-hidden px-6 pb-6`
- 기본 gap: `gap-4`
- card: `rounded-2xl border bg-card`
- card header: `shrink-0 border-b px-4 py-3`
- card body: `p-4`
- scroll owner: `min-h-0 overflow-y-auto`
- pane: `min-h-0 min-w-0`
- sticky bar: `sticky top-0 z-10 border-b bg-background/95 backdrop-blur`

## 승인된 패턴
이 스킬은 아래 패턴만 사용한다.

### 패턴 A) top-fixed / bottom-scroll
```jsx
<div className="grid h-full min-h-0 grid-rows-[auto,1fr] gap-4">
  <div className="shrink-0">Fixed Area</div>
  <div className="min-h-0 overflow-y-auto">Scroll Area</div>
</div>
```

사용 예:
- 상단 필터 + 하단 결과
- 상단 요약 + 하단 본문
- 상단 액션 + 하단 목록

규칙:
- 상단은 compact하게 유지한다.
- 많은 내용을 fixed area에 넣지 않는다.

### 패턴 B) sticky toolbar + content
```jsx
<div className="grid h-full min-h-0 grid-rows-[auto,1fr]">
  <div className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">Toolbar</div>
  <div className="min-h-0 overflow-y-auto">Content</div>
</div>
```

규칙:
- sticky는 content scroll owner 안에서만 동작하게 한다.
- sticky parent의 overflow 문맥을 확인한다.

### 패턴 C) two-pane list-detail
```jsx
<div className="grid h-full min-h-0 min-w-0 grid-cols-[360px,1fr] gap-4">
  <section className="grid min-h-0 min-w-0 grid-rows-[auto,1fr] gap-3">
    <div className="shrink-0">Filters / Summary</div>
    <div className="min-h-0 overflow-y-auto">List</div>
  </section>

  <section className="min-h-0 min-w-0 overflow-y-auto">Detail</section>
</div>
```

사용 예:
- 왼쪽 리스트 / 오른쪽 상세
- 왼쪽 검색 / 오른쪽 미리보기

규칙:
- 왼쪽 pane은 고정폭 또는 제한된 폭을 사용한다.
- 오른쪽 detail에는 `min-w-0`를 반드시 둔다.
- 좌/우 pane 모두 많은 데이터가 있는 경우에만 양쪽 y-scroll을 분리한다.

### 패턴 D) dashboard
```jsx
<div className="flex h-full min-h-0 flex-col gap-4">
  <section className="grid grid-cols-4 gap-4">KPI Cards</section>

  <section className="grid flex-1 min-h-0 min-w-0 grid-cols-[2fr,1fr] gap-4">
    <div className="min-h-0 min-w-0 overflow-hidden rounded-2xl border bg-card">Main Panel</div>
    <div className="min-h-0 min-w-0 overflow-hidden rounded-2xl border bg-card">Side Panel</div>
  </section>
</div>
```

규칙:
- KPI는 상단, heavy content는 하단에 둔다.
- card 내부에서 다시 layout을 나눌 때만 추가 grid를 사용한다.

### 패턴 E) table page
```jsx
<div className="grid h-full min-h-0 grid-rows-[auto,1fr] gap-4">
  <div className="shrink-0">Page Header / Filters / Actions</div>

  <div className="min-h-0 min-w-0 overflow-hidden rounded-2xl border bg-card">
    <div className="grid h-full min-h-0 grid-rows-[auto,1fr]">
      <div className="shrink-0 border-b px-4 py-3">Table Toolbar</div>
      <div className="min-h-0 min-w-0 overflow-auto">Table</div>
    </div>
  </div>
</div>
```

규칙:
- wide table은 table shell 안에서만 scroll시킨다.
- page 전체와 table 내부가 동시에 주 scroll owner가 되지 않게 한다.
- table 때문에 page가 가로로 밀리지 않도록 `min-w-0`를 둔다.

### 패턴 F) settings / form
```jsx
<div className="h-full min-h-0 overflow-y-auto">
  <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <section className="rounded-2xl border bg-card p-6">Basic Settings</section>
    <section className="rounded-2xl border bg-card p-6">Advanced Settings</section>
  </div>
</div>
```

규칙:
- 읽기와 입력이 많은 화면은 폭을 제한한다.
- form은 full width보다 constrained width를 우선한다.
- destructive action은 맨 아래 별도 section으로 분리한다.

## 카드 규칙
기본 단위는 card를 우선한다.

기본 card:
```jsx
<div className="rounded-2xl border bg-card">...</div>
```

header/body 분리 card:
```jsx
<div className="rounded-2xl border bg-card">
  <div className="shrink-0 border-b px-4 py-3">Header</div>
  <div className="p-4">Body</div>
</div>
```

규칙:
- 같은 depth의 card는 같은 radius/border/padding을 사용한다.
- card 안에 card를 불필요하게 중첩하지 않는다.
- box-shadow 남용보다 border 기반 구성을 우선한다.

## spacing 규칙
- page padding: `px-6 py-4`
- work-area bottom padding: `pb-6`
- section gap: `gap-4`
- 큰 section 분리: `gap-6`
- 내부 compact gap: `gap-2`, `gap-3`
- 임의 수치(`gap-[13px]`, `p-[22px]`)는 피한다.

## width 규칙
full width 우선:
- dashboard
- table
- workbench
- explorer
- monitoring page

constrained width 우선:
- settings
- form
- detail reading page

허용 예:
- `max-w-5xl`
- `max-w-6xl`
- CSS 변수 기반 pane width

규칙:
- page마다 제각각 다른 max-width를 쓰지 않는다.
- arbitrary width보다 정해진 pane width/token을 우선한다.

## componentization 규칙
같은 레이아웃 패턴이 2회 이상 반복되면 layout component로 승격한다.

- `apps/web/src/components/layout/<LayoutName>.jsx`

허용 예:
- `PageShell`
- `SplitPaneLayout`
- `FilterResultLayout`
- `TablePageLayout`
- `ContentCard`

금지:
- feature 폴더에 범용 layout component 생성
- route 파일 안에서 page shell 직접 복붙
- `apps/web/src/routes/*`에 layout component 신규 생성

## 출력 방식
이 스킬 사용 시 내부 판단 순서는 아래를 따른다.

1. page type
2. scroll owners
3. chosen pattern
4. JSX
5. risk check

시각 디자인 변경이 포함되면 `product-ui-design-system` 기준으로 token/state/accessibility도 함께 점검한다.

## 수정 작업 시 규칙
- 먼저 wrapper 구조를 고친다.
- 그 다음 `overflow-*`, `min-h-0`, `min-w-0`를 바로잡는다.
- 마지막에 padding/gap/card 구조를 정리한다.
- 비즈니스 로직은 가능한 건드리지 않는다.
- 레이아웃 문제를 내부 child patch로 우회하지 않는다.

## 금지사항
- 같은 region에서 중첩된 y-scroll
- `min-h-0` 없는 scroll container
- `min-w-0` 없는 split pane/table pane
- child component가 page-level padding 결정
- route 내부의 nested `h-screen`
- sticky에 배경/경계선 없이 사용
- page마다 제각각 gap/padding/card radius 사용
- 불필요한 wrapper 중첩
- card 안에 card 안에 card 구조 남발

## 최종 점검 체크리스트
- 누가 전체 높이를 소유하는가?
- 누가 주 y-scroll owner인가?
- scroll owner마다 `min-h-0`가 있는가?
- pane마다 `min-w-0`가 있는가?
- page padding과 child padding이 분리되었는가?
- sticky가 필요한 얇은 영역에만 쓰였는가?
- table/list/detail이 승인된 패턴 중 하나를 따르는가?
- nested `h-screen`이 없는가?
- 기존 기능 로직을 불필요하게 건드리지 않았는가?

## 검증
layout 변경 후 가능하면 `ui-consistency-audit` skill을 사용해 아래 명령을 실행한다.

```bash
scripts/agent/check_ui_consistency.sh
```

## 좋은 결과의 기준
- 어디가 고정이고 어디가 스크롤인지 바로 보인다.
- page마다 spacing 감각이 비슷하다.
- list/table/detail/form 화면이 같은 제품처럼 보인다.
- 콘텐츠가 많아져도 쉽게 무너지지 않는다.
- wrapper를 봤을 때 height ownership이 명확하다.
