import { useEffect, useMemo, useRef, useState } from "react"
import { Activity, Search, Waves } from "lucide-react"
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

import { usePmSpiderDetailResult } from "../hooks/usePmComparisonQueries"
import { formatNumber } from "../utils/format"
import { buildJitterKde, buildRawSeries, buildShapeData, C as TC, StepSelector } from "./TraceSignalPanel"

// ──────────────────────────────────────────────────────────────
// 타입 탭 정의: NPW / PW
// ──────────────────────────────────────────────────────────────
const TYPE_TABS = [
  { id: "ag",      label: "NPW" },
  { id: "process", label: "PW"  },
]

// ──────────────────────────────────────────────────────────────
// 랭킹 빌드 헬퍼
// ──────────────────────────────────────────────────────────────
function buildRankRows(category, panelType) {
  const rows = (category?.rows ?? []).filter(Boolean)
  if (category?.kind === "trace") {
    const sorted = [...rows].sort((a, b) =>
      panelType === "p2"
        ? Number(b.alarmPct ?? 0) - Number(a.alarmPct ?? 0)
        : Number(b.deltaShape ?? 0) - Number(a.deltaShape ?? 0)
    )
    return sorted.filter((r) => r.itemName || r.traceSensor)
  }
  const byStep = new Map()
  for (const row of rows) {
    const stepKey = row.step || row.itemName || ""
    if (!stepKey) continue
    const prev = byStep.get(stepKey)
    const metric = panelType === "p2" ? Number(row.flaggedWl ?? 0) : Number(row.deltaSpectrum ?? 0)
    const prevMetric = prev ? (panelType === "p2" ? Number(prev.flaggedWl ?? 0) : Number(prev.deltaSpectrum ?? 0)) : -1
    if (!prev || metric > prevMetric) byStep.set(stepKey, row)
  }
  return Array.from(byStep.values()).sort((a, b) =>
    panelType === "p2"
      ? Number(b.flaggedWl ?? 0) - Number(a.flaggedWl ?? 0)
      : Number(b.deltaSpectrum ?? 0) - Number(a.deltaSpectrum ?? 0)
  )
}

function getRowKey(category, row) {
  if (!row) return ""
  if (category?.kind === "trace") {
    const param = row.itemName || row.traceSensor || ""
    const step  = row.step || ""
    return step ? `${param}::${step}` : param
  }
  return row.step || row.itemName || ""
}

function parseTraceKey(key) {
  if (!key) return { paramName: "", step: "" }
  const idx = key.indexOf("::")
  if (idx === -1) return { paramName: key, step: "" }
  return { paramName: key.slice(0, idx), step: key.slice(idx + 2) }
}

function getRowLabel(category, row) {
  if (!row) return "-"
  if (category?.kind === "trace") return row.itemName || row.traceSensor || "-"
  return row.step || row.itemName || "-"
}

function getRowSubLabel(category, row) {
  if (category?.kind !== "trace") return null
  return row?.step ? `step ${row.step}` : null
}

function getMetricValue(category, row, panelType) {
  if (!row) return 0
  if (category?.kind === "trace") {
    return panelType === "p2" ? Number(row.alarmPct ?? 0) : Number(row.deltaShape ?? 0)
  }
  return panelType === "p2" ? Number(row.flaggedWl ?? 0) : Number(row.deltaSpectrum ?? 0)
}

function getMetricLabel(category, row, panelType) {
  if (!row) return "-"
  if (category?.kind === "trace") {
    return panelType === "p2"
      ? `${formatNumber(row.alarmPct ?? 0, 1)}%`
      : `Δ ${formatNumber(row.deltaShape ?? 0, 3)}`
  }
  return panelType === "p2"
    ? `${formatNumber(row.flaggedWl ?? 0, 0)} wl`
    : `Δ ${formatNumber(row.deltaSpectrum ?? 0, 3)}`
}

function filterRows(rows, category, query) {
  if (!query.trim()) return rows
  const q = query.toLowerCase()
  return rows.filter((row) => getRowLabel(category, row).toLowerCase().includes(q))
}

const BAR_WIDTHS = ["w-1/12","w-1/6","w-1/4","w-1/3","w-5/12","w-1/2","w-7/12","w-2/3","w-3/4","w-5/6","w-full"]
function getBarWidth(val, maxVal) {
  if (maxVal <= 0) return BAR_WIDTHS[BAR_WIDTHS.length - 1]
  const ratio = Math.min(1, val / maxVal)
  const idx = Math.max(0, Math.min(BAR_WIDTHS.length - 1, Math.ceil(ratio * (BAR_WIDTHS.length - 1))))
  return BAR_WIDTHS[idx]
}

