import * as React from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import { LEGEND_PRESET_COLORS } from "../../utils/lineHistoryConfig"

export function LegendLabel({
  label,
  color,
  onSelectColor,
  onResetColor,
  hasOverride,
  disabled,
}) {
  const [open, setOpen] = React.useState(false)
  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild disabled={disabled}>
        <button
          type="button"
          onClick={(event) => event.stopPropagation()}
          className={cn(
            "inline-flex items-center gap-2 rounded-md px-2 py-1 ring-offset-background transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-1 ring-border",
          )}
          aria-label="레전드 색상 변경"
        >
          <span
            className="inline-flex h-3 w-3 rounded-full ring-1 ring-inset ring-border"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          <span className="whitespace-nowrap">{label}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-60"
        sideOffset={6}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="grid grid-cols-5 gap-2 p-2">
          {LEGEND_PRESET_COLORS.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                onSelectColor(preset)
                setOpen(false)
              }}
              className="h-8 rounded-md border ring-offset-background transition hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              style={{ backgroundColor: preset }}
              aria-label={`색상 ${preset}`}
            />
          ))}
        </div>
        {hasOverride && (
          <>
            <DropdownMenuSeparator />
            <button
              type="button"
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                onResetColor?.()
                setOpen(false)
              }}
              className="w-full px-3 py-2 text-left text-xs text-muted-foreground hover:bg-muted"
            >
              기본 색상으로 되돌리기
            </button>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function ColorLegend({ payload = [], seriesConfig, renderItem }) {
  if (!renderItem) return null
  return (
    <ul className="flex flex-wrap justify-end gap-3 text-[11px]">
      {payload.map((entry) => {
        const key = entry?.dataKey ?? entry?.value
        if (!key) return null
        const configEntry = seriesConfig?.[key]

        return (
          <li key={key}>
            {renderItem(
              key,
              configEntry && {
                ...configEntry,
                color: configEntry.color ?? entry?.color,
              },
            )}
          </li>
        )
      })}
    </ul>
  )
}
