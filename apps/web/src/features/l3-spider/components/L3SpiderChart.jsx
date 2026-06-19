import { useState } from "react"
import { BarChart3 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import TrellisChart from "./TrellisChart"

export function L3SpiderChart({
  rows,
  isLoading,
  error,
  groupBy,
  xAxisMode,
  onXAxisModeChange,
  scrollContainerRef,
  outerScrollTop,
  outerViewportHeight,
}) {
  const [lassoMode, setLassoMode] = useState('off')
  const [lassoShape, setLassoShape] = useState('box')
  const [eqcTimeTrellisMode, setEqcTimeTrellisMode] = useState('step')
  const [highlightFirst, setHighlightFirst] = useState(false)

  const trellisLabel = groupBy === 'bin' ? 'Bin' : 'EQPCH'

  return (
    <Card className="grid min-w-0 gap-0 overflow-hidden rounded-lg py-0">
      <CardHeader className="border-b bg-muted/50 px-4 py-2.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm">Scatter Plot — Trellis by</CardTitle>
            <Badge variant="secondary">{trellisLabel}</Badge>
            <Badge variant="outline">{rows.length} rows</Badge>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-muted-foreground">Chart Order</span>
              <div className="flex items-center gap-1 rounded-md border bg-muted/40 p-0.5">
                <Button
                  type="button"
                  variant={!highlightFirst ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => setHighlightFirst(false)}
                >
                  기본 순서
                </Button>
                <Button
                  type="button"
                  variant={highlightFirst ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => setHighlightFirst(true)}
                >
                  High Risk 먼저
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-muted-foreground">X Axis</span>
              <div className="flex items-center gap-1 rounded-md border bg-muted/40 p-0.5">
                <Button
                  type="button"
                  variant={xAxisMode === 'tkin_time' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => onXAxisModeChange('tkin_time')}
                >
                  Time
                </Button>
                <Button
                  type="button"
                  variant={xAxisMode === 'tkin_time_wafer_id' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => onXAxisModeChange('tkin_time_wafer_id')}
                >
                  Time·Wafer
                </Button>
                <Button
                  type="button"
                  variant={xAxisMode === 'eqc_tkin_time' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => onXAxisModeChange('eqc_tkin_time')}
                >
                  EQPCH·Time
                </Button>
              </div>
            </div>
            {xAxisMode === 'eqc_tkin_time' && (
              <div className="flex items-center gap-1 rounded-md border bg-muted/40 p-0.5">
                <Button
                  type="button"
                  variant={eqcTimeTrellisMode === 'step' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => setEqcTimeTrellisMode('step')}
                >
                  by Step
                </Button>
                <Button
                  type="button"
                  variant={eqcTimeTrellisMode === 'step_ppid' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-2.5 text-xs"
                  onClick={() => setEqcTimeTrellisMode('step_ppid')}
                >
                  by Step+PPID
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="flex h-full min-h-64 items-center justify-center text-sm text-muted-foreground">
            차트 데이터를 불러오는 중입니다.
          </div>
        ) : error ? (
          <div className="flex h-full min-h-64 items-center justify-center text-sm text-destructive">
            {error.message || "차트 데이터를 불러오지 못했습니다."}
          </div>
        ) : rows.length === 0 ? (
          <div className="flex h-full min-h-64 flex-col items-center justify-center gap-2 text-center text-sm text-muted-foreground">
            <BarChart3 className="size-6" aria-hidden="true" />
            <p>EQPCH 또는 Bin Name을 선택하면 차트가 표시됩니다.</p>
          </div>
        ) : (
          <TrellisChart
            data={rows}
            trellisBy={groupBy}
            xAxisMode={xAxisMode}
            highlightFirst={highlightFirst}
            lassoMode={lassoMode}
            lassoShape={lassoShape}
            eqcTimeTrellisMode={eqcTimeTrellisMode}
            onLassoModeChange={setLassoMode}
            onLassoShapeChange={setLassoShape}
            scrollContainerRef={scrollContainerRef}
            outerScrollTop={outerScrollTop}
            outerViewportHeight={outerViewportHeight}
          />
        )}
      </CardContent>
    </Card>
  )
}
