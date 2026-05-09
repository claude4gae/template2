import { IconRefresh, IconSettings } from "@tabler/icons-react"

import { Button } from "@/components/ui/button"

export function LineSettingsHeader({ lineId, title, lastUpdatedLabel, isRefreshing, onRefresh }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-end gap-x-2 gap-y-1 text-lg font-semibold">
          <IconSettings className="size-5" />
          <span>{lineId ? `${lineId} Line ${title}` : title}</span>

          <div className="ml-0 md:ml-2 text-[10px] font-normal text-muted-foreground" aria-live="polite">
            Updated {lastUpdatedLabel}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 self-end">
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={!lineId || isRefreshing}
          className="gap-1"
          aria-label="Refresh"
          title="Refresh"
        >
          <IconRefresh className={`size-3 ${isRefreshing ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>
    </div>
  )
}
