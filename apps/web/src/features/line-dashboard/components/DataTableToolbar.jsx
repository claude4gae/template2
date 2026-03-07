// src/features/line-dashboard/components/DataTableToolbar.jsx
import { IconChevronDown, IconDatabase, IconRefresh } from "@tabler/icons-react"

import { cn } from "@/lib/utils"
import { Button } from "components/ui/button"
import { QuickFilterFavorites } from "./QuickFilterFavorites"

const LINE_FILTER_MODE_TARGET_USER_SDWT = "target_user_sdwt_prod"
const LINE_FILTER_MODE_USER_SDWT = "user_sdwt_prod"
const LINE_FILTER_MODE_SDWT = "sdwt_prod"

const LINE_FILTER_MODE_OPTIONS = [
  {
    value: LINE_FILTER_MODE_TARGET_USER_SDWT,
    labelKey: "lineFilterModeTargetUserSdwt",
  },
  {
    value: LINE_FILTER_MODE_USER_SDWT,
    labelKey: "lineFilterModeUserSdwt",
  },
  {
    value: LINE_FILTER_MODE_SDWT,
    labelKey: "lineFilterModeSdwt",
  },
]

/**
 * 테이블 상단의 타이틀, 즐겨찾기, 새로고침 버튼을 묶어둔 헤더입니다.
 * - DataTable은 상태 계산에 집중하고, 이 컴포넌트는 UI 조립만 담당합니다.
 */
export function DataTableToolbar({
  lineId,
  labels,
  lastUpdatedLabel,
  lineFilterMode,
  onChangeLineFilterMode,
  isRefreshing,
  onRefresh,
  favorites,
}) {
  const {
    filters,
    favorites: favoriteList,
    onSaveFavorite,
    onUpdateFavorite,
    onApplyFavorite,
    onDeleteFavorite,
    resetSignal,
  } = favorites ?? {}
  const selectedOption = LINE_FILTER_MODE_OPTIONS.find((option) => option.value === lineFilterMode)
  const selectedLabel =
    selectedOption && labels?.[selectedOption.labelKey]
      ? labels[selectedOption.labelKey]
      : labels?.lineFilterModeTargetUserSdwt ?? "기본"

  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-lg font-semibold">
          <IconDatabase className="size-5" />
          {lineId} {labels.titleSuffix}
          <span
            className="ml-2 text-[10px] font-normal text-muted-foreground self-end"
            aria-live="polite"
          >
            {labels.updated} {lastUpdatedLabel || "-"}
          </span>
        </div>
      </div>

      <div className="ml-auto flex flex-wrap items-end gap-2">
        <div className="flex flex-col items-start gap-1">
          <span className="pl-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Line Filter
          </span>
          <div className="relative">
            <select
              value={lineFilterMode}
              onChange={(event) => onChangeLineFilterMode?.(event.target.value)}
              className={cn(
                "quick-filter-select h-8 w-44 appearance-none rounded-md border border-input bg-background px-3 pr-8 text-xs font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-1 focus:ring-ring"
              )}
              aria-label="Line Filter"
              title={selectedLabel}
            >
              {LINE_FILTER_MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {labels[option.labelKey]}
                </option>
              ))}
            </select>
            <IconChevronDown
              className="pointer-events-none absolute right-2 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
          </div>
        </div>
        <QuickFilterFavorites
          filters={filters}
          favorites={favoriteList}
          onSaveFavorite={onSaveFavorite}
          onUpdateFavorite={onUpdateFavorite}
          onApplyFavorite={onApplyFavorite}
          onDeleteFavorite={onDeleteFavorite}
          resetSignal={resetSignal}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          className="gap-1"
          aria-label={labels.refresh}
          title={labels.refresh}
          aria-busy={isRefreshing}
        >
          <IconRefresh className={cn("size-3", isRefreshing && "animate-spin")} />
          {labels.refresh}
        </Button>
      </div>
    </div>
  )
}
