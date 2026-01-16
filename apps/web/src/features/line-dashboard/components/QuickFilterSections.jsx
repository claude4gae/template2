// src/features/line-dashboard/components/QuickFilterSections.jsx
import * as React from "react"
import { IconCheck, IconChevronDown } from "@tabler/icons-react"

import { cn } from "@/lib/utils"
import { Slider } from "@/components/ui/slider"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { GlobalFilter } from "./GlobalFilter"
import {
  buildMainStepToken,
  isMultiSelectFilter,
  normalizeRecentHoursRange,
  parseMainStepToken,
  RECENT_HOURS_MAX,
} from "../utils/dataTableQuickFilters"
import {
  formatHoursAgo,
  formatRecentHoursRange,
  rangeToSliderPositions,
  RECENT_SLIDER_MAX,
  RECENT_SLIDER_MIN,
  RECENT_SLIDER_STEP,
  sliderPositionsToRange,
} from "../utils/recentHoursSlider"

const DROPDOWN_SECTION_KEYS = new Set([
  "sdwt_prod",
  "sample_type",
  "sample_group",
  "user_sdwt_prod",
  "main_step",
])
const CHECKBOX_SECTION_KEYS = new Set(["my_sop"])
const FIELDSET_CLASS = "flex flex-col rounded-xl px-2"
const EMPTY_OPTIONS = []

const isNil = (value) => value === null || value === undefined

export function QuickFilterFieldset({
  legendId,
  label,
  children,
  className,
  legendClassName,
  isLegendHidden = false,
}) {
  return (
    <fieldset
      className={cn(FIELDSET_CLASS, className)}
      aria-labelledby={legendId}
    >
      <legend
        id={legendId}
        className={cn(
          isLegendHidden
            ? "sr-only"
            : "text-[9px] font-semibold uppercase tracking-wide text-muted-foreground",
          legendClassName
        )}
      >
        {label}
      </legend>
      {children}
    </fieldset>
  )
}

export function QuickFilterSections({
  sections,
  filters,
  onToggle,
  statusSidebar = null,
  globalFilterValue,
  onGlobalFilterChange,
  globalFilterPlaceholder = "Search rows",
}) {
  const hasSections = Array.isArray(sections) && sections.length > 0
  const showGlobalFilter = typeof onGlobalFilterChange === "function"
  if (!hasSections && !showGlobalFilter) return null

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
                "flex h-8 w-40 items-center justify-between rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring",
                hasDropdownValue && "border-primary bg-primary/10 text-primary"
              )}
            >
              <span className="truncate">{displayValue}</span>
              <IconChevronDown className="size-4 shrink-0" />
            </button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="start" className="w-40 p-1">
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
          "quick-filter-select h-8 w-40 rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring",
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

