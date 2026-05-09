import * as React from "react"
import { IconCheck, IconChevronDown } from "@tabler/icons-react"

import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { QuickFilterFieldset } from "./QuickFilterFieldset"
import {
  buildMainStepToken,
  parseMainStepToken,
} from "../../utils/dataTableQuickFilters"

const EMPTY_OPTIONS = []

export function MainStepDropdownSection({ section, legendId, current, onToggle }) {
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
              hasSelection && "border-primary bg-primary/10 text-primary",
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
                        isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted",
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
                    activeSuffix ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
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
                      "data-[state=checked]:bg-primary/10 data-[state=checked]:text-primary",
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
                          "data-[state=checked]:bg-primary/10 data-[state=checked]:text-primary",
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
