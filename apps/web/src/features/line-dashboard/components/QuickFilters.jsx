// src/features/line-dashboard/components/QuickFilters.jsx
import * as React from "react"
import { IconChevronDown } from "@tabler/icons-react"

import { cn } from "@/lib/utils"
import { QuickFilterSections } from "./QuickFilterSections"

export function QuickFilters({
  sections = [],
  filters = {},
  onToggle,
  onClear,
  activeCount,
  globalFilterValue,
  onGlobalFilterChange,
  globalFilterPlaceholder = "Search rows",
  statusSidebar = null,
  trailingControls = null,
}) {
  const hasSections = sections.length > 0
  const showGlobalFilter = typeof onGlobalFilterChange === "function"
  const showContainer = hasSections || showGlobalFilter || Boolean(trailingControls)
  const hasGlobalValue = showGlobalFilter && Boolean(globalFilterValue)
  const [isCollapsed, setIsCollapsed] = React.useState(false)

  const handleToggleCollapse = () => setIsCollapsed((previous) => !previous)

  const handleClearAll = () => {
    onClear?.()
    if (showGlobalFilter) onGlobalFilterChange?.("")
  }

  if (!showContainer) return null

  return (
    <fieldset
      className={cn(
        "flex flex-col rounded-lg",
        isCollapsed ? "px-3 border-0" : "gap-3 border p-3"
      )}
    >
      <legend className="flex items-center justify-between gap-3 px-1 text-xs font-semibold tracking-wide text-muted-foreground">
        <button
          type="button"
          onClick={handleToggleCollapse}
          aria-expanded={!isCollapsed}
          className="flex items-center gap-1 text-left text-xs font-semibold tracking-wide text-muted-foreground transition-colors hover:text-foreground"
        >
          <span>Quick Filters</span>
          <IconChevronDown
            aria-hidden
            className={cn(
              "size-4 transition-transform",
              !isCollapsed ? "-rotate-180" : "rotate-0"
            )}
          />
        </button>

        {(activeCount > 0 || hasGlobalValue) && (
          <button
            type="button"
            onClick={handleClearAll}
            className="flex items-center rounded-md  bg-background px-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            🧹필터초기화
          </button>
        )}
      </legend>

      {!isCollapsed && (
        <QuickFilterSections
          sections={sections}
          filters={filters}
          onToggle={onToggle}
          statusSidebar={statusSidebar}
          trailingControls={trailingControls}
          globalFilterValue={globalFilterValue}
          onGlobalFilterChange={onGlobalFilterChange}
          globalFilterPlaceholder={globalFilterPlaceholder}
        />
      )}
    </fieldset>
  )
}

export { QuickFilterFavorites } from "./QuickFilterFavorites"
