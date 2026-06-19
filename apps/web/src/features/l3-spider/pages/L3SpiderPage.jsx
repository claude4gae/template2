import { useEffect, useMemo, useState } from "react"
import { Database, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"

import { L3SpiderChart } from "../components/L3SpiderChart"
import { L3SpiderDataSelector } from "../components/L3SpiderDataSelector"
import { L3SpiderFilterPanel } from "../components/L3SpiderFilterPanel"
import { L3SpiderSummaryCards } from "../components/L3SpiderSummaryCards"
import {
  useL3SpiderData,
  useL3SpiderMeta,
  useL3SpiderSummary,
} from "../hooks/useL3SpiderQueries"
import {
  EMPTY_META,
  EMPTY_SELECTION,
  EMPTY_SUMMARY,
  hasCompleteSelection,
} from "../utils/selection"

export function L3SpiderPage() {
  const [selection, setSelection] = useState(EMPTY_SELECTION)
  // 모든 선택: 단일값 (string | null)
  const [checkedEdsStep, setCheckedEdsStep] = useState(null)
  const [checkedStep, setCheckedStep] = useState(null)
  const [checkedPpid, setCheckedPpid] = useState(null)
  const [checkedEqc, setCheckedEqc] = useState(null)   // EQPCH 모드
  const [checkedBin, setCheckedBin] = useState(null)   // Bin 모드
  // 분석 모드: EQPCH 선택 → 'eqpch' / Bin 선택 → 'bin'
  const [analysisMode, setAnalysisMode] = useState("eqpch")
  const [xAxisMode, setXAxisMode] = useState("tkin_time")


  const metaQuery = useL3SpiderMeta()
  const summaryQuery = useL3SpiderSummary(selection)

  const meta = metaQuery.data ?? EMPTY_META
  const summary = summaryQuery.data ?? EMPTY_SUMMARY
  const isSelectionReady = hasCompleteSelection(selection)

  const resetLeafSelections = () => {
    setCheckedEdsStep(null)
    setCheckedStep(null)
    setCheckedPpid(null)
    setCheckedEqc(null)
    setCheckedBin(null)
  }

  useEffect(() => { resetLeafSelections() }, [selection])
  useEffect(() => {
    if (!summaryQuery.isSuccess) return
    resetLeafSelections()
  }, [summary, summaryQuery.isSuccess])

  // trellis 기준: EQPCH 선택 → bin별 subplots / Bin 선택 → eqc별 subplots
  const groupBy = analysisMode === "eqpch" ? "bin" : "eqc"

  // Mode 1(EQPCH선택): 해당 EQPCH의 이상 bins만 필터
  // Mode 2(Bin선택): EQPCH 필터 해제 → 모든 EQPCH trellis
  const resolvedEqcs = useMemo(
    () => checkedBin ? [] : (checkedEqc ? [checkedEqc] : []),
    [checkedBin, checkedEqc],
  )
  const resolvedBins = useMemo(
    () => checkedBin
      ? [checkedBin]
      : (checkedEqc ? (summary.eqcAnomalyBins?.[checkedEqc] ?? []) : []),
    [checkedBin, checkedEqc, summary.eqcAnomalyBins],
  )

  const dataQuery = useL3SpiderData(
    selection, checkedEdsStep, checkedStep, checkedPpid, checkedEqc, checkedBin,
    resolvedEqcs, resolvedBins,
  )
  const rows = dataQuery.data?.rows ?? []

  return (
    <div className="relative flex h-full min-h-0 min-w-0 flex-col overflow-y-auto">
      <header className="shrink-0 border-b bg-card px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight">L3 Spider</h1>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              metaQuery.refetch()
              summaryQuery.refetch()
              dataQuery.refetch()
            }}
          >
            <RefreshCw className="size-4" />
            전체 새로고침
          </Button>
        </div>
      </header>

      <L3SpiderDataSelector
        meta={meta}
        selection={selection}
        onSelectionChange={setSelection}
        isLoading={metaQuery.isFetching}
        onRefresh={() => metaQuery.refetch()}
      />

      {metaQuery.error ? (
        <div className="mx-6 mt-4 shrink-0 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {metaQuery.error.message || "L3 Spider 메타데이터를 불러오지 못했습니다."}
        </div>
      ) : null}

      {isSelectionReady ? <L3SpiderSummaryCards stats={summary.stats} /> : null}

      {!isSelectionReady ? (
        <div className="m-6 flex flex-1 items-center justify-center rounded-xl border bg-card p-8 text-center text-sm text-muted-foreground shadow-sm">
          <div className="grid justify-items-center gap-2">
            <Database className="size-6" aria-hidden="true" />
            날짜, Line, Process, EDS Step을 선택하면 요약과 차트를 조회합니다.
          </div>
        </div>
      ) : (
        <main className="grid gap-5 px-6 pb-6 pt-4">
          <L3SpiderFilterPanel
            edsStepSeqs={summary.edsStepSeqs ?? {}}
            edsStepPpids={summary.edsStepPpids ?? {}}
            ppidEqcs={summary.ppidEqcs ?? {}}
            ppidBins={summary.ppidBins ?? {}}
            eqcBins={summary.eqcBins ?? {}}
            eqcAnomalyBins={summary.eqcAnomalyBins ?? {}}
            checkedEdsStep={checkedEdsStep}
            checkedStep={checkedStep}
            checkedPpid={checkedPpid}
            checkedEqc={checkedEqc}
            checkedBin={checkedBin}
            analysisMode={analysisMode}
            onCheckedEdsStepChange={setCheckedEdsStep}
            onCheckedStepChange={setCheckedStep}
            onCheckedPpidChange={setCheckedPpid}
            onCheckedEqcChange={setCheckedEqc}
            onCheckedBinChange={setCheckedBin}
            onAnalysisModeChange={setAnalysisMode}
          />
          <L3SpiderChart
            rows={rows}
            isLoading={summaryQuery.isFetching || dataQuery.isFetching}
            error={summaryQuery.error || dataQuery.error}
            groupBy={groupBy}
            xAxisMode={xAxisMode}
            onXAxisModeChange={setXAxisMode}
          />
        </main>
      )}
    </div>
  )
}
