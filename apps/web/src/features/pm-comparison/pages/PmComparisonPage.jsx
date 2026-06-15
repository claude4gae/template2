import { useState } from "react"
import { AlertTriangle, Database, RefreshCw } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

import { PmComparisonFilterBar } from "../components/PmComparisonFilterBar"
import { PmSpiderCategoryDashboard } from "../components/PmSpiderCategoryDashboard"
import { usePmComparisonMeta, usePmSpiderCategoryResults } from "../hooks/usePmComparisonQueries"
import { DEFAULT_PM_FORM, buildPmComparisonPayload } from "../utils/format"

function ErrorBanner({ error }) {
  if (!error) return null
  return (
    <div className="mx-6 mt-3 flex shrink-0 items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      <AlertTriangle className="size-4" aria-hidden="true" />
      <span>{error.message || "PM SPIDER 데이터를 불러오지 못했습니다."}</span>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-0 items-center justify-center p-6">
      <div className="grid justify-items-center gap-3 rounded-lg border border-dashed bg-card px-8 py-10 text-center text-sm text-muted-foreground">
        <Database className="size-7" aria-hidden="true" />
        <div>
          <p className="font-medium text-foreground">PM SPIDER 조건을 입력하세요.</p>
          <p className="mt-1">Line ID, EQP ID, PM 기준 시점을 넣으면 NPW/PW trace/OES 랭킹을 조회합니다.</p>
        </div>
      </div>
    </div>
  )
}

export function PmComparisonPage() {
  const [form, setForm] = useState(DEFAULT_PM_FORM)
  const [payload, setPayload] = useState(() => buildPmComparisonPayload(DEFAULT_PM_FORM))
  const [selectedCategoryId, setSelectedCategoryId] = useState("ag")
  const metaQuery = usePmComparisonMeta()
  const categoryResults = usePmSpiderCategoryResults(payload, null)

  const submit = () => {
    setPayload(buildPmComparisonPayload(form))
  }

  return (
    <div className="flex min-h-full flex-col bg-muted/30">
      <header className="shrink-0 border-b bg-card px-4 py-3 md:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight">PM SPIDER</h1>
              <Badge variant="outline">NPW / PW · P2 / P3</Badge>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              NPW(ag)/PW(process) × Trace/OES 기준 P2(per-wafer) / P3(집단비교) 이상 파라미터 랭킹.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              metaQuery.refetch()
              if (payload) {
                categoryResults.refetch()
              }
            }}
            disabled={metaQuery.isFetching || categoryResults.isFetching}
          >
            <RefreshCw className="size-4" />
            전체 새로고침
          </Button>
        </div>
      </header>

      <PmComparisonFilterBar
        form={form}
        meta={metaQuery.data}
        isMetaLoading={metaQuery.isFetching}
        isResultFetching={categoryResults.isFetching}
        onFormChange={setForm}
        onSubmit={submit}
      />

      <ErrorBanner error={metaQuery.error || categoryResults.error} />

      <main className="flex-1 px-4 py-4 md:px-6">
        {!payload ? (
          <EmptyState />
        ) : categoryResults.isLoading ? (
          <div className="flex h-full min-h-0 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
            PM SPIDER category 데이터를 계산하는 중입니다.
          </div>
        ) : (
          <PmSpiderCategoryDashboard
            categories={categoryResults.categories}
            selectedCategoryId={selectedCategoryId}
            onSelectedCategoryChange={setSelectedCategoryId}
            isFetching={categoryResults.isFetching}
          />
        )}
      </main>
    </div>
  )
}
