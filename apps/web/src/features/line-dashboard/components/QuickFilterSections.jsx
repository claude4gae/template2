// src/features/line-dashboard/components/QuickFilterSections.jsx
import { IconChevronDown } from "@tabler/icons-react"

import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { GlobalFilter } from "./GlobalFilter"
import { MainStepDropdownSection } from "./filters/MainStepDropdownSection"
import { QuickFilterFieldset } from "./filters/QuickFilterFieldset"
import { RecentHoursQuickFilterSection } from "./filters/RecentHoursQuickFilterSection"
import { isMultiSelectFilter } from "../utils/dataTableQuickFilters"

const DROPDOWN_SECTION_KEYS = new Set([
  "sdwt_prod",
  "sample_type",
  "sample_group",
  "user_sdwt_prod",
  "main_step",
])
const WIDE_DROPDOWN_SECTION_KEYS = new Set(["sample_type", "sample_group"])
const CHECKBOX_SECTION_KEYS = new Set(["my_sop"])

const isNil = (value) => value === null || value === undefined

const getDropdownWidthClass = (sectionKey) =>
  WIDE_DROPDOWN_SECTION_KEYS.has(sectionKey) ? "w-56" : "w-40"

export { QuickFilterFieldset }

export function QuickFilterSections({
  sections,
  filters,
  onToggle,
  statusSidebar = null,
  trailingControls = null,
  globalFilterValue,
  onGlobalFilterChange,
  globalFilterPlaceholder = "Search rows",
}) {
  const hasSections = Array.isArray(sections) && sections.length > 0
  const showGlobalFilter = typeof onGlobalFilterChange === "function"
  if (!hasSections && !showGlobalFilter && !trailingControls) return null

  const sectionBlocks = hasSections
    ? sections.map((section) => (
      <QuickFilterSection
        key={section.key}
        section={section}
        filters={filters}
        onToggle={onToggle}
      />
    ))
    : []

  if (showGlobalFilter) {
    sectionBlocks.push(
      <QuickFilterFieldset
        key="__global__"
        legendId="legend-global-filter"
        label="검색"
      >
        <div className="w-52 sm:w-64 lg:w-80">
          <GlobalFilter
            value={globalFilterValue}
            onChange={onGlobalFilterChange}
            placeholder={globalFilterPlaceholder}
          />
        </div>
      </QuickFilterFieldset>
    )
  }

  if (trailingControls) {
    sectionBlocks.push(
      <div key="__trailing_controls__" className="flex items-end">
        {trailingControls}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
      {statusSidebar ? (
        <div className="w-full flex-shrink-0 lg:max-w-[200px]">{statusSidebar}</div>
      ) : null}
      <div className="flex flex-1 flex-wrap items-start gap-2">
        {sectionBlocks}
      </div>
    </div>
  )
}

function QuickFilterSection({ section, filters, onToggle }) {
  const isMulti = isMultiSelectFilter(section.key)
  const current = filters?.[section.key]
  const selectedValues = getSelectedValues(isMulti, current)
  const allSelected = isMulti ? selectedValues.length === 0 : isNil(current)
  const legendId = `legend-${section.key}`

  if (section.key === "recent_hours") {
    return (
      <RecentHoursQuickFilterSection
        key={section.key}
        section={section}
        legendId={legendId}
        current={current}
        onToggle={onToggle}
      />
    )
  }

  if (CHECKBOX_SECTION_KEYS.has(section.key)) {
    return (
      <CheckboxQuickFilterSection
        key={section.key}
        section={section}
        legendId={legendId}
        checked={Boolean(current)}
        onToggle={onToggle}
      />
    )
  }

  if (DROPDOWN_SECTION_KEYS.has(section.key)) {
    if (section.key === "main_step") {
      return (
        <MainStepDropdownSection
          key={section.key}
          section={section}
          legendId={legendId}
          current={current}
          onToggle={onToggle}
        />
      )
    }
    return (
      <DropdownQuickFilterSection
        key={section.key}
        section={section}
        legendId={legendId}
        current={current}
        isMulti={isMulti}
        selectedValues={selectedValues}
        onToggle={onToggle}
      />
    )
  }

  return (
    <ButtonQuickFilterSection
      key={section.key}
      section={section}
      legendId={legendId}
      allSelected={allSelected}
      selectedValues={selectedValues}
      onToggle={onToggle}
    />
  )
}

function CheckboxQuickFilterSection({ section, legendId, checked, onToggle }) {
  const inputId = `${section.key}-checkbox`

  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <label
        htmlFor={inputId}
        className="flex h-8 items-center gap-2 text-xs font-medium text-foreground"
      >
        <input
          id={inputId}
          type="checkbox"
          className="h-4 w-4 accent-primary"
          checked={checked}
          onChange={(event) =>
            onToggle(section.key, event.target.checked ? true : null, { forceValue: true })
          }
        />
        <div className="flex flex-col items-center justify-center leading-tight">
          {section.userId ? (
            <div className="text-[11px] font-normal text-muted-foreground">
              {section.userId}
            </div>
          ) : null}
        </div>
      </label>
    </QuickFilterFieldset>
  )
}

