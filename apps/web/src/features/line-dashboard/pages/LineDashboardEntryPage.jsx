// 파일 경로: src/features/line-dashboard/pages/LineDashboardEntryPage.jsx
import { useEffect, useMemo } from "react"
import { AlertCircle, Loader2 } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"

import { Button } from "components/ui/button"
import { useAuth } from "@/lib/auth"
import { useLineOptionsQuery } from "../hooks/useLineOptionsQuery"

function getFirstLineId(lineOptions) {
  if (!Array.isArray(lineOptions)) return null
  const candidate = lineOptions.find((lineId) => typeof lineId === "string" && lineId.trim().length > 0)
  return candidate ?? null
}

export function LineDashboardEntryPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data: lineOptions = [], isLoading, isError, error, refetch } = useLineOptionsQuery({
    preferredUserSdwtProd:
      typeof user?.user_sdwt_prod === "string" ? user.user_sdwt_prod.trim() : "",
  })

  const firstLineId = useMemo(() => getFirstLineId(lineOptions), [lineOptions])

  useEffect(() => {
    if (firstLineId) {
      navigate(`/ESOP_Dashboard/${firstLineId}`, { replace: true })
    }
  }, [firstLineId, navigate])

  if (firstLineId) {
    return (
      <section className="grid gap-4">
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Opening line dashboard</p>
              <p className="text-xs text-muted-foreground">Redirecting to {firstLineId}...</p>
            </div>
          </div>
        </div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <section className="grid gap-4">
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading available lines...</p>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="grid gap-4">
      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-1 h-5 w-5 text-destructive" />
          <div className="space-y-3">
            <div className="space-y-1">
              <h1 className="text-lg font-semibold">Line dashboard is unavailable</h1>
              <p className="text-sm text-muted-foreground">
                {isError && error?.message
                  ? error.message
                  : "No production lines were found. Add a line or check your permissions, then try again."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => refetch()} size="sm">
                Retry
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link to="/">Back to home</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
