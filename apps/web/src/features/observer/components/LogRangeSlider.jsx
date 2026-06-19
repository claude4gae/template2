import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CalendarDaysIcon } from "@heroicons/react/24/outline";
import { Slider } from "@/components/ui/slider";
import {
  DEFAULT_LOG_RANGE_DAYS,
  LOG_RANGE_SLIDER_STEP,
  MAX_LOG_RANGE_DAYS,
  MIN_LOG_RANGE_DAYS,
} from "../utils/constants";
import {
  formatLogRangeLabel,
  formatLogRangeWindow,
  normalizeLogRange,
} from "../utils/logDateRange";

const RANGE_VALUE_SPAN = MAX_LOG_RANGE_DAYS - MIN_LOG_RANGE_DAYS;
const ENDPOINT_DRAG_BUFFER_PX = 10;

function getVisualPercent(daysAgo) {
  return ((MAX_LOG_RANGE_DAYS - daysAgo) / RANGE_VALUE_SPAN) * 100;
}

function moveRangeByDays(range, deltaDays) {
  const rangeWidth = range.startDaysAgo - range.endDaysAgo;
  const minEndDaysAgo = MIN_LOG_RANGE_DAYS;
  const maxEndDaysAgo = MAX_LOG_RANGE_DAYS - rangeWidth;
  const nextEndDaysAgo = Math.min(
    Math.max(range.endDaysAgo + deltaDays, minEndDaysAgo),
    maxEndDaysAgo
  );

  return {
    startDaysAgo: nextEndDaysAgo + rangeWidth,
    endDaysAgo: nextEndDaysAgo,
  };
}

export default function LogRangeSlider({
  value = DEFAULT_LOG_RANGE_DAYS,
  onChange,
}) {
  const sliderAreaRef = useRef(null);
  const rangeDragRef = useRef(null);
  const dragMoveHandlerRef = useRef(null);
  const dragUpHandlerRef = useRef(null);
  const normalizedValue = useMemo(() => normalizeLogRange(value), [value]);
  const [draftValue, setDraftValue] = useState(normalizedValue);

  useEffect(() => {
    setDraftValue(normalizedValue);
  }, [normalizedValue]);

  const sliderValue = useMemo(
    () => [draftValue.endDaysAgo, draftValue.startDaysAgo],
    [draftValue.endDaysAgo, draftValue.startDaysAgo]
  );
  const rangeLabel = formatLogRangeLabel(draftValue);
  const rangeWindow = formatLogRangeWindow(draftValue);

  const sliderValueToRange = (nextValue) =>
    normalizeLogRange({
      endDaysAgo: nextValue[0],
      startDaysAgo: nextValue[1],
    });

  const handleValueChange = (nextValue) => {
    setDraftValue(sliderValueToRange(nextValue));
  };

  const handleValueCommit = (nextValue) => {
    const nextRange = sliderValueToRange(nextValue);
    setDraftValue(nextRange);
    onChange?.(nextRange);
  };

  const cleanupRangeDrag = useCallback(() => {
    if (dragMoveHandlerRef.current) {
      window.removeEventListener("pointermove", dragMoveHandlerRef.current);
    }
    if (dragUpHandlerRef.current) {
      window.removeEventListener("pointerup", dragUpHandlerRef.current);
    }
    dragMoveHandlerRef.current = null;
    dragUpHandlerRef.current = null;
    rangeDragRef.current = null;
  }, []);

  const handleRangePointerDown = (event) => {
    if (event.button !== 0 || !sliderAreaRef.current) return;

    const rect = sliderAreaRef.current.getBoundingClientRect();
    const pointerX = event.clientX - rect.left;
    const leftX = (getVisualPercent(draftValue.startDaysAgo) / 100) * rect.width;
    const rightX = (getVisualPercent(draftValue.endDaysAgo) / 100) * rect.width;
    const isInsideRange = pointerX > leftX && pointerX < rightX;
    const isNearEndpoint =
      pointerX - leftX < ENDPOINT_DRAG_BUFFER_PX ||
      rightX - pointerX < ENDPOINT_DRAG_BUFFER_PX;

    if (!isInsideRange || isNearEndpoint) return;

    event.preventDefault();
    event.stopPropagation();
    rangeDragRef.current = {
      startX: event.clientX,
      startRange: draftValue,
      currentRange: draftValue,
      trackWidth: rect.width,
    };

    const handleRangePointerMove = (moveEvent) => {
      const dragState = rangeDragRef.current;
      if (!dragState) return;

      moveEvent.preventDefault();
      const deltaX = moveEvent.clientX - dragState.startX;
      const deltaDays = -Math.round(
        (deltaX / dragState.trackWidth) * RANGE_VALUE_SPAN
      );
      const nextRange = moveRangeByDays(dragState.startRange, deltaDays);
      dragState.currentRange = nextRange;
      setDraftValue(nextRange);
    };

    const handleRangePointerUp = () => {
      const dragState = rangeDragRef.current;
      if (dragState?.currentRange) {
        onChange?.(dragState.currentRange);
      }
      cleanupRangeDrag();
    };

    dragMoveHandlerRef.current = handleRangePointerMove;
    dragUpHandlerRef.current = handleRangePointerUp;
    window.addEventListener("pointermove", handleRangePointerMove);
    window.addEventListener("pointerup", handleRangePointerUp);
  };

  useEffect(() => cleanupRangeDrag, [cleanupRangeDrag]);

  return (
    <div className="flex h-9 min-w-[252px] max-w-[520px] flex-1 items-center gap-2 rounded-md border-border bg-card px-2">
      <CalendarDaysIcon className="h-8 w-8 shrink-0 self-end text-muted-foreground" />
      <span className="mt-5 shrink-0 text-[11px] text-muted-foreground">
        - 90 days
      </span>
      <div
        ref={sliderAreaRef}
        className="relative min-w-[105px] flex-1 cursor-grab pt-5 active:cursor-grabbing"
        onPointerDownCapture={handleRangePointerDown}
      >
        <span className="absolute left-1/2 top-0 -translate-x-1/2 whitespace-nowrap text-[11px] font-medium text-muted-foreground">
          {rangeLabel} ({rangeWindow})
        </span>
        <Slider
          className="[&>span:first-child]:h-2 [&_[role=slider]]:size-3 [&_[role=slider]]:shadow-sm"
          min={MIN_LOG_RANGE_DAYS}
          max={MAX_LOG_RANGE_DAYS}
          step={LOG_RANGE_SLIDER_STEP}
          value={sliderValue}
          dir="rtl"
          minStepsBetweenThumbs={1}
          onValueChange={handleValueChange}
          onValueCommit={handleValueCommit}
          aria-label="로그 조회 기간 선택"
        />
      </div>
      <span className="mt-5 shrink-0 text-[11px] text-muted-foreground">
        -1 day
      </span>
    </div>
  );
}
