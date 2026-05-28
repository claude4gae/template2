import { useEffect, useMemo, useState } from "react"
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ChevronRight,
  Gauge,
  Layers3,
} from "lucide-react"
import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"

import {
  FDC_LINES,
  getSeverityLabel,
  getTeamsByLine,
  getTrendSteps,
} from "../utils/fdcTrendMockData"

const TREND_TYPE_LABELS = {
  "upper-shift": "상한 이동",
  variance: "분산 확대",
  cluster: "군집 이상",
  drift: "점진 Drift",
}

function formatTrendType(value) {
  return TREND_TYPE_LABELS[value] ?? value
}

function SummaryMetric({ icon: Icon, label, value, helper }) {
  return (
    <Card className="gap-3 rounded-lg py-4 shadow-none">
      <CardContent className="flex items-start gap-3 px-4">
        <span className="rounded-md border bg-background p-2 text-muted-foreground">
          <Icon className="size-4" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block text-xs text-muted-foreground">{label}</span>
          <span className="mt-1 block text-lg font-semibold tabular-nums">{value}</span>
          <span className="mt-0.5 block text-xs text-muted-foreground">{helper}</span>
        </span>
      </CardContent>
    </Card>
  )
}

function TrendStepButton({ step, selected, onSelect }) {
  const severityLabel = getSeverityLabel(step.severity)

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "grid w-full gap-3 rounded-lg border bg-card p-4 text-left transition hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        selected && "border-primary bg-accent text-accent-foreground",
      )}
    >
      <span className="flex min-w-0 items-start justify-between gap-3">
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold">{step.stepName}</span>
          <span className="mt-1 block text-xs text-muted-foreground">
            {step.stepCode} · {step.toolGroup}
          </span>
        </span>
        <Badge variant={severityLabel === "High" ? "destructive" : "secondary"}>
          {severityLabel}
        </Badge>
      </span>
      <span className="grid grid-cols-3 gap-2 text-xs">
        <span>
          <span className="block text-muted-foreground">Score</span>
          <span className="font-semibold tabular-nums">{step.severity}</span>
        </span>
        <span>
          <span className="block text-muted-foreground">Abnormal</span>
          <span className="font-semibold tabular-nums">{step.abnormalCount}</span>
        </span>
        <span>
          <span className="block text-muted-foreground">Lots</span>
          <span className="font-semibold tabular-nums">{step.lotCount}</span>
        </span>
      </span>
      <span className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
        <span>{formatTrendType(step.trendType)}</span>
        <span className="inline-flex items-center gap-1">
          상세 보기
          <ChevronRight className="size-3" aria-hidden="true" />
        </span>
      </span>
    </button>
  )
}

function ScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const row = payload[0]?.payload
  if (!row) return null

  return (
    <ChartTooltipContent
      active={active}
      payload={[
        { dataKey: "wafer", name: "Wafer", value: row.wafer },
        { dataKey: "lot", name: "Lot", value: row.lot },
        { dataKey: "time", name: "Time", value: row.time },
        { dataKey: "value", name: "Value", value: row.value },
      ]}
      hideLabel
    />
  )
}

