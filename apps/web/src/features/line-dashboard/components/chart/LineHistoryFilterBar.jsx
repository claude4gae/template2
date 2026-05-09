import { IconRefresh } from "@tabler/icons-react"
import { CalendarIcon, FilterIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { DateRangeCalendar } from "@/components/common"
import { cn } from "@/lib/utils"
import { BIN_OPTIONS, DIMENSION_OPTIONS } from "../../utils/lineHistoryConfig"
import { formatRangeLabel } from "../../utils/lineHistoryTransforms"

export function LineHistoryFilterBar({
  dateRange,
  today,
  defaultRange,
  isCalendarOpen,
  calendarButtonRef,
  calendarPopoverRef,
  onCalendarToggle,
  onCalendarClose,
  onDateRangeSelect,
  binMode,
  onBinChange,
  activeDimension,
  activeDimensionLabel,
  dimensionRecords,
  onDimensionChange,
  activeDimensionTotals,
  activeCategories,
  hasFilterSelection,
  onCategoryToggle,
  onClearActiveCategories,
  hasAnyActiveFilter,
  isLoading,
  onResetAllFilters,
  onRefresh,
}) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Button
              ref={calendarButtonRef}
              variant="outline"
              size="sm"
              className="h-8 min-w-[220px] justify-between px-3 text-xs"
              onClick={onCalendarToggle}
              aria-expanded={isCalendarOpen}
              aria-haspopup="dialog"
            >
              <span className="text-[11px] text-muted-foreground">
                조회 기간
              </span>
              <span className="flex items-center gap-2">
                <CalendarIcon className="size-4" />
                {formatRangeLabel(dateRange)}
              </span>
            </Button>
            {isCalendarOpen && (
              <div
                ref={calendarPopoverRef}
                className="absolute left-0 top-full z-50 mt-2 rounded-lg border bg-popover p-3 shadow-lg"
              >
                <DateRangeCalendar
                  selected={dateRange}
                  defaultMonth={dateRange?.from ?? today}
                  onSelect={onDateRangeSelect}
                  disableAfter={today}
                />
                <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>기본값: 최근 한 달</span>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 px-2 text-xs"
                      onClick={() => onDateRangeSelect(defaultRange)}
                    >
                      기간 초기화
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-7 px-2 text-xs"
                      onClick={onCalendarClose}
                    >
                      닫기
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-muted-foreground">
              X축 Bin
            </span>
            <div className="flex items-center gap-[2px] rounded-md border bg-muted/60 p-[2px]">
              {BIN_OPTIONS.map((option) => {
                const isActive = binMode === option.value
                return (
                  <Button
                    key={option.value}
                    size="sm"
                    variant={isActive ? "secondary" : "ghost"}
                    className="h-8 px-3 text-xs"
                    onClick={() => onBinChange(option.value)}
                  >
                    {option.label}
                  </Button>
                )
              })}
            </div>
          </div>

          <div className="flex items-center gap-1">
            <span className="text-[11px] text-muted-foreground">
              분류 기준
            </span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 px-3 text-xs"
                >
                  <span className="font-medium">
                    {activeDimensionLabel}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                <DropdownMenuLabel>차트 레전드 기준 선택</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {DIMENSION_OPTIONS.map((option) => {
                  const records = dimensionRecords?.[option.value]?.records
                  const hasRecords =
                    Array.isArray(records) && records.length > 0
                  return (
                    <DropdownMenuItem
                      key={option.value}
                      disabled={!hasRecords}
                      className={
                        !hasRecords ? "cursor-not-allowed opacity-60" : ""
                      }
                      onSelect={(event) => {
                        event.preventDefault()
                        if (!hasRecords) return
                        onDimensionChange(option.value)
                      }}
                    >
                      {option.label}
                      {!hasRecords && (
                        <span className="ml-1 text-[10px] text-muted-foreground">
                          (데이터 없음)
                        </span>
                      )}
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {activeDimension && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <FilterIcon className="size-4" />
                  <span>{activeDimensionLabel} 카테고리 필터</span>
                  {hasFilterSelection && (
                    <span className="rounded bg-muted px-1 text-[11px] text-muted-foreground">
                      {activeCategories.length}
                    </span>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-64 max-h-80 overflow-y-auto">
                <DropdownMenuLabel>
                  {activeDimensionLabel} 카테고리 필터
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                {activeDimensionTotals.map(([category]) => (
                  <DropdownMenuCheckboxItem
                    key={category}
                    checked={activeCategories.includes(category)}
                    onSelect={(event) => event.preventDefault()}
                    onCheckedChange={(checked) =>
                      onCategoryToggle(
                        activeDimension,
                        category,
                        checked === true,
                      )
                    }
                  >
                    {category}
                  </DropdownMenuCheckboxItem>
                ))}
                {hasFilterSelection && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onSelect={(event) => event.preventDefault()}
                      onClick={onClearActiveCategories}
                    >
                      {activeDimensionLabel} 필터 초기화
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={onResetAllFilters}
            disabled={!hasAnyActiveFilter || isLoading}
            className="gap-1 text-xs"
            aria-label="필터 전체 초기화"
            title="날짜 / 집계 단위 / 카테고리 / 숨김 시리즈 모두 초기화"
          >
            <FilterIcon className="size-4" />
            필터 전체 초기화
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={onRefresh}
            disabled={isLoading}
            className="gap-1"
            aria-label="refresh"
            title="refresh"
          >
            <IconRefresh
              className={cn("size-4", isLoading && "animate-spin")}
            />
            Refresh
          </Button>
        </div>
      </div>
    </div>
  )
}