function MainStepDropdownSection({ section, legendId, current, onToggle }) {
  const selectionMap = buildMainStepSelectionMap(current)
  const suffixOptions = Array.isArray(section?.options) ? section.options : EMPTY_OPTIONS
  const firstSelectedSuffix = selectionMap.size > 0 ? Array.from(selectionMap.keys())[0] : null
  const initialSuffix = firstSelectedSuffix ?? null
  const [activeSuffix, setActiveSuffix] = React.useState(initialSuffix)

  React.useEffect(() => {
    if (!suffixOptions.length) {
      setActiveSuffix(null)
      return
    }
    if (activeSuffix && suffixOptions.some((option) => option.value === activeSuffix)) return
    setActiveSuffix(firstSelectedSuffix ?? null)
  }, [activeSuffix, suffixOptions, firstSelectedSuffix])

  const persistSelection = (nextMap) => {
    const tokens = buildMainStepTokensFromSelection(nextMap)
    onToggle(section.key, tokens, { forceValue: true })
  }

  const handleSelectSuffix = (suffix) => {
    const nextMap = new Map(selectionMap)
    const wasSelected = selectionMap.has(suffix)
    if (wasSelected) {
      nextMap.delete(suffix)
    } else {
      nextMap.set(suffix, new Set(["*"]))
    }

    const remainingSuffixes = Array.from(nextMap.keys())
    const nextActive = wasSelected ? remainingSuffixes[0] ?? null : suffix
    setActiveSuffix(nextActive)
    persistSelection(nextMap)
  }

  const handleTogglePrefix = (suffix, prefix) => {
    const nextMap = new Map(selectionMap)
    const currentPrefixes = new Set(nextMap.get(suffix) ?? [])
    const normalizedPrefixes = toggleMainStepPrefix(currentPrefixes, prefix)
    nextMap.set(suffix, normalizedPrefixes)

    persistSelection(nextMap)
  }

  const handleClearAll = () => {
    onToggle(section.key, [], { forceValue: true })
    setActiveSuffix(null)
  }

  const displayValue = getMainStepDisplayValue(selectionMap)

  const activeOption = suffixOptions.find((option) => option.value === activeSuffix)
  const prefixOptions = Array.isArray(activeOption?.prefixes)
    ? [...activeOption.prefixes].sort((a, b) => a.localeCompare(b))
    : []
  const activePrefixes = selectionMap.get(activeSuffix) ?? new Set()
  const hasSelection = selectionMap.size > 0

  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className={cn(
              "flex h-8 w-48 items-center justify-between rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring",
              hasSelection && "border-primary bg-primary/10 text-primary"
            )}
          >
            <span className="truncate">{displayValue}</span>
            <IconChevronDown className="size-4 shrink-0" />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="start" className="w-80 p-2">
          <div className="grid grid-cols-2 gap-2">
	            <div className="rounded-md border p-1">
	              <div className="px-1 pb-1 text-[10px] font-semibold text-muted-foreground">
	                Step선택
	              </div>
	              <div className="flex max-h-52 flex-col gap-1 overflow-y-auto pr-1">
	                {suffixOptions.map((option) => {
	                  const isSelected = selectionMap.has(option.value)
	                  return (
	                    <button
	                      key={option.value}
                      type="button"
                      onClick={(event) => {
                        event.preventDefault()
                        handleSelectSuffix(option.value)
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-md border border-transparent px-2 py-1 text-left text-xs transition-colors",
                        isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                      )}
                    >
                      <span className="flex h-4 w-4 items-center justify-center">
                        {isSelected ? <IconCheck className="size-4 text-primary" aria-hidden /> : null}
                      </span>
                      <span className="truncate">{option.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="rounded-md border p-1">
              <div className="flex items-center justify-between px-1 pb-1 text-[10px] font-semibold text-muted-foreground">
                <span>PRC선택</span>
                <span
                  className={cn(
                    "rounded px-1 py-[2px] text-[10px] font-medium",
                    activeSuffix ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                  )}
                >
                  {activeSuffix ? `STEP ${activeOption?.label ?? activeSuffix}` : "Step 미선택"}
                </span>
              </div>
              {activeSuffix ? (
                <div className="flex max-h-52 flex-col gap-1 overflow-y-auto pr-1">
                  <DropdownMenuCheckboxItem
                    className={cn(
                      "text-xs",
                      "data-[state=checked]:bg-primary/10 data-[state=checked]:text-primary"
                    )}
                    checked={activePrefixes.has("*")}
                    onCheckedChange={() => handleTogglePrefix(activeSuffix, "*")}
                    onSelect={(event) => event.preventDefault()}
                  >
                    전체선택
                  </DropdownMenuCheckboxItem>
                  <DropdownMenuSeparator />
                  {prefixOptions.length === 0 ? (
                    <div className="px-2 py-1 text-[11px] text-muted-foreground">
                      선택 가능한 PRC가 없습니다.
                    </div>
                  ) : (
                    prefixOptions.map((prefix) => (
                      <DropdownMenuCheckboxItem
                        key={`${activeSuffix}-${prefix}`}
                        className={cn(
                          "text-xs",
                          "data-[state=checked]:bg-primary/10 data-[state=checked]:text-primary"
                        )}
                        checked={activePrefixes.has(prefix)}
                        onCheckedChange={() => handleTogglePrefix(activeSuffix, prefix)}
                        onSelect={(event) => event.preventDefault()}
                      >
                        {prefix}
                      </DropdownMenuCheckboxItem>
                    ))
                  )}
                </div>
              ) : (
                <div className="px-2 py-1 text-[11px] text-muted-foreground">
                  Step을 먼저 선택하세요.
                </div>
              )}
            </div>
          </div>

          <div className="mt-2 flex items-center justify-end">
            <button
              type="button"
              className="text-[11px] font-medium text-muted-foreground hover:text-foreground"
              onClick={handleClearAll}
            >
              전체 해제
            </button>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
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

function RecentHoursQuickFilterSection({ section, legendId, current, onToggle }) {
  const [rangeValue, setRangeValue] = React.useState(() =>
    normalizeRecentHoursRange(current)
  )

  React.useEffect(() => {
    setRangeValue(normalizeRecentHoursRange(current))
  }, [current])

  const sliderPositions = rangeToSliderPositions(rangeValue)

  const handleSliderChange = (value) => {
    setRangeValue(normalizeRecentHoursRange(sliderPositionsToRange(value)))
  }

  const handleSliderCommit = (value) => {
    const nextRange = normalizeRecentHoursRange(sliderPositionsToRange(value))
    setRangeValue(nextRange)
    onToggle(section.key, nextRange, { forceValue: true })
  }

  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <div className="flex w-60 flex-col rounded-lg px-3 py-1">
        <div className="flex mt-1 h-2 items-start gap-3">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {formatHoursAgo(RECENT_HOURS_MAX)}
          </span>

          <Slider
            className="flex-1"
            min={RECENT_SLIDER_MIN}
            max={RECENT_SLIDER_MAX}
            step={RECENT_SLIDER_STEP}
            value={sliderPositions}
            onValueChange={handleSliderChange}
            onValueCommit={handleSliderCommit}
            aria-label="최근 시간 범위 선택"
          />

          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            현재
          </span>
        </div>

        <p className=" text-center text-[9px] font-medium text-muted-foreground">
          {formatRecentHoursRange(rangeValue)}
        </p>
      </div>
    </QuickFilterFieldset>
  )
}

function buildMainStepSelectionMap(tokens) {
  const map = new Map()
  const normalizedTokens = Array.isArray(tokens) ? tokens : []
  normalizedTokens.forEach((token) => {
    const parsed = parseMainStepToken(token)
    if (!parsed?.suffix) return
    const prefix = parsed.prefix && parsed.prefix !== "" ? parsed.prefix : "*"
    const set = map.get(parsed.suffix) ?? new Set()
    set.add(prefix)
    map.set(parsed.suffix, set)
  })
  return map
}

function buildMainStepTokensFromSelection(selectionMap) {
  const tokens = []
  selectionMap.forEach((prefixes, suffix) => {
    if (!prefixes || prefixes.size === 0) return
    const normalizedPrefixes = prefixes.has("*") ? ["*"] : Array.from(prefixes)
    normalizedPrefixes.forEach((prefix) => {
      const token = buildMainStepToken(suffix, prefix)
      if (token) tokens.push(token)
    })
  })
  return tokens
}

function toggleMainStepPrefix(currentPrefixes, prefix) {
  const nextPrefixes = new Set(currentPrefixes)

  if (prefix === "*") {
    if (nextPrefixes.has("*")) {
      nextPrefixes.delete("*")
    } else {
      nextPrefixes.clear()
      nextPrefixes.add("*")
    }
    return normalizePrefixSelection(nextPrefixes)
  }

  if (nextPrefixes.has("*")) {
    nextPrefixes.delete("*")
  }

  if (nextPrefixes.has(prefix)) {
    nextPrefixes.delete(prefix)
  } else {
    nextPrefixes.add(prefix)
  }

  return normalizePrefixSelection(nextPrefixes)
}

function normalizePrefixSelection(prefixes) {
  if (!prefixes || prefixes.size === 0) return new Set(["*"])
  return prefixes
}

function getMainStepDisplayValue(selectionMap) {
  if (selectionMap.size === 0) return "전체"
  if (selectionMap.size === 1) {
    const [suffix, prefixes] = Array.from(selectionMap.entries())[0]
    if (!prefixes || prefixes.size === 0 || prefixes.has("*")) return suffix
    return `${suffix} (${Array.from(prefixes).join(", ")})`
  }
  return `${selectionMap.size}개 선택`
}

function getSelectedValues(isMulti, current) {
  if (isMulti) {
    return Array.isArray(current) ? current : []
  }
  return isNil(current) ? [] : [current]
}
