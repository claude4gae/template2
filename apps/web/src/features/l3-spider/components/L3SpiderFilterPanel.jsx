import { useMemo, useState } from "react"
import { ChevronRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

import { sortedValues } from "../utils/selection"

function SelectRow({ label, hint, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-9 w-full min-w-0 items-center justify-between gap-3 rounded-md border border-transparent px-3 text-left transition",
        "hover:border-border hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        selected && "border-primary/30 bg-primary/10 text-primary shadow-sm",
      )}
    >
      <span
        className={cn(
          "min-w-0 flex-1 truncate text-[13px] font-medium leading-5 text-foreground",
          selected && "text-primary",
        )}
      >
        {label}
      </span>
      {hint != null && (
        <span className="shrink-0 text-[11px] text-muted-foreground">
          {hint}
        </span>
      )}
      <ChevronRight className="size-3 shrink-0 text-muted-foreground" aria-hidden="true" />
    </button>
  )
}

function ColumnCard({ title, badge, disabled, placeholder, isActive, children }) {
  const [query, setQuery] = useState("")

  return (
    <Card
      className={cn(
        "grid min-h-0 grid-rows-[48px_40px_minmax(0,1fr)] gap-0 overflow-hidden rounded-xl border bg-card py-0 shadow-sm transition-all",
        isActive && "ring-2 ring-primary/50",
      )}
    >
      <div
        className={cn(
          "flex h-12 items-center border-b px-4",
          isActive ? "bg-primary/10" : "bg-muted/40",
        )}
      >
        <div className="flex h-full min-w-0 flex-1 items-center justify-between gap-2">
          <CardTitle
            className={cn(
              "truncate text-sm font-semibold leading-5",
              disabled && "text-muted-foreground",
              isActive && "text-primary",
            )}
          >
            {title}
          </CardTitle>
          {badge != null ? (
            <Badge variant={isActive ? "default" : "secondary"} className="shrink-0 text-[11px]">
              {badge}
            </Badge>
          ) : null}
        </div>
      </div>
      <div className="border-b px-2 py-1.5">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="검색…"
          className="h-7 text-xs"
          disabled={disabled}
        />
      </div>
      <CardContent className="min-h-0 overflow-y-auto bg-background/60 p-2">
        {disabled ? (
          <div className="flex h-full min-h-16 items-center justify-center text-center text-sm text-muted-foreground">
            {placeholder}
          </div>
        ) : (
          <div className="grid content-start gap-1.5">
            {children(query)}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function applyQuery(items, query) {
  const q = query.trim().toLowerCase()
  return q ? items.filter((item) => item.toLowerCase().includes(q)) : items
}

export function L3SpiderFilterPanel({
  edsStepSeqs,
  edsStepPpids,
  ppidHighRiskEqcs,
  eqcAnomalyBins,
  eqcHighRiskBins,
  checkedEdsStep,  // string | null
  checkedStep,     // string | null
  checkedPpid,     // string | null
  checkedEqc,      // string | null — EQPCH 모드 (단일)
  checkedBin,      // string | null — Bin 모드 (단일)
  onCheckedEdsStepChange,
  onCheckedStepChange,
  onCheckedPpidChange,
  onCheckedEqcChange,
  onCheckedBinChange,
  onAnalysisModeChange,
}) {
  const edsSteps = useMemo(() => sortedValues(Object.keys(edsStepSeqs || {})), [edsStepSeqs])

  const visibleSteps = useMemo(
    () => checkedEdsStep ? sortedValues(edsStepSeqs?.[checkedEdsStep] ?? []) : [],
    [checkedEdsStep, edsStepSeqs],
  )

  const visiblePpids = useMemo(
    () => (checkedEdsStep && checkedStep)
      ? sortedValues(edsStepPpids?.[`${checkedEdsStep}|||${checkedStep}`] ?? [])
      : [],
    [checkedEdsStep, checkedStep, edsStepPpids],
  )

  const visibleEqcs = useMemo(
    () => checkedPpid ? sortedValues(ppidHighRiskEqcs?.[checkedPpid] ?? []) : [],
    [checkedPpid, ppidHighRiskEqcs],
  )

  // EQPCH 선택 시 이상 감지된 bin_name만 표시
  const visibleBins = useMemo(
    () => checkedEqc ? sortedValues(eqcAnomalyBins?.[checkedEqc] ?? []) : [],
    [checkedEqc, eqcAnomalyBins],
  )

  // 상위 해제 시 하위 전부 리셋
  const selectEdsStep = (eds) => {
    const next = checkedEdsStep === eds ? null : eds
    onCheckedEdsStepChange(next)
    onCheckedStepChange(null)
    onCheckedPpidChange(null)
    onCheckedEqcChange(null)
    onCheckedBinChange(null)
  }

  const selectStep = (step) => {
    const next = checkedStep === step ? null : step
    onCheckedStepChange(next)
    onCheckedPpidChange(null)
    onCheckedEqcChange(null)
    onCheckedBinChange(null)
  }

  const selectPpid = (ppid) => {
    const next = checkedPpid === ppid ? null : ppid
    onCheckedPpidChange(next)
    onCheckedEqcChange(null)
    onCheckedBinChange(null)
  }

  // EQPCH 선택 → 모드 'eqpch', Bin 클리어
  const selectEqc = (eqc) => {
    const next = checkedEqc === eqc ? null : eqc
    onCheckedEqcChange(next)
    onCheckedBinChange(null)
    if (next !== null) onAnalysisModeChange("eqpch")
  }

  // Bin 선택 → 해당 bin의 전체 EQPCH trellis (모드 전환, EQPCH는 유지)
  const selectBin = (bin) => {
    const next = checkedBin === bin ? null : bin
    onCheckedBinChange(next)
    onAnalysisModeChange(next !== null ? 'bin' : 'eqpch')
  }

  return (
    <section className="grid h-[320px] grid-cols-5 gap-4">
      <ColumnCard
        title="EDS Step"
        badge={`${edsSteps.length}`}
        disabled={edsSteps.length === 0}
        placeholder="항목 없음"
        isActive={checkedEdsStep !== null}
      >
        {(query) =>
          applyQuery(edsSteps, query).map((eds) => (
            <SelectRow
              key={eds}
              label={eds}
              selected={checkedEdsStep === eds}
              onClick={() => selectEdsStep(eds)}
            />
          ))
        }
      </ColumnCard>

      <ColumnCard
        title="Step Seq"
        badge={visibleSteps.length > 0 ? `${visibleSteps.length}` : null}
        disabled={!checkedEdsStep}
        placeholder="EDS Step을 먼저 선택하세요"
        isActive={checkedStep !== null}
      >
        {(query) =>
          applyQuery(visibleSteps, query).map((step) => (
            <SelectRow
              key={step}
              label={step}
              selected={checkedStep === step}
              onClick={() => selectStep(step)}
            />
          ))
        }
      </ColumnCard>

      <ColumnCard
        title="PPID"
        badge={visiblePpids.length > 0 ? `${visiblePpids.length}` : null}
        disabled={!checkedStep}
        placeholder="Step Seq를 먼저 선택하세요"
        isActive={checkedPpid !== null}
      >
        {(query) =>
          applyQuery(visiblePpids, query).map((ppid) => (
            <SelectRow
              key={ppid}
              label={ppid}
              selected={checkedPpid === ppid}
              onClick={() => selectPpid(ppid)}
            />
          ))
        }
      </ColumnCard>

      {/* EQPCH: 단일 선택 → bin_name trellis */}
      <ColumnCard
        title="EQPCH"
        badge={visibleEqcs.length > 0 ? `${visibleEqcs.length}` : null}
        disabled={!checkedPpid}
        placeholder="PPID를 먼저 선택하세요"
        isActive={checkedEqc !== null}
      >
        {(query) =>
          applyQuery(visibleEqcs, query).map((eqc) => {
            const highRiskBinCount = eqcHighRiskBins?.[eqc]?.length ?? 0
            return (
              <SelectRow
                key={eqc}
                label={eqc}
                hint={highRiskBinCount > 0 ? String(highRiskBinCount) : null}
                selected={checkedEqc === eqc}
                onClick={() => selectEqc(eqc)}
              />
            )
          })
        }
      </ColumnCard>

      {/* Bin Name: EQPCH 선택 후 활성화되는 세부 필터 */}
      <ColumnCard
        title="Bin Name"
        badge={visibleBins.length > 0 ? `${visibleBins.length}` : null}
        disabled={!checkedEqc}
        placeholder="EQPCH를 먼저 선택하세요"
        isActive={checkedBin !== null}
      >
        {(query) =>
          applyQuery(visibleBins, query).map((bin) => (
            <SelectRow
              key={bin}
              label={bin}
              selected={checkedBin === bin}
              onClick={() => selectBin(bin)}
            />
          ))
        }
      </ColumnCard>
    </section>
  )
}