// ──────────────────────────────────────────────────────────────
// RankPanel
// ──────────────────────────────────────────────────────────────
function RankPanel({ panelType, category, selectedKeys, onSelectRow, onClearAll, onPanelTypeChange, search, onSearchChange }) {
  const isP2 = panelType === "p2"
  const rows = useMemo(() => buildRankRows(category, panelType), [category, panelType])
  const filtered = useMemo(() => filterRows(rows, category, search), [rows, category, search])
  const metricVals = filtered.map((r) => getMetricValue(category, r, panelType))
  const maxMetric = Math.max(0.001, ...metricVals)

  const headerLabel = isP2
    ? category?.kind === "trace" ? "P2 · Per Wafer (ALARM 비율)" : "P2 · Per Wafer (이상 파장 수)"
    : category?.kind === "trace" ? "P3 · 집단비교 (ΔShape)" : "P3 · 집단비교 (ΔSpectrum)"

  const searchPlaceholder = category?.kind === "trace" ? "파라미터 검색..." : "Step 검색..."

  return (
    <Card className="flex flex-col overflow-hidden rounded-lg py-0">
      <div className={cn(
        "shrink-0 border-b px-3 py-2",
        isP2 ? "bg-blue-50/60 dark:bg-blue-950/20" : "bg-orange-50/60 dark:bg-orange-950/20"
      )}>
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold">{headerLabel}</p>
          {onPanelTypeChange && (
            <div className="flex overflow-hidden rounded border">
              {["p2", "p3"].map((mode) => (
                <button key={mode} type="button" onClick={() => onPanelTypeChange(mode)}
                  className={cn(
                    "px-2 py-0.5 text-[10px] transition-colors",
                    panelType === mode
                      ? "bg-primary text-primary-foreground"
                      : "bg-background text-muted-foreground hover:bg-muted",
                  )}>
                  {mode.toUpperCase()}
                </button>
              ))}
            </div>
          )}
        </div>
        <p className="text-[10px] text-muted-foreground">
          {isP2 ? "개별 wafer vs REF 분포" : "COMP 집단 median vs REF tube"}
        </p>
      </div>
      <div className="shrink-0 border-b px-3 py-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-7 pl-7 text-xs"
          />
        </div>
      </div>
      <div className="flex items-center shrink-0 border-b bg-muted/20 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        <span>Rank · {isP2 ? "이상 비율 높은 순" : "변화량 큰 순"}</span>
        {filtered.length !== rows.length && (
          <span className="ml-1 text-primary">{filtered.length}/{rows.length}</span>
        )}
        {onClearAll && selectedKeys.length > 0 && (
          <button type="button" onClick={onClearAll}
            className="ml-auto rounded px-1.5 py-0.5 normal-case tracking-normal text-muted-foreground hover:bg-muted hover:text-foreground">
            전체 해제
          </button>
        )}
      </div>
      <div className="max-h-[320px] overflow-y-auto">
        {category?.isLoading ? (
          <div className="flex min-h-32 items-center justify-center text-sm text-muted-foreground">데이터 조회 중...</div>
        ) : !filtered.length ? (
          <div className="flex min-h-32 items-center justify-center text-sm text-muted-foreground">
            {rows.length ? "검색 결과 없음" : "데이터가 없습니다."}
          </div>
        ) : (
          <div className="divide-y">
            {filtered.map((row, idx) => {
              const key      = getRowKey(category, row)
              const subLabel = getRowSubLabel(category, row)
              const isSelected = selectedKeys.includes(key)
              const metric = getMetricValue(category, row, panelType)
              const barColor = isP2 ? "bg-blue-500" : "bg-orange-500"
              return (
                <button
                  key={`${key}-${idx}`}
                  type="button"
                  onClick={() => onSelectRow(key)}
                  className={cn(
                    "grid w-full gap-1 px-3 py-2 text-left transition-colors hover:bg-muted/50",
                    isSelected && "border-l-2 bg-accent/40",
                    isSelected && (isP2 ? "border-l-blue-500" : "border-l-orange-500"),
                  )}
                >
                  <div className="flex min-w-0 items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="flex size-5 shrink-0 items-center justify-center rounded bg-muted text-[10px] font-medium tabular-nums">
                        {idx + 1}
                      </span>
                      <div className="min-w-0">
                        <span className="block truncate text-xs font-medium">{getRowLabel(category, row)}</span>
                        {subLabel && (
                          <span className="block text-[10px] text-muted-foreground">{subLabel}</span>
                        )}
                      </div>
                      {row.flag && row.flag !== "OK" && (
                        <Badge variant="outline" className="shrink-0 px-1 py-0 text-[9px]">
                          {row.flag}
                        </Badge>
                      )}
                    </div>
                    <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                      {getMetricLabel(category, row, panelType)}
                    </span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-muted">
                    <div className={cn("h-full rounded-full", barColor, getBarWidth(metric, maxMetric))} />
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </Card>
  )
}

// ──────────────────────────────────────────────────────────────
// Chart zoom hook — drag-to-zoom (div-based pixel tracking)
// recharts onMouseMove는 data 변경 후 불안정하므로 div native 이벤트 사용
// yAxisWidth/marginRight는 chart layout과 맞춰야 함
// ──────────────────────────────────────────────────────────────
function useChartZoom(defaultDomain, yAxisWidth = 50, marginRight = 8) {
  const [domain, setDomain] = useState(defaultDomain)
  const [area, setArea]     = useState({ x1: null, x2: null })
  const selecting           = useRef(false)
  const x1Ref               = useRef(null)
  const x2Ref               = useRef(null)
  const x1PxRef             = useRef(null)  // mousedown 픽셀 X (드래그 거리 판별용)
  const wrapperRef          = useRef(null)

  useEffect(() => {
    const handleMouseUp = (e) => {
      if (!selecting.current) return
      selecting.current = false
      const x1 = x1Ref.current
      const x2 = x2Ref.current
      const dragPx = x1PxRef.current != null ? Math.abs(e.clientX - x1PxRef.current) : 0
      // 5px 미만은 클릭으로 처리 → 더블클릭 리셋이 발동할 수 있도록 줌 미적용
      if (x1 != null && x2 != null && x1 !== x2 && dragPx >= 5) {
        const [lo, hi] = [x1, x2].sort((a, b) => a - b)
        setDomain([lo, hi])
      }
      setArea({ x1: null, x2: null })
      x1Ref.current = null
      x2Ref.current = null
      x1PxRef.current = null
    }
    window.addEventListener("mouseup", handleMouseUp)
    return () => window.removeEventListener("mouseup", handleMouseUp)
  }, [])

  const pixelToData = (clientX, dataMin, dataMax) => {
    if (!wrapperRef.current || !isFinite(dataMin) || !isFinite(dataMax) || dataMin === dataMax) return null
    const rect = wrapperRef.current.getBoundingClientRect()
    const plotLeft  = yAxisWidth
    const plotRight = rect.width - marginRight
    const plotWidth = plotRight - plotLeft
    if (plotWidth <= 0) return null
    const relX = Math.max(0, Math.min(1, (clientX - rect.left - plotLeft) / plotWidth))
    return dataMin + relX * (dataMax - dataMin)
  }

  const onWrapperMouseDown = (e, dataMin, dataMax) => {
    selecting.current = true
    x1PxRef.current = e.clientX
    const v = pixelToData(e.clientX, dataMin, dataMax)
    x1Ref.current = v
    x2Ref.current = v
  }
  const onWrapperMouseMove = (e, dataMin, dataMax) => {
    if (!selecting.current) return
    const v = pixelToData(e.clientX, dataMin, dataMax)
    if (v == null) return
    if (x1Ref.current == null) x1Ref.current = v
    x2Ref.current = v
    setArea({ x1: x1Ref.current, x2: v })
  }
  const reset = () => {
    selecting.current = false
    setDomain(defaultDomain)
    setArea({ x1: null, x2: null })
    x1Ref.current = null
    x2Ref.current = null
    x1PxRef.current = null
  }
  const isZoomed = domain[0] !== defaultDomain[0] || domain[1] !== defaultDomain[1]
  const showArea = area.x1 != null && area.x2 != null && area.x1 !== area.x2

  return { domain, area, showArea, isZoomed, wrapperRef, onWrapperMouseDown, onWrapperMouseMove, reset }
}

// X 범위로 데이터 필터링 — recharts domain prop보다 신뢰성 높음
function filterByXDomain(data, xKey, xDomain) {
  if (!data?.length) return data
  if (!Array.isArray(xDomain) || xDomain[0] === "auto" || xDomain[1] === "auto") return data
  const [lo, hi] = xDomain
  return data.filter(d => { const x = Number(d[xKey]); return isFinite(x) && x >= lo && x <= hi })
}

// 필터링된 데이터에서 Y min/max 계산 (여백 3%)
function computeYRange(data, yKeys, padFrac = 0.03) {
  if (!data?.length || !yKeys.length) return ["auto", "auto"]
  let mn = Infinity, mx = -Infinity
  for (const d of data) {
    for (const k of yKeys) { const v = Number(d[k]); if (isFinite(v)) { mn = Math.min(mn, v); mx = Math.max(mx, v) } }
  }
  if (!isFinite(mn) || mn === mx) return ["auto", "auto"]
  const pad = (mx - mn) * padFrac
  return [mn - pad, mx + pad]
}

// OES 스펙트럼: intensity vs wavelength (all time bins median)
function buildSpectrumData(rows) {
  if (!rows?.length) return []
  const byWl = new Map()
  for (const r of rows) {
    const wl  = Math.round(Number(r.wavelength) * 2) / 2
    const val = Number(r.value)
    if (!Number.isFinite(wl) || !Number.isFinite(val)) continue
    const isRef = r.phase === "ref" || r.group === "ref"
    if (!byWl.has(wl)) byWl.set(wl, { ref: [], comp: [] })
    if (isRef) byWl.get(wl).ref.push(val)
    else        byWl.get(wl).comp.push(val)
  }
  const med = (arr) => arr.length ? [...arr].sort((a, b) => a - b)[Math.floor(arr.length / 2)] : null
  return Array.from(byWl.entries())
    .sort(([a], [b]) => a - b)
    .map(([wl, { ref, comp }]) => ({ wl, ref: med(ref), comp: med(comp) }))
}

// ──────────────────────────────────────────────────────────────
// LegendPanel — 계층형 토글 패널 (그룹 + 개별 wafer)
// groups = [{ groupKey, label, color, series: [{ key, label }] }]
// extras = [{ key, label, colorStyle }]
// ──────────────────────────────────────────────────────────────
function LegendPanel({ vis, onToggle, onGroupToggle, groups = [], extras = [] }) {
  return (
    <div className="flex w-[150px] shrink-0 flex-col gap-0 overflow-y-auto rounded-lg border p-2" style={{ maxHeight: 300 }}>
      <p className="mb-1 text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">Legend</p>

      {groups.map(({ groupKey, label, color, series }) => {
        const allOn = series.every((s) => vis[s.key] !== false)
        const anyOn = series.some((s) => vis[s.key] !== false)
        return (
          <div key={groupKey}>
            {/* 그룹 헤더 — 전체 토글 */}
            <button
              type="button"
              onClick={() => onGroupToggle(groupKey, series)}
              className={cn(
                "flex w-full items-center gap-1.5 rounded px-1 py-0.5 text-left text-[10px] font-semibold transition-colors hover:bg-muted/50",
                !anyOn && "opacity-35",
              )}
            >
              <span
                className="size-3 shrink-0 rounded-sm border border-black/10"
                style={{ background: color, opacity: allOn ? 1 : anyOn ? 0.5 : 0.2 }}
              />
              <span className="truncate">{label}</span>
            </button>
            {/* 개별 wafer 행 */}
            {series.map((s) => {
              const on = vis[s.key] !== false
              return (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => onToggle(s.key)}
                  className={cn(
                    "flex w-full items-center gap-1 rounded py-[1px] pl-4 pr-1 text-left text-[10px] transition-colors hover:bg-muted/50",
                    !on && "opacity-35",
                  )}
                >
                  <span className="size-2 shrink-0 rounded-sm" style={{ background: color }} />
                  <span className="truncate font-mono">{s.label}</span>
                </button>
              )
            })}
          </div>
        )
      })}

      {/* 평면 항목 (median, tube 등) */}
      {extras.map(({ key, label, colorStyle }) => {
        const enabled = vis[key] !== false
        return (
          <button
            key={key}
            type="button"
            onClick={() => onToggle(key)}
            className={cn(
              "flex items-center gap-1.5 rounded px-1 py-0.5 text-left text-[10px] transition-colors hover:bg-muted/50",
              !enabled && "opacity-35",
            )}
          >
            <span className="size-3 shrink-0 rounded-sm border border-black/10" style={colorStyle} />
            <span className="truncate leading-tight">{label}</span>
          </button>
        )
      })}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// TraceDetailWithLegend — 원신호 / Shape / Jitter 탭 + Legend + Zoom
// ──────────────────────────────────────────────────────────────
function TraceDetailWithLegend({ category, selectedKey, refPmDates }) {
  const [vis, setVis]             = useState({ refMed: true, compMed: true, tube: true })
  const [chStep, setChStep]       = useState("")
  const [activeTab, setActiveTab] = useState("shape")

  const shapeZoom = useChartZoom([0, 99])
  const rawZoom   = useChartZoom(["auto", "auto"])

  const { paramName, step: defaultStep } = parseTraceKey(selectedKey)
  const queryRow    = paramName ? { itemName: paramName, traceSensor: paramName } : null
  const detailQuery = usePmSpiderDetailResult(category, queryRow, refPmDates)
  const shapeRows   = detailQuery.data?.trace?.shapeRows ?? []
  const jitterRows  = detailQuery.data?.trace?.jitterRows ?? []
  const trendRows   = detailQuery.data?.trace?.trendRows ?? []

  const chSteps = useMemo(() => {
    const all = new Set([
      ...shapeRows.map((r) => String(r.chStep ?? r.ch_step ?? "")).filter(Boolean),
      ...trendRows.map((r) => String(r.chStep ?? r.ch_step ?? "")).filter(Boolean),
      ...jitterRows.map((r) => String(r.chStep ?? r.ch_step ?? "")).filter(Boolean),
    ])
    return Array.from(all).sort()
  }, [shapeRows, trendRows, jitterRows])

  useEffect(() => { setChStep(defaultStep) }, [selectedKey, defaultStep])

  // 데이터 로드 완료 시 — shape 우선, 없으면 raw로 자동 전환
  useEffect(() => {
    if (detailQuery.isFetching || !detailQuery.data) return
    if (shapeRows.length > 0) setActiveTab("shape")
    else if (trendRows.length > 0) setActiveTab("raw")
  }, [detailQuery.isFetching, detailQuery.data, shapeRows.length, trendRows.length])

  const { data: shapeData, waferSeries, compMedKey, hasTube } = useMemo(
    () => buildShapeData(shapeRows, chStep), [shapeRows, chStep],
  )
  const { series: rawAllSeries, data: rawData } = useMemo(
    () => buildRawSeries(trendRows, chStep), [trendRows, chStep],
  )
  const { data: jitterData, refMed: jRefMed, compMed: jCompMed } = useMemo(
    () => buildJitterKde(jitterRows, chStep), [jitterRows, chStep],
  )

  // wafer series — shape 우선, 없으면 raw 에서 추출
  // group 형식: ref_{lot}_{slot} / comp_{lot}_{slot}
  const shapeRef  = waferSeries.filter((s) => s.group.startsWith("ref_") || s.group === "ref")
  const shapeComp = waferSeries.filter((s) => s.group.startsWith("comp_") || s.group === "comp")
  const rawRef    = rawAllSeries.filter((s) => s.group === "ref").map((s) => ({ key: `ref__${s.slot}`,  group: "ref",  slot: s.slot }))
  const rawComp   = rawAllSeries.filter((s) => s.group === "comp").map((s) => ({ key: `comp__${s.slot}`, group: "comp", slot: s.slot }))
  const refBase   = shapeRef.length  > 0 ? shapeRef  : rawRef
  const compBase  = shapeComp.length > 0 ? shapeComp : rawComp

  const refSeries  = refBase.map((s)  => ({ ...s, label: s.key.replace(/^ref_/, "") }))
  const compSeries = compBase.map((s) => ({ ...s, label: s.key.replace(/^comp_/, "") }))

  // X 범위 필터링된 데이터 — recharts에 넘기면 자동으로 scale 재계산
  const visibleRawData   = useMemo(() => filterByXDomain(rawData,   "x", rawZoom.domain),   [rawData,   rawZoom.domain])
  const visibleShapeData = useMemo(() => filterByXDomain(shapeData, "x", shapeZoom.domain), [shapeData, shapeZoom.domain])

  const rawYKeys   = useMemo(() => [...rawRef.map(s => s.key), ...rawComp.map(s => s.key)], [rawRef, rawComp])
  const rawYDomain = useMemo(() => computeYRange(visibleRawData, rawYKeys), [visibleRawData, rawYKeys])

  const shapeYKeys = useMemo(() => [
    ...refSeries.map(s => s.key), ...compSeries.map(s => s.key),
    "q50", ...(compMedKey ? [compMedKey] : []), "lsl",
  ], [refSeries, compSeries, compMedKey])
  const shapeYDomain = useMemo(() => computeYRange(visibleShapeData, shapeYKeys), [visibleShapeData, shapeYKeys])

  // div 기반 pixel→data 변환을 위한 X 범위
  const shapeXRange = useMemo(() => {
    if (!visibleShapeData.length) return [0, 99]
    const xs = visibleShapeData.map(d => d.x).filter(isFinite)
    return xs.length ? [Math.min(...xs), Math.max(...xs)] : [0, 99]
  }, [visibleShapeData])
  const rawXRange = useMemo(() => {
    if (!visibleRawData.length) return [0, 0]
    const xs = visibleRawData.map(d => d.x).filter(isFinite)
    return xs.length ? [Math.min(...xs), Math.max(...xs)] : [0, 0]
  }, [visibleRawData])

  const toggleVis   = (k) => setVis((p) => ({ ...p, [k]: p[k] !== false ? false : true }))
  const toggleGroup = (_gk, series) => {
    const allOn = series.every((s) => vis[s.key] !== false)
    setVis((p) => { const n = { ...p }; series.forEach((s) => { n[s.key] = !allOn }); return n })
  }

  const legendGroups = [
    { groupKey: "ref",  label: `REF (${refSeries.length})`,   color: TC.REF_LINE,  series: refSeries },
    { groupKey: "comp", label: `COMP (${compSeries.length})`, color: TC.COMP_LINE, series: compSeries },
  ]
  const shapeExtras = [
    { key: "refMed",  label: "REF med",       colorStyle: { background: TC.TUBE_Q50 } },
    ...(compMedKey ? [{ key: "compMed", label: "COMP med", colorStyle: { background: TC.COMP_MED } }] : []),
    ...(hasTube ? [{ key: "tube", label: "Tube (LSL–USL)", colorStyle: { background: TC.TUBE_FILL, border: `1px solid ${TC.TUBE_STROKE}` } }] : []),
  ]

  // jitter: group-level visibility (per-wafer toggle → group KDE 제어)
  const showJRef  = refSeries.some((s)  => vis[s.key] !== false)
  const showJComp = compSeries.some((s) => vis[s.key] !== false)

  const hasRaw    = trendRows.length > 0
  const hasShape  = shapeRows.length > 0
  const hasJitter = jitterRows.length > 0

  const TABS = [
    { id: "raw",    label: "원신호", disabled: !hasRaw },
    { id: "shape",  label: "Shape",  disabled: !hasShape },
    { id: "jitter", label: "Jitter", disabled: !hasJitter },
  ]

  if (detailQuery.isFetching && !detailQuery.data) {
    return (
      <Card className="rounded-lg py-0">
        <CardContent className="flex min-h-48 items-center justify-center p-3 text-sm text-muted-foreground">
          <Activity className="mr-2 size-4 animate-pulse" /> 데이터 조회 중...
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="rounded-lg py-0">
      <CardContent className="p-3">
        {/* 헤더 */}
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium">Trace · {paramName || selectedKey}</p>
            <div className="flex gap-1">
              {TABS.map(({ id, label, disabled }) => (
                <button key={id} type="button" disabled={disabled}
                  onClick={() => setActiveTab(id)}
                  className={cn(
                    "rounded px-2 py-0.5 text-xs transition-colors",
                    activeTab === id ? "bg-primary text-primary-foreground" : "border bg-background hover:bg-muted",
                    disabled && "cursor-not-allowed opacity-40",
                  )}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* zoom reset */}
            {activeTab === "shape" && shapeZoom.isZoomed && (
              <button type="button" onClick={shapeZoom.reset}
                className="rounded border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted">
                확대 초기화
              </button>
            )}
            {activeTab === "raw" && rawZoom.isZoomed && (
              <button type="button" onClick={rawZoom.reset}
                className="rounded border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted">
                확대 초기화
              </button>
            )}
            {chSteps.length > 0 && <StepSelector steps={chSteps} value={chStep} onChange={setChStep} />}
          </div>
        </div>

        {/* ── 원신호 탭 ── */}
        {activeTab === "raw" && (
          !rawData.length ? (
            <div className="flex min-h-40 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              원신호(raw trend) 데이터가 없습니다
            </div>
          ) : (
            <div className="flex gap-3">
              <div ref={rawZoom.wrapperRef} className="min-w-0 flex-1" style={{ cursor: "crosshair" }}
                onMouseDown={(e) => rawZoom.onWrapperMouseDown(e, rawXRange[0], rawXRange[1])}
                onMouseMove={(e) => rawZoom.onWrapperMouseMove(e, rawXRange[0], rawXRange[1])}
                onDoubleClick={rawZoom.reset}>
                <ResponsiveContainer width="100%" height={240}>
                  <ComposedChart data={visibleRawData} margin={{ top: 4, right: 8, bottom: 22, left: 0 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]}
                      tickFormatter={(v) => formatNumber(v, 1)}
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }}
                      label={{ value: "step time (s)", position: "insideBottom", offset: -8, fontSize: 10, fill: "var(--muted-foreground)" }} />
                    <YAxis domain={rawYDomain} tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }} width={50} />
                    <Tooltip formatter={(v, n) => [formatNumber(v, 2), n]}
                      labelFormatter={(v) => `t = ${formatNumber(v, 2)} s`}
                      contentStyle={{ fontSize: 11 }} />
                    {rawRef.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.REF_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {rawComp.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.COMP_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {rawZoom.showArea && (
                      <ReferenceArea x1={rawZoom.area.x1} x2={rawZoom.area.x2}
                        fill="rgba(59,130,246,0.15)" stroke="rgba(59,130,246,0.4)" />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <LegendPanel vis={vis} onToggle={toggleVis} onGroupToggle={toggleGroup}
                groups={legendGroups} extras={[]} />
            </div>
          )
        )}

        {/* ── Shape 탭 ── */}
        {activeTab === "shape" && (
          !shapeData.length ? (
            <div className="flex min-h-40 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              {paramName || selectedKey} — shape 데이터가 없습니다
            </div>
          ) : (
            <div className="flex gap-3">
              <div ref={shapeZoom.wrapperRef} className="min-w-0 flex-1" style={{ cursor: "crosshair" }}
                onMouseDown={(e) => shapeZoom.onWrapperMouseDown(e, shapeXRange[0], shapeXRange[1])}
                onMouseMove={(e) => shapeZoom.onWrapperMouseMove(e, shapeXRange[0], shapeXRange[1])}
                onDoubleClick={shapeZoom.reset}>
                <ResponsiveContainer width="100%" height={240}>
                  <ComposedChart data={visibleShapeData} margin={{ top: 4, right: 8, bottom: 22, left: 0 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]}
                      tickFormatter={(v) => String(Math.round(v))}
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }}
                      label={{ value: "normalized phase", position: "insideBottom", offset: -8, fontSize: 10, fill: "var(--muted-foreground)" }} />
                    <YAxis domain={shapeYDomain} tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }} width={50}
                      tickFormatter={(v) => formatNumber(v, 3)} />
                    <Tooltip formatter={(v, n) => [formatNumber(v, 3), n]}
                      labelFormatter={(v) => `phase ${v}`} contentStyle={{ fontSize: 11 }} />
                    {vis.tube !== false && hasTube && (
                      <>
                        <Area type="monotone" dataKey="lsl" stackId="tube"
                          fillOpacity={0} stroke="none" dot={false} connectNulls activeDot={false}
                          legendType="none" isAnimationActive={false} />
                        <Area type="monotone" dataKey="band" stackId="tube"
                          fill={TC.TUBE_FILL} fillOpacity={1} stroke={TC.TUBE_STROKE} strokeWidth={0.5}
                          dot={false} connectNulls activeDot={false}
                          legendType="none" isAnimationActive={false} name="Tube" />
                      </>
                    )}
                    {refSeries.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.REF_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {compSeries.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.COMP_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {vis.refMed !== false && hasTube && (
                      <Line type="monotone" dataKey="q50"
                        stroke={TC.TUBE_Q50} strokeWidth={1.5} strokeDasharray="4 2"
                        dot={false} connectNulls isAnimationActive={false} name="REF med" />
                    )}
                    {vis.compMed !== false && compMedKey && (
                      <Line type="monotone" dataKey={compMedKey}
                        stroke={TC.COMP_MED} strokeWidth={2}
                        dot={false} connectNulls isAnimationActive={false} name="COMP med" />
                    )}
                    {shapeZoom.showArea && (
                      <ReferenceArea x1={shapeZoom.area.x1} x2={shapeZoom.area.x2}
                        fill="rgba(59,130,246,0.15)" stroke="rgba(59,130,246,0.4)" />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <LegendPanel vis={vis} onToggle={toggleVis} onGroupToggle={toggleGroup}
                groups={legendGroups} extras={shapeExtras} />
            </div>
          )
        )}

        {/* ── Jitter 탭 ── */}
        {activeTab === "jitter" && (
          !jitterData.length ? (
            <div className="flex min-h-40 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              Jitter 데이터가 없습니다
            </div>
          ) : (
            <div className="flex gap-3">
              <div className="min-w-0 flex-1">
                <ResponsiveContainer width="100%" height={240}>
                  <ComposedChart data={jitterData} margin={{ top: 4, right: 8, bottom: 22, left: 0 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="x" type="number" domain={["dataMin", "dataMax"]}
                      tickFormatter={(v) => formatNumber(v, 3)}
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }}
                      label={{ value: "jitter RMS", position: "insideBottom", offset: -8, fontSize: 10, fill: "var(--muted-foreground)" }} />
                    <YAxis tickFormatter={(v) => formatNumber(v, 2)}
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }} width={50}
                      label={{ value: "density", angle: -90, position: "insideLeft", offset: 10, fontSize: 10, fill: "var(--muted-foreground)" }} />
                    <Tooltip formatter={(v, n) => [formatNumber(v, 5), n]}
                      labelFormatter={(v) => `jitter = ${formatNumber(v, 4)}`}
                      contentStyle={{ fontSize: 11 }} />
                    {showJRef && (
                      <Area type="monotone" dataKey="ref"
                        stroke={TC.REF_MED} strokeWidth={2}
                        fill="rgba(37,99,235,0.15)" fillOpacity={1}
                        dot={false} connectNulls isAnimationActive={false} name="REF" />
                    )}
                    {showJComp && (
                      <Area type="monotone" dataKey="comp"
                        stroke={TC.COMP_MED} strokeWidth={2}
                        fill="rgba(234,88,12,0.15)" fillOpacity={1}
                        dot={false} connectNulls isAnimationActive={false} name="COMP" />
                    )}
                    {showJRef && jRefMed != null && (
                      <ReferenceLine x={jRefMed} stroke={TC.REF_MED} strokeWidth={1.5} strokeDasharray="4 3"
                        label={{ value: "ref", fontSize: 9, fill: TC.REF_MED, position: "insideTopRight" }} />
                    )}
                    {showJComp && jCompMed != null && (
                      <ReferenceLine x={jCompMed} stroke={TC.COMP_MED} strokeWidth={1.5} strokeDasharray="4 3"
                        label={{ value: "comp", fontSize: 9, fill: TC.COMP_MED, position: "insideTopLeft" }} />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <LegendPanel vis={vis} onToggle={toggleVis} onGroupToggle={toggleGroup}
                groups={legendGroups} extras={[]} />
            </div>
          )
        )}
      </CardContent>
    </Card>
  )
}

// ── OES intensity heatmap 헬퍼 ────────────────────────────────
const N_PHASE_BINS = 40

function buildIntensityData(rows) {
  if (!rows?.length) return null
  const refBuf  = new Map()
  const compBuf = new Map()
  const wlSet   = new Set()

  for (const r of rows) {
    const wl  = Math.round(Number(r.wavelength) * 2) / 2
    const tp  = Number(r.trajPhase ?? r.traj_phase ?? 0)
    const val = Number(r.value)
    if (!Number.isFinite(wl) || !Number.isFinite(tp) || !Number.isFinite(val)) continue
    const bin = Math.round(tp * N_PHASE_BINS) / N_PHASE_BINS
    const key = `${bin}|${wl}`
    wlSet.add(wl)
    const buf  = r.phase === "ref" ? refBuf : compBuf
    const prev = buf.get(key) ?? { s: 0, n: 0 }
    buf.set(key, { s: prev.s + val, n: prev.n + 1 })
  }

  const wavelengths = Array.from(wlSet).sort((a, b) => a - b)
  const phaseSet    = new Set()
  for (const k of refBuf.keys())  phaseSet.add(Number(k.split("|")[0]))
  for (const k of compBuf.keys()) phaseSet.add(Number(k.split("|")[0]))
  const phases = Array.from(phaseSet).sort((a, b) => a - b)
  if (!wavelengths.length || !phases.length) return null

  const avg = (buf, bin, wl) => { const e = buf.get(`${bin}|${wl}`); return e ? e.s / e.n : null }

  let rMin = Infinity, rMax = -Infinity
  let cMin = Infinity, cMax = -Infinity
  let dMin = Infinity, dMax = -Infinity
  for (const b of phases) {
    for (const w of wavelengths) {
      const rv = avg(refBuf,  b, w); if (rv != null) { rMin = Math.min(rMin, rv); rMax = Math.max(rMax, rv) }
      const cv = avg(compBuf, b, w); if (cv != null) { cMin = Math.min(cMin, cv); cMax = Math.max(cMax, cv) }
      if (rv != null && cv != null) { const d = cv - rv; dMin = Math.min(dMin, d); dMax = Math.max(dMax, d) }
    }
  }
  return { wavelengths, phases, avg, refBuf, compBuf, rMin, rMax, cMin, cMax, dMin, dMax }
}

// 특정 wavelength의 time-series: per-wafer + REF tube + median
function buildWavelengthLineData(rows, targetWl) {
  if (!rows?.length || targetWl == null) return { data: [], refSeries: [], compSeries: [] }
  const N = N_PHASE_BINS
  const refBins  = new Map()
  const compBins = new Map()
  const refWaferBins  = new Map() // `${slot}|${bin}` → [vals]
  const compWaferBins = new Map()
  const refSlots  = new Set()
  const compSlots = new Set()

  for (const r of rows) {
    const wl  = Math.round(Number(r.wavelength) * 2) / 2
    if (wl !== targetWl) continue
    const tp   = Number(r.trajPhase ?? r.traj_phase ?? 0)
    const val  = Number(r.value)
    const slot = String(r.slotNo ?? r.slot_no ?? r.wafer_id ?? 0)
    if (!Number.isFinite(tp) || !Number.isFinite(val)) continue
    const bin   = Math.round(tp * N) / N
    const isRef = r.phase === "ref"

    const agg = isRef ? refBins : compBins
    if (!agg.has(bin)) agg.set(bin, [])
    agg.get(bin).push(val)

    const wMap = isRef ? refWaferBins : compWaferBins
    const wKey = `${slot}|${bin}`
    if (!wMap.has(wKey)) wMap.set(wKey, [])
    wMap.get(wKey).push(val)
    ;(isRef ? refSlots : compSlots).add(slot)
  }

  const binSet = new Set([...refBins.keys(), ...compBins.keys()])
  if (!binSet.size) return { data: [], refSeries: [], compSeries: [] }

  const med = (arr) => {
    if (!arr?.length) return null
    const s = [...arr].sort((a, b) => a - b)
    return s[Math.floor(s.length / 2)]
  }
  const pct = (arr, p) => {
    if (!arr?.length) return null
    const s = [...arr].sort((a, b) => a - b)
    return s[Math.floor(s.length * p)]
  }
  const avgArr = (arr) => arr?.length ? arr.reduce((s, v) => s + v, 0) / arr.length : null

  const refSlotList  = Array.from(refSlots)
  const compSlotList = Array.from(compSlots)

  const data = Array.from(binSet).sort((a, b) => a - b).map((bin) => {
    const rv    = refBins.get(bin)
    const cv    = compBins.get(bin)
    const refLo = pct(rv, 0.1)
    const refHi = pct(rv, 0.9)
    const band  = refLo != null && refHi != null ? refHi - refLo : null
    const row   = { t: bin, refMed: med(rv), refLo, band, compMed: med(cv) }
    for (const slot of refSlotList)  row[`ref__${slot}`]  = avgArr(refWaferBins.get(`${slot}|${bin}`))
    for (const slot of compSlotList) row[`comp__${slot}`] = avgArr(compWaferBins.get(`${slot}|${bin}`))
    return row
  })

  const refSeries  = refSlotList.map((slot)  => ({ key: `ref__${slot}`,  group: "ref",  slot }))
  const compSeries = compSlotList.map((slot) => ({ key: `comp__${slot}`, group: "comp", slot }))
  return { data, refSeries, compSeries }
}

function intensityHsl(t) {
  const h = Math.round(270 - t * 210)
  const s = Math.round(70 + t * 20)
  const l = Math.round(15 + t * 60)
  return `hsl(${h},${s}%,${l}%)`
}

function oobHsl(d, absMax) {
  if (absMax <= 0) return "hsl(0,0%,90%)"
  const t = Math.max(-1, Math.min(1, d / absMax))
  return t >= 0
    ? `hsl(0,${Math.round(t * 85)}%,${Math.round(95 - t * 45)}%)`
    : `hsl(240,${Math.round(-t * 80)}%,${Math.round(95 + t * 40)}%)`
}

function HeatmapGrid({ title, titleColor, phases, wavelengths, getColor, selectedWl, onWlClick }) {
  const wlStep  = Math.max(1, Math.ceil(wavelengths.length / 80))
  const phStep  = Math.max(1, Math.ceil(phases.length / 40))
  const dWls    = wavelengths.filter((_, i) => i % wlStep === 0)
  const dPhs    = phases.filter((_, i) => i % phStep === 0)

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-0.5">
      <p className="text-center text-[10px] font-semibold" style={{ color: titleColor }}>{title}</p>
      <div
        className="overflow-hidden rounded border"
        style={{ display: "grid", gridTemplateColumns: `repeat(${dWls.length}, 1fr)` }}
      >
        {dPhs.map((ph) =>
          dWls.map((wl) => (
            <div
              key={`${ph}|${wl}`}
              onClick={() => onWlClick?.(wl)}
              style={{
                height: 5,
                backgroundColor: getColor(ph, wl),
                cursor: "crosshair",
                ...(wl === selectedWl && { filter: "brightness(2) contrast(1.3)", outline: "1px solid rgba(255,255,255,0.7)" }),
              }}
            />
          ))
        )}
      </div>
      <div className="flex justify-between text-[9px] text-muted-foreground">
        <span>{Math.round(wavelengths[0])} nm</span>
        <span className="text-center">wavelength →</span>
        <span>{Math.round(wavelengths[wavelengths.length - 1])} nm</span>
      </div>
    </div>
  )
}

// ── OES: wavelength 선택 시 시계열 + 스펙트럼 탭 ──────────────
function OesWavelengthLineChart({ trajectoryRows, selectedWl, onClose }) {
  const [vis, setVis]             = useState({ refMed: true, compMed: true, tube: true })
  const [activeTab, setActiveTab] = useState("시계열")
  const timeZoom   = useChartZoom([0, 1], 42)
  const specZoom   = useChartZoom(["auto", "auto"], 42)

  const { data: timeData, refSeries: rawRef, compSeries: rawComp } = useMemo(
    () => buildWavelengthLineData(trajectoryRows, selectedWl),
    [trajectoryRows, selectedWl],
  )
  const specData = useMemo(() => buildSpectrumData(trajectoryRows), [trajectoryRows])

  const refSeries  = rawRef.map((s)  => ({ ...s, label: s.slot }))
  const compSeries = rawComp.map((s) => ({ ...s, label: s.slot }))
  const hasTube    = timeData.some((d) => d.band != null)

  const toggleVis   = (k) => setVis((p) => ({ ...p, [k]: p[k] !== false ? false : true }))
  const toggleGroup = (_gk, series) => {
    const allOn = series.every((s) => vis[s.key] !== false)
    setVis((p) => { const n = { ...p }; series.forEach((s) => { n[s.key] = !allOn }); return n })
  }

  const legendGroups = [
    { groupKey: "ref",  label: `REF (${refSeries.length})`,  color: TC.REF_LINE,  series: refSeries },
    { groupKey: "comp", label: `COMP (${compSeries.length})`, color: TC.COMP_LINE, series: compSeries },
  ]
  const timeExtras = [
    { key: "refMed",  label: "REF median",  colorStyle: { background: "#2563eb" } },
    { key: "compMed", label: "COMP median", colorStyle: { background: "#ea580c" } },
    ...(hasTube ? [{ key: "tube", label: "Tube (p10–p90)", colorStyle: { background: "rgba(37,99,235,0.1)", border: "1px solid #93c5fd" } }] : []),
  ]

  // 스펙트럼: REF/COMP visibility (group-level)
  const showSpecRef  = refSeries.length  === 0 || refSeries.some((s)  => vis[s.key] !== false)
  const showSpecComp = compSeries.length === 0 || compSeries.some((s) => vis[s.key] !== false)

  // X 범위 필터링된 데이터
  const visibleTimeData = useMemo(() => filterByXDomain(timeData, "t",  timeZoom.domain), [timeData, timeZoom.domain])
  const visibleSpecData = useMemo(() => filterByXDomain(specData, "wl", specZoom.domain), [specData, specZoom.domain])

  const timeYKeys   = useMemo(() => [...refSeries.map(s => s.key), ...compSeries.map(s => s.key), "refMed", "compMed", "refLo"], [refSeries, compSeries])
  const timeYDomain = useMemo(() => computeYRange(visibleTimeData, timeYKeys), [visibleTimeData, timeYKeys])
  const specYDomain = useMemo(() => computeYRange(visibleSpecData, ["ref", "comp"]), [visibleSpecData])

  const timeXRange = useMemo(() => {
    if (!visibleTimeData.length) return [0, 1]
    const ts = visibleTimeData.map(d => d.t).filter(isFinite)
    return ts.length ? [Math.min(...ts), Math.max(...ts)] : [0, 1]
  }, [visibleTimeData])
  const specXRange = useMemo(() => {
    if (!visibleSpecData.length) return [200, 800]
    const wls = visibleSpecData.map(d => d.wl).filter(isFinite)
    return wls.length ? [Math.min(...wls), Math.max(...wls)] : [200, 800]
  }, [visibleSpecData])

  const TABS = ["시계열", "스펙트럼"]

  return (
    <Card className="rounded-lg py-0">
      <CardContent className="p-3">
        {/* 헤더 */}
        <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold">
              OES · <span className="text-primary">{selectedWl != null ? `${selectedWl} nm` : "전체"}</span>
            </p>
            <div className="flex gap-1">
              {TABS.map((t) => (
                <button key={t} type="button" onClick={() => setActiveTab(t)}
                  className={cn(
                    "rounded px-2 py-0.5 text-[10px] transition-colors",
                    activeTab === t ? "bg-primary text-primary-foreground" : "border bg-background hover:bg-muted",
                    t === "시계열" && selectedWl == null && "cursor-not-allowed opacity-40",
                  )}
                  disabled={t === "시계열" && selectedWl == null}>
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {activeTab === "시계열" && timeZoom.isZoomed && (
              <button type="button" onClick={timeZoom.reset}
                className="rounded border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted">확대 초기화</button>
            )}
            {activeTab === "스펙트럼" && specZoom.isZoomed && (
              <button type="button" onClick={specZoom.reset}
                className="rounded border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted">확대 초기화</button>
            )}
            {onClose && (
              <button type="button" onClick={onClose}
                className="rounded px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted hover:text-foreground">✕</button>
            )}
          </div>
        </div>

        {/* ── 시계열 탭 ── */}
        {activeTab === "시계열" && (
          !timeData.length ? (
            <div className="flex min-h-[100px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              <span className="mr-1 font-semibold text-foreground">{selectedWl} nm</span> trajectory 데이터 없음
            </div>
          ) : (
            <div className="flex gap-3">
              <div ref={timeZoom.wrapperRef} className="min-w-0 flex-1" style={{ cursor: "crosshair" }}
                onMouseDown={(e) => timeZoom.onWrapperMouseDown(e, timeXRange[0], timeXRange[1])}
                onMouseMove={(e) => timeZoom.onWrapperMouseMove(e, timeXRange[0], timeXRange[1])}
                onDoubleClick={timeZoom.reset}>
                <ResponsiveContainer width="100%" height={180}>
                  <ComposedChart data={visibleTimeData} margin={{ top: 4, right: 8, left: 0, bottom: 20 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="t" type="number" domain={["dataMin", "dataMax"]}
                      tickFormatter={(v) => Number(v).toFixed(2)}
                      tick={{ fontSize: 9, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }}
                      label={{ value: "time (0 → 1)", position: "insideBottom", offset: -8, fontSize: 9, fill: "var(--muted-foreground)" }} />
                    <YAxis domain={timeYDomain} tick={{ fontSize: 9, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }} width={42}
                      tickFormatter={(v) => formatNumber(v, 1)} />
                    <Tooltip formatter={(v, n) => [formatNumber(v, 3), n]}
                      labelFormatter={(t) => `time: ${Number(t).toFixed(3)}`}
                      contentStyle={{ fontSize: 10 }} />
                    {vis.tube !== false && hasTube && (
                      <>
                        <Area type="monotone" dataKey="refLo" stackId="tube"
                          fillOpacity={0} stroke="none" dot={false} connectNulls activeDot={false}
                          legendType="none" isAnimationActive={false} name="p10" />
                        <Area type="monotone" dataKey="band" stackId="tube"
                          fill="rgba(37,99,235,0.10)" fillOpacity={1} stroke="#93c5fd" strokeWidth={0.5}
                          dot={false} connectNulls activeDot={false}
                          legendType="none" isAnimationActive={false} name="p10–p90" />
                      </>
                    )}
                    {refSeries.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.REF_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {compSeries.map((s) => vis[s.key] !== false && (
                      <Line key={s.key} type="monotone" dataKey={s.key}
                        stroke={TC.COMP_LINE} strokeWidth={1}
                        dot={false} connectNulls activeDot={false}
                        legendType="none" isAnimationActive={false} />
                    ))}
                    {vis.refMed !== false && (
                      <Line type="monotone" dataKey="refMed"
                        stroke="#2563eb" strokeWidth={1.5} strokeDasharray="4 2"
                        dot={false} connectNulls isAnimationActive={false} name="REF med" />
                    )}
                    {vis.compMed !== false && (
                      <Line type="monotone" dataKey="compMed"
                        stroke="#ea580c" strokeWidth={1.5}
                        dot={false} connectNulls isAnimationActive={false} name="COMP med" />
                    )}
                    {timeZoom.showArea && (
                      <ReferenceArea x1={timeZoom.area.x1} x2={timeZoom.area.x2}
                        fill="rgba(59,130,246,0.15)" stroke="rgba(59,130,246,0.4)" />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <LegendPanel vis={vis} onToggle={toggleVis} onGroupToggle={toggleGroup}
                groups={legendGroups} extras={timeExtras} />
            </div>
          )
        )}

        {/* ── 스펙트럼 탭 ── */}
        {activeTab === "스펙트럼" && (
          !specData.length ? (
            <div className="flex min-h-[100px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
              스펙트럼 데이터 없음
            </div>
          ) : (
            <div className="flex gap-3">
              <div ref={specZoom.wrapperRef} className="min-w-0 flex-1" style={{ cursor: "crosshair" }}
                onMouseDown={(e) => specZoom.onWrapperMouseDown(e, specXRange[0], specXRange[1])}
                onMouseMove={(e) => specZoom.onWrapperMouseMove(e, specXRange[0], specXRange[1])}
                onDoubleClick={specZoom.reset}>
                <ResponsiveContainer width="100%" height={180}>
                  <ComposedChart data={visibleSpecData} margin={{ top: 4, right: 8, left: 0, bottom: 20 }}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="wl" type="number" domain={["dataMin", "dataMax"]}
                      tickFormatter={(v) => `${Math.round(v)}`}
                      tick={{ fontSize: 9, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }}
                      label={{ value: "wavelength (nm)", position: "insideBottom", offset: -8, fontSize: 9, fill: "var(--muted-foreground)" }} />
                    <YAxis domain={specYDomain} tick={{ fontSize: 9, fill: "var(--muted-foreground)" }}
                      tickLine={false} axisLine={{ stroke: "var(--border)" }} width={42}
                      tickFormatter={(v) => formatNumber(v, 1)} />
                    <Tooltip formatter={(v, n) => [formatNumber(v, 3), n]}
                      labelFormatter={(v) => `${Math.round(v)} nm`}
                      contentStyle={{ fontSize: 10 }} />
                    {showSpecRef && (
                      <Line type="monotone" dataKey="ref"
                        stroke={TC.REF_MED} strokeWidth={1.5}
                        dot={false} connectNulls isAnimationActive={false} name="REF median" />
                    )}
                    {showSpecComp && (
                      <Line type="monotone" dataKey="comp"
                        stroke={TC.COMP_MED} strokeWidth={1.5}
                        dot={false} connectNulls isAnimationActive={false} name="COMP median" />
                    )}
                    {selectedWl != null && (
                      <ReferenceLine x={selectedWl} stroke="rgba(59,130,246,0.6)" strokeWidth={1} strokeDasharray="3 2"
                        label={{ value: `${selectedWl}`, fontSize: 8, fill: "#2563eb", position: "insideTopRight" }} />
                    )}
                    {specZoom.showArea && (
                      <ReferenceArea x1={specZoom.area.x1} x2={specZoom.area.x2}
                        fill="rgba(59,130,246,0.15)" stroke="rgba(59,130,246,0.4)" />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <LegendPanel vis={vis} onToggle={toggleVis} onGroupToggle={toggleGroup}
                groups={[
                  { groupKey: "ref",  label: "REF",  color: TC.REF_MED,  series: [] },
                  { groupKey: "comp", label: "COMP", color: TC.COMP_MED, series: [] },
                ]}
                extras={[]} />
            </div>
          )
        )}
      </CardContent>
    </Card>
  )
}

// ── OES intensity heatmap (REF / COMP / OOB) ─────────────────
function OesIntensityHeatmaps({ trajectoryRows, selectedStep, isLoading }) {
  const [selectedWl, setSelectedWl] = useState(null)
  const data = useMemo(() => buildIntensityData(trajectoryRows), [trajectoryRows])

  if (!selectedStep) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
        랭킹에서 rcp_step을 선택하면 intensity heatmap이 표시됩니다
      </div>
    )
  }
  if (isLoading) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-lg border text-sm text-muted-foreground">
        <Waves className="mr-2 size-4 animate-pulse" /> OES intensity 조회 중...
      </div>
    )
  }
  if (!data) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
        step <span className="mx-1 font-semibold text-foreground">{selectedStep}</span>의 intensity 데이터가 없습니다
      </div>
    )
  }

  const { wavelengths, phases, avg, refBuf, compBuf, rMin, rMax, cMin, cMax, dMin, dMax } = data
  const absD = Math.max(Math.abs(dMin), Math.abs(dMax), 0.01)

  const refColor  = (ph, wl) => { const v = avg(refBuf,  ph, wl); return v != null ? intensityHsl((v - rMin) / (rMax - rMin || 1)) : "#0a0a1e" }
  const compColor = (ph, wl) => { const v = avg(compBuf, ph, wl); return v != null ? intensityHsl((v - cMin) / (cMax - cMin || 1)) : "#0a0a1e" }
  const oobColor  = (ph, wl) => { const rv = avg(refBuf, ph, wl); const cv = avg(compBuf, ph, wl); return (rv != null && cv != null) ? oobHsl(cv - rv, absD) : "hsl(0,0%,88%)" }

  return (
    <div className="flex flex-col gap-3">
      <Card className="rounded-lg py-0">
        <CardContent className="p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-semibold">
              OES Intensity Heatmap · step <span className="text-primary">{selectedStep}</span>
            </p>
            <p className="text-[10px] text-muted-foreground">
              클릭 → wavelength 선택 · x = wavelength · y = time(0→1)
            </p>
          </div>
          <div className="flex gap-4">
            <div className="shrink-0 flex flex-col justify-center gap-1">
              <p className="text-[9px] text-muted-foreground text-center rotate-180" style={{ writingMode: "vertical-rl" }}>time →</p>
            </div>
            <HeatmapGrid title="REF"       titleColor="#2563eb" phases={phases} wavelengths={wavelengths} getColor={refColor}
              selectedWl={selectedWl} onWlClick={setSelectedWl} />
            <HeatmapGrid title="COMP"      titleColor="#ea580c" phases={phases} wavelengths={wavelengths} getColor={compColor}
              selectedWl={selectedWl} onWlClick={setSelectedWl} />
            <HeatmapGrid title="OOB (C−R)" titleColor="#7c3aed" phases={phases} wavelengths={wavelengths} getColor={oobColor}
              selectedWl={selectedWl} onWlClick={setSelectedWl} />
          </div>
          <div className="mt-2 flex items-center gap-6 text-[9px] text-muted-foreground">
            <div className="flex items-center gap-1">
              <div className="h-2 w-16 rounded" style={{ background: "linear-gradient(to right, hsl(270,70%,15%), hsl(180,85%,35%), hsl(60,90%,55%))" }} />
              <span>low→high intensity</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-2 w-16 rounded" style={{ background: "linear-gradient(to right, hsl(240,80%,65%), hsl(0,0%,95%), hsl(0,85%,50%))" }} />
              <span>comp &lt; ref → comp &gt; ref</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {selectedWl != null && (
        <OesWavelengthLineChart
          trajectoryRows={trajectoryRows}
          selectedWl={selectedWl}
          onClose={() => setSelectedWl(null)}
        />
      )}
    </div>
  )
}

// ── OES step 개별 쿼리 + heatmap 래퍼 ──────────────────────────
function OesStepDetail({ category, selectedStep, refPmDates, onRemove }) {
  const stepCell    = { step: selectedStep }
  const detailQuery = usePmSpiderDetailResult(category, stepCell, refPmDates, stepCell)
  const trajectoryRows =
    detailQuery.data?.oes?.trajectoryRows ?? detailQuery.data?.oes?.detailRows ?? []

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {category?.label ?? ""} · OES · step {selectedStep}
        </span>
        <button
          type="button"
          onClick={() => onRemove(selectedStep)}
          className="rounded px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          ✕ 닫기
        </button>
      </div>
      <OesIntensityHeatmaps
        key={selectedStep}
        trajectoryRows={trajectoryRows}
        selectedStep={selectedStep}
        isLoading={detailQuery.isFetching && !detailQuery.data}
      />
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// Main export
// ──────────────────────────────────────────────────────────────
export function PmSpiderCategoryDashboard({
  categories,
  selectedCategoryId,
  onSelectedCategoryChange,
  isFetching,
}) {
  const refPmDates = null

  // selectedCategoryId: "ag" | "process" (or legacy "ag-trace" → "ag")
  const activeType = useMemo(() => {
    const raw = selectedCategoryId || "ag"
    if (raw === "ag" || raw === "process") return raw
    return raw.startsWith("process") ? "process" : "ag"
  }, [selectedCategoryId])

  const traceCategory = categories.find((c) => c.type === activeType && c.kind === "trace")
  const oesCategory   = categories.find((c) => c.type === activeType && c.kind === "oes")

  const [selectedTraceKeys, setSelectedTraceKeys] = useState([])
  const [selectedOesSteps,  setSelectedOesSteps]  = useState([])
  const [traceRankMode, setTraceRankMode] = useState("p3")
  const [oesRankMode,   setOesRankMode]   = useState("p3")
  const [traceSearch,   setTraceSearch]   = useState("")
  const [oesSearch,     setOesSearch]     = useState("")

  const handleTypeChange = (type) => {
    onSelectedCategoryChange?.(type)
    setSelectedTraceKeys([])
    setSelectedOesSteps([])
    setTraceSearch("")
    setOesSearch("")
  }

  const toggleTraceKey = (key) =>
    setSelectedTraceKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  const toggleOesStep = (step) =>
    setSelectedOesSteps((prev) =>
      prev.includes(step) ? prev.filter((s) => s !== step) : [...prev, step]
    )

  if (!categories.length) {
    return (
      <div className="flex min-h-96 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
        PM SPIDER category 데이터가 없습니다.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* ── 타입 탭: NPW / PW ── */}
      <div className="flex overflow-hidden rounded-lg border bg-card">
        {TYPE_TABS.map((tab) => {
          const trCat  = categories.find((c) => c.type === tab.id && c.kind === "trace")
          const oesCat = categories.find((c) => c.type === tab.id && c.kind === "oes")
          const isEmpty = !trCat?.rows?.length && !oesCat?.rows?.length
          const isActive = activeType === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleTypeChange(tab.id)}
              className={cn(
                "relative flex flex-1 items-center justify-center border-r px-4 py-2.5 text-sm font-medium last:border-r-0 transition-colors hover:bg-muted/40",
                isActive
                  ? "bg-background text-foreground after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary"
                  : "text-muted-foreground",
                isEmpty && "opacity-50",
              )}
            >
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* ── Trace | OES 랭킹 (좌/우 2열) ── */}
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 px-0.5">
            <Activity className="size-3 text-muted-foreground" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Trace</span>
          </div>
          <RankPanel
            panelType={traceRankMode}
            category={traceCategory}
            selectedKeys={selectedTraceKeys}
            onSelectRow={toggleTraceKey}
            onClearAll={() => setSelectedTraceKeys([])}
            onPanelTypeChange={setTraceRankMode}
            search={traceSearch}
            onSearchChange={setTraceSearch}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 px-0.5">
            <Waves className="size-3 text-muted-foreground" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">OES</span>
          </div>
          <RankPanel
            panelType={oesRankMode}
            category={oesCategory}
            selectedKeys={selectedOesSteps}
            onSelectRow={toggleOesStep}
            onClearAll={() => setSelectedOesSteps([])}
            onPanelTypeChange={setOesRankMode}
            search={oesSearch}
            onSearchChange={setOesSearch}
          />
        </div>
      </div>

      {/* ── Trace 상세 차트 ── */}
      {selectedTraceKeys.map((key) => (
        <TraceDetailWithLegend
          key={key}
          category={traceCategory}
          selectedKey={key}
          refPmDates={refPmDates}
        />
      ))}

      {/* ── OES 상세 차트 ── */}
      {selectedOesSteps.map((step) => (
        <OesStepDetail
          key={step}
          category={oesCategory}
          selectedStep={step}
          refPmDates={refPmDates}
          onRemove={toggleOesStep}
        />
      ))}

      {!selectedTraceKeys.length && !selectedOesSteps.length && (
        <div className="flex min-h-[160px] items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
          랭킹에서 항목을 선택하면 상세 차트가 표시됩니다
        </div>
      )}

      {isFetching && (
        <div className="pointer-events-none fixed bottom-4 right-4 rounded-md border bg-card px-3 py-2 text-xs text-muted-foreground shadow-sm">
          PM SPIDER 데이터 갱신 중...
        </div>
      )}
    </div>
  )
}
