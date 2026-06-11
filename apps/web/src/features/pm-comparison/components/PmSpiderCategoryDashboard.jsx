import { useEffect, useMemo, useState } from "react"
import { Activity, AlertTriangle, BarChart3, CheckCircle2, RotateCcw, Waves } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

import { usePmSpiderDetailResult } from "../hooks/usePmComparisonQueries"
import { formatNumber } from "../utils/format"
import { OesSpectrumChart } from "./OesSpectrumChart"
import { PmScoreScatterChart } from "./PmScoreScatterChart"
import { TraceTrendChart } from "./TraceTrendChart"

const CATEGORY_ICONS = {
  trace: Activity,
  oes: Waves,
}

const RANK_WIDTH_CLASSES = [
  "w-1/12",
  "w-1/6",
  "w-1/4",
  "w-1/3",
  "w-5/12",
  "w-1/2",
  "w-7/12",
  "w-2/3",
  "w-3/4",
  "w-5/6",
  "w-full",
]

const EMPTY_REF_CYCLES = []

function getRankScore(row) {
  const score = Number(row?.score ?? row?.absDelta ?? 0)
  return Number.isFinite(score) ? score : 0
}

function getRowLabel(category, row) {
  if (category?.kind === "trace") {
    return row?.traceSensor || row?.traceParamName || row?.itemName || "-"
  }
  return `${row?.step || "-"} / ${formatNumber(row?.wavelength, 5)}`
}

function getRowKey(category, row) {
  if (!row) return ""
  if (category?.kind === "trace") {
    return row.traceSensor || row.traceParamName || row.itemName || ""
  }
  return `${row.step || ""}:${row.wavelength || ""}`
}

function getTraceSensor(row) {
  return row?.traceSensor || row?.traceParamName || row?.itemName || ""
}

function getRowDetail(category, row) {
  if (category?.kind === "trace") {
    return `score ${formatNumber(row?.score)} · ${row?.phase || "comp"}`
  }
  return `score ${formatNumber(row?.score)} · λ ${formatNumber(row?.wavelength, 5)}`
}

function getScoreRange(rows) {
  const scores = rows.map(getRankScore)
  if (!scores.length) {
    return { min: 0, max: 0 }
  }
  return {
    min: Math.min(...scores),
    max: Math.max(...scores),
  }
}

function getRankWidthClass(row, range) {
  if (range.max <= range.min) return RANK_WIDTH_CLASSES[RANK_WIDTH_CLASSES.length - 1]
  const ratio = (getRankScore(row) - range.min) / (range.max - range.min)
  const index = Math.max(0, Math.min(RANK_WIDTH_CLASSES.length - 1, Math.ceil(ratio * (RANK_WIDTH_CLASSES.length - 1))))
  return RANK_WIDTH_CLASSES[index]
}

function areSameDates(left, right) {
  const leftValues = [...(left || [])].sort()
  const rightValues = [...(right || [])].sort()
  return leftValues.length === rightValues.length && leftValues.every((value, index) => value === rightValues[index])
}

function getRefCycles(category) {
  return Array.isArray(category?.source?.refCycles) ? category.source.refCycles : EMPTY_REF_CYCLES
}

function getDefaultRefPmDates(refCycles) {
  return refCycles
    .filter((cycle) => cycle?.selected !== false)
    .map((cycle) => cycle.pmDate)
    .filter(Boolean)
}