function FdcScatterChart({ selectedStep }) {
  if (!selectedStep) {
    return (
      <div className="flex h-full min-h-72 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
        스텝을 선택하면 scatter chart가 표시됩니다.
      </div>
    )
  }

  return (
    <Card className="grid h-full min-h-0 grid-rows-[auto,1fr] gap-0 overflow-hidden rounded-lg py-0 shadow-none">
      <CardHeader className="border-b bg-muted/40 px-4 py-3">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <CardTitle className="truncate text-base">{selectedStep.stepName}</CardTitle>
              <Badge variant="outline">{selectedStep.toolGroup}</Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {selectedStep.stepCode} · {formatTrendType(selectedStep.trendType)} · Last {selectedStep.latestAt}
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="secondary">{selectedStep.points.length} wafers</Badge>
            <Badge variant={getSeverityLabel(selectedStep.severity) === "High" ? "destructive" : "outline"}>
              Score {selectedStep.severity}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="min-h-0 p-4">
        <ChartContainer
          className="h-full min-h-80"
          config={{
            value: { label: "FDC Value", color: "var(--chart-1)" },
            limit: { label: "Limit", color: "var(--destructive)" },
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 16, right: 20, bottom: 20, left: 8 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis
                type="category"
                dataKey="wafer"
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                interval={2}
              />
              <YAxis
                type="number"
                dataKey="value"
                domain={["dataMin - 4", "dataMax + 4"]}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                width={44}
              />
              <ReferenceLine
                y={selectedStep.points[0]?.limit}
                stroke="var(--destructive)"
                strokeDasharray="4 4"
                label={{ value: "Limit", fill: "var(--destructive)", fontSize: 11 }}
              />
              <ChartTooltip cursor={{ strokeDasharray: "3 3" }} content={<ScatterTooltip />} />
              <Scatter
                name="FDC Value"
                data={selectedStep.points}
                dataKey="value"
                fill="var(--chart-1)"
                shape={(props) => {
                  const { cx, cy, payload } = props
                  const abnormal = payload?.status === "abnormal"
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={abnormal ? 5 : 4}
                      fill={abnormal ? "var(--destructive)" : "var(--chart-1)"}
                      stroke={abnormal ? "var(--destructive)" : "var(--background)"}
                      strokeWidth={1.5}
                    />
                  )
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

export function FdcTrendPage() {
  const [selectedLine, setSelectedLine] = useState(FDC_LINES[0])
  const teams = useMemo(() => getTeamsByLine(selectedLine), [selectedLine])
  const [selectedTeam, setSelectedTeam] = useState(teams[0] ?? "")
  const trendSteps = useMemo(
    () => getTrendSteps({ lineId: selectedLine, teamId: selectedTeam }),
    [selectedLine, selectedTeam],
  )
  const [selectedStepId, setSelectedStepId] = useState("")

  useEffect(() => {
    setSelectedTeam(teams[0] ?? "")
  }, [teams])

  useEffect(() => {
    setSelectedStepId(trendSteps[0]?.id ?? "")
  }, [trendSteps])

  const selectedStep = trendSteps.find((step) => step.id === selectedStepId) ?? trendSteps[0]
  const highCount = trendSteps.filter((step) => getSeverityLabel(step.severity) === "High").length
  const abnormalTotal = trendSteps.reduce((sum, step) => sum + step.abnormalCount, 0)
  const avgScore = trendSteps.length
    ? Math.round(trendSteps.reduce((sum, step) => sum + step.severity, 0) / trendSteps.length)
    : 0

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col overflow-hidden">
      <header className="shrink-0 border-b bg-card px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">이상 FDC Trend</h1>
              <Badge variant="outline">Screening</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              라인과 분임조를 선택해 선별된 이상 Trend를 스텝 기준으로 확인합니다.
            </p>
          </div>
          <Button type="button" variant="outline" size="sm">
            <BarChart3 className="size-4" aria-hidden="true" />
            Trend 기준 보기
          </Button>
        </div>
      </header>

      <section className="grid shrink-0 gap-3 border-b bg-background px-6 py-4">
        <Tabs value={selectedLine} onValueChange={setSelectedLine}>
          <TabsList className="h-auto w-full flex-wrap justify-start gap-1 bg-muted/70">
            {FDC_LINES.map((lineId) => (
              <TabsTrigger key={lineId} value={lineId} className="h-8 flex-none px-3">
                {lineId}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Tabs value={selectedTeam} onValueChange={setSelectedTeam}>
          <TabsList className="h-auto w-full flex-wrap justify-start gap-1 bg-muted/70">
            {teams.map((teamId) => (
              <TabsTrigger key={teamId} value={teamId} className="h-8 flex-none px-3">
                {teamId}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </section>

      <section className="grid shrink-0 grid-cols-4 gap-3 px-6 py-4">
        <SummaryMetric icon={Layers3} label="Selected line" value={selectedLine} helper={selectedTeam} />
        <SummaryMetric icon={Activity} label="Trend steps" value={trendSteps.length} helper="스텝 단위 선별" />
        <SummaryMetric icon={AlertTriangle} label="High severity" value={highCount} helper="즉시 확인 대상" />
        <SummaryMetric icon={Gauge} label="Avg. score" value={avgScore} helper={`${abnormalTotal} abnormal points`} />
      </section>

      <main className="grid flex-1 min-h-0 min-w-0 grid-cols-[380px,1fr] gap-4 overflow-hidden px-6 pb-6">
        <section className="grid min-h-0 min-w-0 grid-rows-[auto,1fr] gap-3">
          <div className="shrink-0">
            <h2 className="text-base font-semibold">스텝별 이상 Trend</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              위험도가 높은 순서로 정렬됩니다.
            </p>
          </div>
          <div className="min-h-0 overflow-y-auto pr-1">
            {trendSteps.length === 0 ? (
              <div className="flex min-h-52 items-center justify-center rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                선택한 분임조에 표시할 이상 Trend가 없습니다.
              </div>
            ) : (
              <div className="grid gap-3">
                {trendSteps.map((step) => (
                  <TrendStepButton
                    key={step.id}
                    step={step}
                    selected={step.id === selectedStep?.id}
                    onSelect={() => setSelectedStepId(step.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="min-h-0 min-w-0">
          <FdcScatterChart selectedStep={selectedStep} />
        </section>
      </main>
    </div>
  )
}
