import * as React from "react"

import { Slider } from "@/components/ui/slider"
import { QuickFilterFieldset } from "./QuickFilterFieldset"
import {
  normalizeRecentHoursRange,
  RECENT_HOURS_MAX,
} from "../../utils/dataTableQuickFilters"
import {
  formatHoursAgo,
  formatRecentHoursRange,
  rangeToSliderPositions,
  RECENT_SLIDER_MAX,
  RECENT_SLIDER_MIN,
  RECENT_SLIDER_STEP,
  sliderPositionsToRange,
} from "../../utils/recentHoursSlider"

export function RecentHoursQuickFilterSection({ section, legendId, current, onToggle }) {
  const [rangeValue, setRangeValue] = React.useState(() =>
    normalizeRecentHoursRange(current),
  )

  React.useEffect(() => {
    setRangeValue(normalizeRecentHoursRange(current))
  }, [current])

  const sliderPositions = rangeToSliderPositions(rangeValue)

  const handleSliderChange = (value) => {
    setRangeValue(normalizeRecentHoursRange(sliderPositionsToRange(value)))
  }

  const handleSliderCommit = (value) => {
    const nextRange = normalizeRecentHoursRange(sliderPositionsToRange(value))
    setRangeValue(nextRange)
    onToggle(section.key, nextRange, { forceValue: true })
  }

  return (
    <QuickFilterFieldset legendId={legendId} label={section.label}>
      <div className="flex w-60 flex-col rounded-lg px-3 py-1">
        <div className="flex mt-1 h-2 items-start gap-3">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {formatHoursAgo(RECENT_HOURS_MAX)}
          </span>

          <Slider
            className="flex-1"
            min={RECENT_SLIDER_MIN}
            max={RECENT_SLIDER_MAX}
            step={RECENT_SLIDER_STEP}
            value={sliderPositions}
            onValueChange={handleSliderChange}
            onValueCommit={handleSliderCommit}
            aria-label="최근 시간 범위 선택"
          />

          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            현재
          </span>
        </div>

        <p className=" text-center text-[9px] font-medium text-muted-foreground">
          {formatRecentHoursRange(rangeValue)}
        </p>
      </div>
    </QuickFilterFieldset>
  )
}