function DropdownQuickFilterSection({
  section,
  legendId,
  current,
  onToggle,
  isMulti,
  selectedValues,
}) {
  const resolvedSelectedValues = selectedValues ?? getSelectedValues(isMulti, current)
  const dropdownWidthClass = getDropdownWidthClass(section.key)

  if (isMulti) {
    const hasDropdownValue = resolvedSelectedValues.length > 0
    const displayValue =
      resolvedSelectedValues.length === 0
        ? "전체"
        : `${resolvedSelectedValues.length}개 선택`

    return (
      <QuickFilterFieldset legendId={legendId} label={section.label}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className={cn(
                "flex h-8 items-center justify-between rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring",
                dropdownWidthClass,
                hasDropdownValue && "border-primary bg-primary/10 text-primary"
              )}
            >
              <span className="truncate">{displayValue}</span>
              <IconChevronDown className="size-4 shrink-0" />
            </button>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            align="start"
            className={cn("p-1", dropdownWidthClass)}
          >
            <DropdownMenuItem
              className="text-xs"
              onSelect={(event) => {
                event.preventDefault()
                onToggle(section.key, null, { forceValue: true })
              }}
            >
              전체
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {section.options.map((option) => {
              const isChecked = resolvedSelectedValues.includes(option.value)
              return (
                <DropdownMenuCheckboxItem
                  key={`${section.key}-${String(option.value)}`}
                  checked={isChecked}
                  onCheckedChange={() => onToggle(section.key, option.value)}
                  onSelect={(event) => event.preventDefault()}
                  className={cn(
                    "text-xs",
                    "data-[state=checked]:bg-primary/10 data-[state=checked]:text-primary"
                  )}
                >
                  {option.label}
                </DropdownMenuCheckboxItem>
              )
            })}
          </DropdownMenuContent>
        </DropdownMenu>
      </QuickFilterFieldset>
    )
  }

  const hasDropdownValue = !isNil(current) && String(current).length > 0

  const handleChange = (event) => {
    onToggle(section.key, event.target.value || null)
  }

  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <select
        value={current ?? ""}
        onChange={handleChange}
        className={cn(
          "quick-filter-select h-8 rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring",
          dropdownWidthClass,
          hasDropdownValue && "border-primary bg-primary/10 text-primary"
        )}
      >
        <option value="">전체</option>
        {section.options.map((option) => (
          <option key={`${section.key}-${String(option.value)}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </QuickFilterFieldset>
  )
}

function ButtonQuickFilterSection({
  section,
  legendId,
  selectedValues,
  allSelected,
  onToggle,
}) {
  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <div className="flex flex-wrap items-center">
        <button
          type="button"
          onClick={() => onToggle(section.key, null)}
          className={cn(
            "h-8 px-3 text-xs font-medium border border-input bg-background",
            "-ml-px first:ml-0 first:rounded-l last:rounded-r",
            "transition-colors",
            allSelected
              ? "relative z-[1] border-primary bg-primary/10 text-primary"
              : "hover:bg-muted"
          )}
        >
          전체
        </button>

        {section.options.map((option) => {
          const isActive = selectedValues.includes(option.value)
          return (
            <button
              key={`${section.key}-${String(option.value)}`}
              type="button"
              onClick={() => onToggle(section.key, option.value)}
              className={cn(
                "h-8 px-3 text-xs font-medium border border-input bg-background",
                "-ml-px first:ml-0 first:rounded-l last:rounded-r",
                "transition-colors",
                isActive
                  ? "relative z-[1] border-primary bg-primary/10 text-primary"
                  : "hover:bg-muted"
              )}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    </QuickFilterFieldset>
  )
}

function getSelectedValues(isMulti, current) {
  if (isMulti) {
    return Array.isArray(current) ? current : []
  }
  return isNil(current) ? [] : [current]
}
