// src/features/line-dashboard/components/LineHistoryDashboard.jsx
import * as React from "react"
import { IconAlertCircle } from "@tabler/icons-react"

import { LineHistoryFilterBar } from "./chart/LineHistoryFilterBar"
import { ColorLegend, LegendLabel } from "./chart/LineHistoryLegend"
import { LineHistoryMetricChart } from "./chart/LineHistoryMetricChart"
import { timeFormatter } from "../utils/formatters"
import {
  BIN_LABELS,
  BIN_OPTIONS,
  DEFAULT_BIN,
  DIMENSION_LABELS,
  DIMENSION_OPTIONS,
  HISTORY_LABELS,
  totalsChartConfig,
} from "../utils/lineHistoryConfig"
import {
  aggregateBreakdownsByBin,
  aggregateTotalsByBin,
  buildBreakdownSeries,
  buildTotals,
  getDefaultDateRange,
  resolveDimensionRecords,
} from "../utils/lineHistoryTransforms"
import { useLineHistoryData } from "../hooks/useLineHistoryData"

export function LineHistoryDashboard({ lineId, initialRangeDays = 30 }) {
  const defaultRange = React.useMemo(
    () => getDefaultDateRange(initialRangeDays),
    [initialRangeDays],
  )

  const today = React.useMemo(() => {
    const now = new Date()
    now.setHours(23, 59, 59, 999)
    return now
  }, [])

  // 날짜 범위 (일반적인 range UX)
  const [dateRange, setDateRange] = React.useState(defaultRange)

  // X축 집계 단위
  const [binMode, setBinMode] = React.useState(DEFAULT_BIN)

  // 날짜 선택 팝오버 열림 상태
  const [isCalendarOpen, setIsCalendarOpen] = React.useState(false)

  // 분류 기준(레전드 기준): 처음엔 null, 데이터 들어오면 첫 사용가능 차원으로 자동 설정
  const [activeDimension, setActiveDimension] = React.useState(null)

  // 차원별 카테고리 선택 상태 (차트에는 activeDimension만 적용)
  const [selectedCategoriesByDimension, setSelectedCategoriesByDimension] =
    React.useState(() =>
      DIMENSION_OPTIONS.reduce(
        (acc, option) => ({ ...acc, [option.value]: [] }),
        {},
      ),
    )

  const [legendColorOverrides, setLegendColorOverrides] = React.useState(() =>
    DIMENSION_OPTIONS.reduce(
      (acc, option) => ({ ...acc, [option.value]: {} }),
      {},
    ),
  )

  const calendarButtonRef = React.useRef(null)
  const calendarPopoverRef = React.useRef(null)

  const {
    data,
    isLoading,
    error,
    totalsData: rawTotalsData,
    breakdownRecordsByDimension: rawBreakdownRecordsByDimension,
    hasSendJiraData,
    refresh,
  } = useLineHistoryData({ lineId, dateRange })

  const totalsData = React.useMemo(
    () => aggregateTotalsByBin(rawTotalsData, binMode),
    [rawTotalsData, binMode],
  )

  const breakdownRecordsByDimension = React.useMemo(
    () => aggregateBreakdownsByBin(rawBreakdownRecordsByDimension, binMode),
    [rawBreakdownRecordsByDimension, binMode],
  )

  React.useEffect(() => {
    if (!isCalendarOpen) return
    const handleClick = (event) => {
      const target = event.target
      if (
        calendarPopoverRef.current?.contains(target) ||
        calendarButtonRef.current?.contains(target)
      ) {
        return
      }
      setIsCalendarOpen(false)
    }
    const handleKey = (event) => {
      if (event.key === "Escape") setIsCalendarOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    document.addEventListener("keydown", handleKey)
    return () => {
      document.removeEventListener("mousedown", handleClick)
      document.removeEventListener("keydown", handleKey)
    }
  }, [isCalendarOpen])

  // 차원별 레코드/토탈 계산
  const dimensionRecords = React.useMemo(() => {
    const resolved = {}
    for (const option of DIMENSION_OPTIONS) {
      resolved[option.value] = resolveDimensionRecords(
        breakdownRecordsByDimension,
        option.value,
      )
    }
    return resolved
  }, [breakdownRecordsByDimension])

  const dimensionTotals = React.useMemo(() => {
    const totals = {}
    for (const option of DIMENSION_OPTIONS) {
      const records = dimensionRecords?.[option.value]?.records
      totals[option.value] = Array.isArray(records) ? buildTotals(records) : []
    }
    return totals
  }, [dimensionRecords])

  // 선택된 카테고리 중, 실제 존재하지 않는 카테고리는 정리
  React.useEffect(() => {
    setSelectedCategoriesByDimension((prev) => {
      let changed = false
      const next = { ...prev }

      for (const option of DIMENSION_OPTIONS) {
        const current = prev[option.value] ?? []
        const available = new Set(
          (dimensionTotals[option.value] ?? []).map(([category]) => category),
        )
        const filtered = current.filter((category) => available.has(category))
        const isSameLength = filtered.length === current.length
        const isSameOrder = isSameLength && filtered.every((value, index) => value === current[index])

        next[option.value] = filtered
        if (!isSameOrder) changed = true
      }

      return changed ? next : prev
    })
  }, [dimensionTotals])

  // activeDimension이 없거나 데이터 없는 차원을 가리키면,
  // 데이터가 있는 첫 차원으로 자동 설정
  React.useEffect(() => {
    const hasActive =
      activeDimension &&
      Array.isArray(dimensionRecords?.[activeDimension]?.records) &&
      dimensionRecords[activeDimension].records.length > 0

    if (hasActive) return

    for (const option of DIMENSION_OPTIONS) {
      const records = dimensionRecords?.[option.value]?.records
      if (Array.isArray(records) && records.length > 0) {
        if (option.value !== activeDimension) {
          setActiveDimension(option.value)
        }
        return
      }
    }

    // 어떤 차원에도 데이터가 없으면 null 유지
    if (activeDimension !== null) {
      setActiveDimension(null)
    }
  }, [activeDimension, dimensionRecords])

  const activeDimensionLabel = activeDimension
    ? DIMENSION_LABELS[activeDimension] ?? activeDimension
    : "선택 안됨"

  const activeDimensionTotals = React.useMemo(
    () => (activeDimension ? dimensionTotals[activeDimension] ?? [] : []),
    [activeDimension, dimensionTotals],
  )

  const activeCategories = React.useMemo(
    () =>
      activeDimension ? selectedCategoriesByDimension[activeDimension] ?? [] : [],
    [activeDimension, selectedCategoriesByDimension],
  )

  const activeDimensionRecords = React.useMemo(
    () =>
      activeDimension
        ? dimensionRecords?.[activeDimension]?.records ?? []
        : [],
    [activeDimension, dimensionRecords],
  )

  const hasFilterSelection = React.useMemo(
    () => Array.isArray(activeCategories) && activeCategories.length > 0,
    [activeCategories],
  )

  const activeLegendOverrides = React.useMemo(
    () => (activeDimension ? legendColorOverrides[activeDimension] ?? {} : {}),
    [activeDimension, legendColorOverrides],
  )

  // 진행 건수 브레이크다운 시리즈
  const rowBreakdownSeries = React.useMemo(() => {
    if (
      !activeDimension ||
      !Array.isArray(activeDimensionRecords) ||
      activeDimensionRecords.length === 0 ||
      !Array.isArray(activeCategories) ||
      activeCategories.length === 0
    ) {
      return { data: [], seriesKeys: [], config: {} }
    }

    const resolvedKey = dimensionRecords?.[activeDimension]?.key ?? activeDimension
    const label = DIMENSION_LABELS[activeDimension] ?? activeDimension

    return buildBreakdownSeries(
      activeDimensionRecords,
      ["rowCount"],
      10,
      activeCategories,
      resolvedKey,
      label,
      activeLegendOverrides,
    )
  }, [
    activeDimension,
    activeDimensionRecords,
    activeCategories,
    dimensionRecords,
    activeLegendOverrides,
  ])

  // Send Jira 브레이크다운 시리즈
  const jiraBreakdownSeries = React.useMemo(() => {
    if (
      !hasSendJiraData ||
      !activeDimension ||
      !Array.isArray(activeDimensionRecords) ||
      activeDimensionRecords.length === 0 ||
      !Array.isArray(activeCategories) ||
      activeCategories.length === 0
    ) {
      return { data: [], seriesKeys: [], config: {} }
    }

    const resolvedKey = dimensionRecords?.[activeDimension]?.key ?? activeDimension
    const label = DIMENSION_LABELS[activeDimension] ?? activeDimension

    return buildBreakdownSeries(
      activeDimensionRecords,
      ["sendJiraCount"],
      10,
      activeCategories,
      resolvedKey,
      label,
      activeLegendOverrides,
    )
  }, [
    hasSendJiraData,
    activeDimension,
    activeDimensionRecords,
    activeCategories,
    dimensionRecords,
    activeLegendOverrides,
  ])

  const handleRefresh = React.useCallback(() => {
    if (!lineId) return
    refresh()
  }, [lineId, refresh])

  const handleDateRangeSelect = React.useCallback((range) => {
    setDateRange(range)
  }, [])

  const handleCalendarToggle = React.useCallback(() => {
    setIsCalendarOpen((prev) => !prev)
  }, [])

  const handleCalendarClose = React.useCallback(() => {
    setIsCalendarOpen(false)
  }, [])

  const handleBinChange = React.useCallback((value) => {
    const isValid = BIN_OPTIONS.some((option) => option.value === value)
    setBinMode(isValid ? value : DEFAULT_BIN)
  }, [])

  // 카테고리 선택 토글
  const handleCategoryToggle = React.useCallback(
    (dimension, category, checked) => {
      setSelectedCategoriesByDimension((prev) => {
        const current = prev[dimension] ?? []
        const next =
          checked === true
            ? Array.from(new Set([...current, category]))
            : current.filter((item) => item !== category)
        return { ...prev, [dimension]: next }
      })
    },
    [],
  )

  const handleClearActiveCategories = React.useCallback(() => {
    if (!activeDimension) return
    setSelectedCategoriesByDimension((prev) => ({
      ...prev,
      [activeDimension]: [],
    }))
  }, [activeDimension])

  // 레전드 색상 변경
  const handleLegendColorChange = React.useCallback(
    (dimension, category, color) => {
      if (!dimension || !category || !color) return
      setLegendColorOverrides((prev) => ({
        ...prev,
        [dimension]: {
          ...(prev[dimension] ?? {}),
          [category]: color,
        },
      }))
    },
    [],
  )

  const handleLegendColorReset = React.useCallback((dimension, category) => {
    setLegendColorOverrides((prev) => {
      const prevDimension = prev[dimension] ?? {}
      if (!prevDimension[category]) return prev
      const nextDimension = { ...prevDimension }
      delete nextDimension[category]
      return { ...prev, [dimension]: nextDimension }
    })
  }, [])

  const combinedLegendEntries = React.useMemo(() => {
    if (!hasFilterSelection) return []
    const entriesByCategory = new Map()

    const collectEntries = (series) => {
      if (!series || !Array.isArray(series.seriesKeys)) return
      for (const key of series.seriesKeys) {
        const configEntry = series.config?.[key]
        if (!configEntry?.category) continue
        if (entriesByCategory.has(configEntry.category)) continue
        entriesByCategory.set(configEntry.category, {
          key,
          label: configEntry.label ?? configEntry.category,
          category: configEntry.category,
          color: configEntry.color,
        })
      }
    }

    collectEntries(rowBreakdownSeries)
    collectEntries(jiraBreakdownSeries)

    return Array.from(entriesByCategory.values())
  }, [hasFilterSelection, rowBreakdownSeries, jiraBreakdownSeries])

  const renderLegendLabel = React.useCallback(
    (key, configEntry) => {
      if (!configEntry) return null
      const label = configEntry.label ?? key
      const category = configEntry.category
      const color = configEntry.color ?? "var(--chart-1)"
      const overrideColor = category ? activeLegendOverrides?.[category] : null

      return (
        <LegendLabel
          label={label}
          color={color}
          category={category}
          disabled={!activeDimension || !category}
          hasOverride={Boolean(overrideColor)}
          onResetColor={() =>
            handleLegendColorReset(activeDimension, category)
          }
          onSelectColor={(selected) =>
            handleLegendColorChange(activeDimension, category, selected)
          }
        />
      )
    },
    [
      activeDimension,
      activeLegendOverrides,
      handleLegendColorChange,
      handleLegendColorReset,
    ],
  )

  const lastUpdatedLabel = React.useMemo(() => {
    if (isLoading) return "Updating…"
    const generatedAt = data?.generatedAt
    if (!generatedAt) return "-"
    const parsed = new Date(generatedAt)
    if (Number.isNaN(parsed.getTime())) return "-"
    return timeFormatter.format(parsed)
  }, [data?.generatedAt, isLoading])

  const hasTotalsRowData = Array.isArray(totalsData) && totalsData.length > 0
  const hasTotalsJiraData =
    hasSendJiraData && Array.isArray(totalsData) && totalsData.length > 0

  // 전체 필터가 하나라도 변경되었는지 여부 (버튼 활성화용)
  const hasAnyActiveFilter = React.useMemo(() => {
    const toDateKey = (date) =>
      date instanceof Date ? date.toISOString().slice(0, 10) : null

    const currentFromKey = toDateKey(dateRange?.from)
    const currentToKey = toDateKey(dateRange?.to)
    const defaultFromKey = toDateKey(defaultRange?.from)
    const defaultToKey = toDateKey(defaultRange?.to)

    const hasDateFilter =
      !currentFromKey ||
      !currentToKey ||
      currentFromKey !== defaultFromKey ||
      currentToKey !== defaultToKey

    const hasCategoryFilter = Object.values(selectedCategoriesByDimension).some(
      (categories) => Array.isArray(categories) && categories.length > 0,
    )

    const hasBinSelection = binMode !== DEFAULT_BIN

    return hasDateFilter || hasCategoryFilter || hasBinSelection
  }, [binMode, dateRange, defaultRange, selectedCategoriesByDimension])

  // 필터 전체 초기화
  const handleResetAllFilters = React.useCallback(() => {
    // 날짜 범위 기본값
    setDateRange(defaultRange)

    // 집계 단위 기본값
    setBinMode(DEFAULT_BIN)

    // 달력 닫기
    setIsCalendarOpen(false)

    // 카테고리 필터 초기화
    setSelectedCategoriesByDimension(
      DIMENSION_OPTIONS.reduce(
        (acc, option) => ({ ...acc, [option.value]: [] }),
        {},
      ),
    )
  }, [defaultRange])

  return (
    <div className="relative flex h-full min-h-0 min-w-0 flex-col gap-4 overflow-hidden">
      {/* 제목 + 업데이트 시간 */}
      <div className="flex flex-col gap-1">
        <div className="flex items-baseline gap-2 text-lg font-semibold">
          <h1 className="text-lg font-semibold">
            {lineId ? `${lineId} ${HISTORY_LABELS.titleSuffix}` : HISTORY_LABELS.titleSuffix}
          </h1>
          <span
            className="text-[11px] font-normal text-muted-foreground"
            aria-live="polite"
          >
            {HISTORY_LABELS.updated} {lastUpdatedLabel}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          라인별 E-SOP 진행 추이를 날짜/시간 단위로 확인하고, 선택한 분류 기준에 따라
          카테고리별로 비교합니다.
        </p>
      </div>

      <LineHistoryFilterBar
        dateRange={dateRange}
        today={today}
        defaultRange={defaultRange}
        isCalendarOpen={isCalendarOpen}
        calendarButtonRef={calendarButtonRef}
        calendarPopoverRef={calendarPopoverRef}
        onCalendarToggle={handleCalendarToggle}
        onCalendarClose={handleCalendarClose}
        onDateRangeSelect={handleDateRangeSelect}
        binMode={binMode}
        onBinChange={handleBinChange}
        activeDimension={activeDimension}
        activeDimensionLabel={activeDimensionLabel}
        dimensionRecords={dimensionRecords}
        onDimensionChange={setActiveDimension}
        activeDimensionTotals={activeDimensionTotals}
        activeCategories={activeCategories}
        hasFilterSelection={hasFilterSelection}
        onCategoryToggle={handleCategoryToggle}
        onClearActiveCategories={handleClearActiveCategories}
        hasAnyActiveFilter={hasAnyActiveFilter}
        isLoading={isLoading}
        onResetAllFilters={handleResetAllFilters}
        onRefresh={handleRefresh}
      />

      {/* 에러 메시지 */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <div className="flex items-center gap-2">
            <IconAlertCircle className="size-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* 메인 차트 섹션 */}
      <section className="flex flex-1 min-h-0 min-w-0 flex-col gap-6 overflow-y-auto rounded-lg border bg-background p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">E-SOP Trend</h2>
            <p className="text-xs text-muted-foreground">
              날짜/시간별 E-SOP진행 건수 Jira인폼 건수 Trend Monitoring
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2 text-[11px] text-muted-foreground">
            <span className="rounded-md bg-muted px-2 py-1">
              X축 Bin: {BIN_LABELS[binMode] ?? binMode}
            </span>
            {activeDimension && (
              <span className="rounded-md bg-muted px-2 py-1">
                분류 기준: {activeDimensionLabel}
              </span>
            )}
            {hasFilterSelection && (
              <span className="rounded-md bg-muted px-2 py-1">
                카테고리 필터 {activeCategories.length}개 적용
              </span>
            )}
          </div>
        </div>

        {combinedLegendEntries.length > 0 && (
          <div className="flex justify-end">
            <ColorLegend
              payload={combinedLegendEntries.map((entry) => ({
                dataKey: entry.key,
                value: entry.label,
                color: entry.color,
              }))}
              seriesConfig={Object.fromEntries(
                combinedLegendEntries.map((entry) => [
                  entry.key,
                  {
                    label: entry.label,
                    category: entry.category,
                    color: entry.color,
                  },
                ]),
              )}
              renderItem={(key, configEntry) => renderLegendLabel(key, configEntry)}
            />
          </div>
        )}

        <div className="grid flex-1 min-h-0 min-w-0 grid-cols-1 gap-6 lg:grid-cols-2 lg:auto-rows-fr">
          {/* 진행 건수 차트 */}
          <div className="flex h-full min-h-0 min-w-0 flex-col gap-2">
            <div className="flex items-center justify-between">
              <h3 className="text-md font-semibold uppercase tracking-wide text-muted-foreground">
                진행 건수
              </h3>
            </div>
            <LineHistoryMetricChart
              totalUnavailableText="진행 건수 데이터가 없습니다."
              breakdownSeries={rowBreakdownSeries}
              totalsData={totalsData}
              totalsConfigEntry={totalsChartConfig.rowCount}
              totalsDataKey="rowCount"
              hasTotalsData={hasTotalsRowData}
              hasFilterSelection={hasFilterSelection}
              binMode={binMode}
              tickMargin={12}
              fallbackColor="var(--chart-1)"
            />
          </div>

          {/* Send Jira 차트 */}
          <div className="flex h-full min-h-0 min-w-0 flex-col gap-2">
            <div className="flex items-center justify-between">
              <h3 className="text-md font-semibold uppercase tracking-wide text-muted-foreground">
                Jira 인폼 건수
              </h3>
            </div>
            <LineHistoryMetricChart
              hasMetricData={hasSendJiraData}
              metricUnavailableText="Send Jira 데이터가 없습니다."
              totalUnavailableText="Jira 인폼 데이터가 없습니다."
              breakdownSeries={jiraBreakdownSeries}
              totalsData={totalsData}
              totalsConfigEntry={totalsChartConfig.sendJiraCount}
              totalsDataKey="sendJiraCount"
              hasTotalsData={hasTotalsJiraData}
              hasFilterSelection={hasFilterSelection}
              binMode={binMode}
              tickMargin={16}
              fallbackColor="var(--chart-2)"
            />
          </div>
        </div>
      </section>

      {/* 로딩 인디케이터 */}
      {isLoading && (
        <div className="pointer-events-none absolute inset-x-0 top-24 flex justify-center">
          <div className="rounded-full border border-muted bg-background/90 px-3 py-1 text-xs text-muted-foreground shadow-sm">
            데이터를 불러오는 중...
          </div>
        </div>
      )}
    </div>
  )
}
