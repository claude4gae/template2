// 앱스토어 필터 패널
import { Plus, Search, X } from "lucide-react"

import { CATEGORY_OPTIONS } from "./AppFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"

export function AppFilters({
  totalApps,
  query,
  onQueryChange,
  category,
  categories,
  categoryCounts,
  onCategoryChange,
  onReset,
  onCreate,
  isCreating,
}) {
  const categoryLabel = (option) => (option === "all" ? "전체" : option)
  const categoryCount = (option) => (option === "all" ? totalApps : categoryCounts?.[option] ?? 0)
  const categorySet = new Set(categories)
  const categoryOrderSet = new Set(CATEGORY_OPTIONS)
  const orderedCategories = [
    ...(categorySet.has("all") ? ["all"] : []),
    ...CATEGORY_OPTIONS.filter((option) => categorySet.has(option)),
    ...categories.filter((option) => option !== "all" && !categoryOrderSet.has(option)),
  ]

  return (
    <div className="grid h-full min-h-0 grid-rows-[auto_1fr] gap-2">
      {/* 상단: 요약 + 주요 액션 */}
      <Card className="rounded-2xl border bg-card shadow-sm">
        <CardHeader className="space-y-1 pb-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="rounded-full">
                Appstore
              </Badge>
              <span className="text-xs text-muted-foreground">{totalApps} apps</span>
            </div>

            <Button
              variant="default"
              size="sm"
              onClick={onCreate}
              disabled={isCreating}
              className="gap-1"
              type="button"
            >
              <Plus className="size-4" />
              앱 등록
            </Button>
          </div>

          <CardTitle className="text-base">앱 등록 및 탐색</CardTitle>
          <CardDescription className="text-sm">
            Etch 기술팀에서 사용하는 앱을 빠르게 찾고 관리합니다.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* 하단: 검색 + 필터 */}
      <Card className="min-h-0 rounded-2xl border bg-card shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="text-base">검색 및 필터</CardTitle>
              <CardDescription className="flex flex-wrap gap-2">
                <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
                  {totalApps}개 앱
                </span>
                <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
                  {Math.max(categories.length - 1, 0)}개 카테고리
                </span>
              </CardDescription>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              type="button"
              className="h-8 px-2 text-xs text-muted-foreground"
            >
              초기화
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex min-h-0 flex-1 flex-col gap-3">
          {/* 검색 */}
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="앱 이름, 설명, 카테고리 검색"
              className="h-10 pl-9 pr-9"
            />
            {query ? (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onQueryChange("")}
                type="button"
                className="absolute right-1 top-1/2 size-8 -translate-y-1/2 text-muted-foreground"
                aria-label="검색어 지우기"
              >
                <X className="size-4" />
              </Button>
            ) : null}
          </div>

          <Separator />

          {/* 카테고리 목록 */}
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">카테고리</div>
            <div className="text-xs text-muted-foreground">선택: {categoryLabel(category)}</div>
          </div>

          <div className="min-h-0 overflow-y-auto rounded-lg border bg-background">
            <ul className="divide-y">
              {orderedCategories.map((option) => {
                const isActive = option === category
                return (
                  <li key={option}>
                    <button
                      type="button"
                      onClick={() => onCategoryChange(option)}
                      className={[
                        "flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm",
                        "transition-colors",
                        isActive
                          ? "bg-muted/60"
                          : "hover:bg-muted/40",
                      ].join(" ")}
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={[
                            "h-4 w-1 rounded-full",
                            isActive ? "bg-primary" : "bg-transparent",
                          ].join(" ")}
                          aria-hidden="true"
                        />
                        <span className={isActive ? "font-medium text-foreground" : "text-foreground"}>
                          {categoryLabel(option)}
                        </span>
                      </div>

                      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                        {categoryCount(option)}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
