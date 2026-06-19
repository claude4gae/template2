// src/features/observer/components/LogViewerSection.jsx - 개선된 버전
import React from "react";
import { AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import DirectEqpQuery from "./sections/DirectEqpQuery";
import LogViewerSelectors from "./sections/LogViewerSelectors";
import LogRangeSlider from "./LogRangeSlider";
import ShareButton from "./ShareButton";
import { useDirectEquipmentQuery } from "../hooks/useDirectEquipmentQuery";

export default function LogViewerSection({
  lineId,
  sdwtId,
  prcGroup,
  eqpId,
  setLine,
  setSdwt,
  setPrcGroup,
  setEqp,
  logRange,
  onLogRangeChange,
  showSettingsButton = false,
  isSettingsOpen = false,
  isSettingsDisabled = false,
  onSettingsToggle,
  showShareButton = false,
}) {
  const directQuery = useDirectEquipmentQuery({
    setLine,
    setSdwt,
    setPrcGroup,
    setEqp,
  });

  return (
    <section className="border border-border bg-card shadow-sm rounded-xl p-3 flex flex-col">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <LogRangeSlider
          value={logRange}
          onChange={onLogRangeChange}
        />
        <div className="ml-auto flex shrink-0 items-center justify-end gap-2">
          <div className="flex h-9 shrink-0 items-center gap-2 rounded-md border border-border bg-card px-3">
            <Checkbox
              id="observer-direct-eqp-query"
              checked={directQuery.isDirectQuery}
              onCheckedChange={(checked) =>
                directQuery.handleToggleChange(checked === true)
              }
            />
            <Label
              htmlFor="observer-direct-eqp-query"
              className="cursor-pointer text-xs text-muted-foreground"
            >
              EQP 바로조회
            </Label>
          </div>
          {showSettingsButton ? (
            <button
              type="button"
              onClick={onSettingsToggle}
              disabled={isSettingsDisabled}
              aria-pressed={isSettingsOpen}
              className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border border-border bg-card px-3 text-xs font-medium text-foreground transition hover:bg-muted focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-card"
            >
              <AdjustmentsHorizontalIcon className="h-4 w-4" />
              설정
            </button>
          ) : null}
          {showShareButton ? <ShareButton /> : null}
        </div>
      </div>

      <LogViewerSelectors
        lineId={lineId}
        sdwtId={sdwtId}
        prcGroup={prcGroup}
        eqpId={eqpId}
        setLine={setLine}
        setSdwt={setSdwt}
        setPrcGroup={setPrcGroup}
        setEqp={setEqp}
        isDirectQuery={directQuery.isDirectQuery}
        directQueryControl={
          <DirectEqpQuery
            inputEqpId={directQuery.inputEqpId}
            isLoading={directQuery.isLoading}
            onInputChange={directQuery.handleInputChange}
            onKeyPress={directQuery.handleKeyPress}
            onSubmit={directQuery.handleDirectQuery}
          />
        }
      />
    </section>
  );
}
