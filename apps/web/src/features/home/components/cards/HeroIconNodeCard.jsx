import { forwardRef } from "react"

import { cn } from "@/lib/utils"

export const HeroIconNodeCard = forwardRef(function HeroIconNodeCard(
  { icon: Icon, className, iconClassName },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        "bg-background relative z-10 flex items-center justify-center rounded-xl border-[1.5px] shadow-md",
        className,
      )}
    >
      <Icon className={cn("stroke-1", iconClassName)} />
    </div>
  )
})
