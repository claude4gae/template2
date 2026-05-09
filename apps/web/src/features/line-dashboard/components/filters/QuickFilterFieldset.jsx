import { cn } from "@/lib/utils"

const FIELDSET_CLASS = "flex flex-col rounded-xl px-2"

export function QuickFilterFieldset({
  legendId,
  label,
  children,
  className,
  legendClassName,
  isLegendHidden = false,
}) {
  return (
    <fieldset
      className={cn(FIELDSET_CLASS, className)}
      aria-labelledby={legendId}
    >
      <legend
        id={legendId}
        className={cn(
          isLegendHidden
            ? "sr-only"
            : "text-[9px] font-semibold uppercase tracking-wide text-muted-foreground",
          legendClassName,
        )}
      >
        {label}
      </legend>
      {children}
    </fieldset>
  )
}
