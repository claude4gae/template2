// src/features/timeline/components/LogViewerSection.jsx - 개선된 버전
import React from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import DirectEqpQuery from "./sections/DirectEqpQuery";
import LogViewerSelectors from "./sections/LogViewerSelectors";
import LogRangeSlider from "./LogRangeSlider";
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
}) {
  const directQuery = useDirectEquipmentQuery({
    setLine,
    setSdwt,
    setPrcGroup,
    setEqp,
  });

  return (
    <section className="border border-border bg-card shadow-sm rounded-xl p-3 flex flex-col">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex shrink-0 items-center gap-5">
          <h2 className="text-md font-bold text-foreground">
            📊 Log Viewer
          </h2>
          <div className="flex items-center gap-2">
            <Label
              htmlFor="timeline-direct-eqp-query"
              className="cursor-pointer text-xs text-muted-foreground"
            >
              EQPID 바로조회
            </Label>
            <Switch
              id="timeline-direct-eqp-query"
              checked={directQuery.isDirectQuery}
              onCheckedChange={directQuery.handleToggleChange}
            />
          </div>
        </div>
        <div className="ml-auto flex min-w-[320px] flex-1 items-start justify-end">
          <LogRangeSlider
            value={logRange}
            onChange={onLogRangeChange}
          />
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