function RefCycleSelector({
  category,
  selectedRefPmDates,
  onSelectedRefPmDatesChange,
  isFetching,
}) {
  const refCycles = getRefCycles(category)
  const defaultRefPmDates = useMemo(() => getDefaultRefPmDates(refCycles), [refCycles])
  const appliedRefPmDates = useMemo(
    () => (selectedRefPmDates == null ? defaultRefPmDates : selectedRefPmDates),
    [defaultRefPmDates, selectedRefPmDates],
  )
  const [draftRefPmDates, setDraftRefPmDates] = useState(appliedRefPmDates)
  const hasDraftChanges = !areSameDates(draftRefPmDates, appliedRefPmDates)

  useEffect(() => {
    setDraftRefPmDates(appliedRefPmDates)
  }, [appliedRefPmDates, category?.id])

  const toggleRefDate = (pmDate, checked) => {
    setDraftRefPmDates((current) => {
      const values = new Set(current)
      if (checked) {
        values.add(pmDate)
      } else {
        values.delete(pmDate)
      }
      return Array.from(values)
    })
  }

  const resetDefault = () => {
    setDraftRefPmDates(defaultRefPmDates)
    onSelectedRefPmDatesChange(null)
  }

  return (
    <Card className="rounded-lg py-0">
      <CardContent className="grid gap-3 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <CardTitle className="text-sm">Ref PM cycle</CardTitle>
            <Badge variant="outline">comp 0</Badge>
            <Badge variant="secondary">{category?.data?.window?.pmDate || "-"}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            선택된 ref {formatNumber(draftRefPmDates.length, 0)}개 / 전체 {formatNumber(refCycles.length, 0)}개
          </p>
        </div>
        {refCycles.length === 0 ? (
          <div className="flex min-h-10 items-center rounded-md border border-dashed px-3 text-sm text-muted-foreground">
            선택 가능한 ref PM cycle이 없습니다.
          </div>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex min-w-0 flex-wrap gap-2">
              {refCycles.map((cycle) => {
                const id = `ref-cycle-${category?.id}-${cycle.pmDate}`
                const checked = draftRefPmDates.includes(cycle.pmDate)
                return (
                  <Label
                    key={`${cycle.pmDate}-${cycle.cycleIndex}`}
                    htmlFor={id}
                    className={cn(
                      "flex min-h-8 cursor-pointer items-center gap-2 rounded-md border bg-background px-2.5 py-1 text-xs transition-colors hover:bg-muted/60",
                      checked && "border-primary bg-accent/50",
                    )}
                  >
                    <Checkbox
                      id={id}
                      checked={checked}
                      onCheckedChange={(value) => toggleRefDate(cycle.pmDate, Boolean(value))}
                    />
                    <span className="font-medium tabular-nums">cycle {cycle.cycleIndex}</span>
                    <span className="text-muted-foreground">{cycle.pmDate}</span>
                    {checked ? (
                      <CheckCircle2 className="size-3.5 text-primary" aria-hidden="true" />
                    ) : null}
                  </Label>
                )
              })}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={resetDefault}
                disabled={isFetching}
              >
                <RotateCcw className="size-4" />
                기본값
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => onSelectedRefPmDatesChange(draftRefPmDates)}
                disabled={isFetching || !hasDraftChanges}
              >
                적용
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function RankRows({ category, selectedRankKey, onSelectRank }) {
  const rows = category?.rows || []
  const scoreRange = getScoreRange(rows)

  if (!rows.length) {
    return (
      <div className="flex h-full min-h-64 items-center justify-center p-4 text-center text-sm text-muted-foreground">
        선택한 tab의 rank 데이터가 없습니다.
      </div>
    )
  }

  return (
    <div className="divide-y">
      {rows.map((row, index) => (
        <button
          key={`${category.id}-rank-${getRowKey(category, row)}-${index}`}
          type="button"
          aria-pressed={selectedRankKey === getRowKey(category, row)}
          onClick={() => onSelectRank(getRowKey(category, row))}
          className={cn(
            "grid w-full gap-2 px-3 py-2.5 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            selectedRankKey === getRowKey(category, row) && "border-l-2 border-l-primary bg-accent/40",
          )}
        >
          <div className="flex min-w-0 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-medium tabular-nums">
                {index + 1}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{getRowLabel(category, row)}</p>
                <p className="truncate text-xs text-muted-foreground">{getRowDetail(category, row)}</p>
              </div>
            </div>
            <span className="font-mono text-sm tabular-nums">{formatNumber(row?.score)}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div className={cn("h-full rounded-full bg-primary", getRankWidthClass(row, scoreRange))} />
          </div>
        </button>
      ))}
    </div>
  )
}

function CategorySummaryContent({ category }) {
  const worstRow = category?.rows?.[0]
  const Icon = CATEGORY_ICONS[category?.kind] || BarChart3

  return (
    <div className="grid gap-2 px-3 py-3">
      <div className="flex min-w-0 items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-2">
          <span className="rounded-md border bg-background p-1.5 text-muted-foreground">
            <Icon className="size-3.5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold">{category?.label || "Category"}</h2>
            <p className="truncate text-xs text-muted-foreground">
              {category?.description || "-"} · {category?.sourceLabel || "-"}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-1.5">
          <Badge variant="outline">{category?.patternLabel || "-"}</Badge>
          <Badge variant="secondary">{formatNumber(category?.fileCount || 0, 0)} files</Badge>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-md border bg-background px-2.5 py-2">
          <p className="text-xs text-muted-foreground">Worst item</p>
          <p className="mt-0.5 truncate text-sm font-medium">{worstRow ? getRowLabel(category, worstRow) : "-"}</p>
        </div>
        <div className="rounded-md border bg-background px-2.5 py-2">
          <p className="text-xs text-muted-foreground">Worst score</p>
          <p className="mt-0.5 font-mono text-sm tabular-nums">{formatNumber(worstRow?.score)}</p>
        </div>
        <div className="rounded-md border bg-background px-2.5 py-2">
          <p className="text-xs text-muted-foreground">Rank rows</p>
          <p className="mt-0.5 font-mono text-sm tabular-nums">{formatNumber(category?.rows?.length || 0, 0)}</p>
        </div>
      </div>
    </div>
  )
}

function CategoryTabsPanel({
  categories,
  selectedCategory,
  selectedRankKey,
  onSelectCategory,
  onSelectRank,
}) {
  const activeCategory = selectedCategory || categories[0]

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-card">
      {/* Horizontal tabs - Confluence style */}
      <nav className="flex shrink-0 border-b bg-muted/20">
        {categories.map((category) => {
          const isActive = activeCategory?.id === category.id
          return (
            <button
              key={category.id}
              type="button"
              onClick={() => onSelectCategory(category.id)}
              className={cn(
                "relative flex-1 border-r px-2 py-2.5 text-center text-xs transition-colors last:border-r-0 hover:bg-muted/50",
                isActive
                  ? "bg-background font-semibold text-foreground after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary"
                  : "text-muted-foreground",
              )}
            >
              <span className="block font-medium">{category.patternLabel}</span>
              <span className="block text-[10px]">{category.kind.toUpperCase()}</span>
            </button>
          )
        })}
      </nav>

      {/* Card content */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        {/* Summary section */}
        <section className="shrink-0 border-b">
          <div className="border-b bg-muted/30 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Summary
          </div>
          <CategorySummaryContent category={activeCategory} />
        </section>

        {/* Rank section */}
        <section className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="shrink-0 border-b bg-muted/30 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Rank · 낮은 score 우선
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">
            <RankRows
              category={activeCategory}
              selectedRankKey={selectedRankKey}
              onSelectRank={onSelectRank}
            />
          </div>
        </section>
      </div>
    </div>
  )
}

function SelectedVisualization({ category, selectedRow, detailQuery }) {
  if (category?.kind === "trace") {
    const selectedSensor = getTraceSensor(selectedRow)
    const fallbackRows = Array.isArray(category.source?.trendRows)
      ? category.source.trendRows.filter((row) => row.traceParamName === selectedSensor)
      : []
    const trendRows = detailQuery.data?.trace?.trendRows || fallbackRows

    return (
      <TraceTrendChart
        title={`${category.label} · ${selectedSensor || "Trace"} step_time overlay`}
        rows={trendRows}
        isLoading={detailQuery.isFetching && !detailQuery.data}
      />
    )
  }

  const detailRows = detailQuery.data?.oes?.detailRows || category?.source?.detailRows || []
  return (
    <OesSpectrumChart
      title={`${category?.label || "OES"} · ${selectedRow?.step || "OES"} ref/comp spectrum`}
      rows={detailRows}
      isLoading={detailQuery.isFetching && !detailQuery.data}
    />
  )
}

export function PmSpiderCategoryDashboard({
  categories,
  selectedCategoryId,
  onSelectedCategoryChange,
  selectedRefPmDates,
  onSelectedRefPmDatesChange,
  isFetching,
}) {
  const [selectedRankKeys, setSelectedRankKeys] = useState({})
  const selectedCategory = categories.find((category) => category.id === selectedCategoryId) || categories[0]
  const firstRankKey = getRowKey(selectedCategory, selectedCategory?.rows?.[0])
  const selectedRankKey = selectedRankKeys[selectedCategory?.id] || firstRankKey
  const selectedRow =
    selectedCategory?.rows?.find((row) => getRowKey(selectedCategory, row) === selectedRankKey)
    || selectedCategory?.rows?.[0]
  const detailQuery = usePmSpiderDetailResult(selectedCategory, selectedRow, selectedRefPmDates)
  const warnings = Array.from(new Set(categories.flatMap((category) => category.warnings))).slice(0, 3)

  const selectCategory = (categoryId) => {
    onSelectedCategoryChange(categoryId)
  }
  const selectRank = (rankKey) => {
    setSelectedRankKeys((current) => ({
      ...current,
      [selectedCategory.id]: rankKey,
    }))
  }

  if (!selectedCategory) {
    return (
      <div className="flex min-h-96 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
        PM SPIDER category 데이터가 없습니다.
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <RefCycleSelector
        category={selectedCategory}
        selectedRefPmDates={selectedRefPmDates}
        onSelectedRefPmDatesChange={onSelectedRefPmDatesChange}
        isFetching={isFetching}
      />

      {warnings.length > 0 ? (
        <div className="flex shrink-0 items-center gap-2 rounded-lg border bg-card px-4 py-3 text-xs text-muted-foreground">
          <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
          <span className="truncate">{warnings.join(" / ")}</span>
        </div>
      ) : null}

      <section className="grid min-h-[55vh] min-w-0 grid-cols-[minmax(0,1.4fr)_minmax(340px,1fr)] gap-3">
        <PmScoreScatterChart
          title={`${selectedCategory.label} PM cycle score trend`}
          rows={selectedCategory.source?.scoreTrendRows}
          selectedLabel={getRowLabel(selectedCategory, selectedRow)}
        />
        <CategoryTabsPanel
          categories={categories}
          selectedCategory={selectedCategory}
          selectedRankKey={selectedRankKey}
          onSelectCategory={selectCategory}
          onSelectRank={selectRank}
        />
      </section>

      <section className="min-h-[360px] min-w-0">
        <SelectedVisualization
          category={selectedCategory}
          selectedRow={selectedRow}
          detailQuery={detailQuery}
        />
      </section>

      {isFetching ? (
        <div className="pointer-events-none fixed bottom-4 right-4 rounded-md border bg-card px-3 py-2 text-xs text-muted-foreground shadow-sm">
          PM SPIDER category 데이터를 갱신하는 중입니다.
        </div>
      ) : null}
    </div>
  )
}
