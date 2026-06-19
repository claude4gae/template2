import React from "react";
import EqpObserver from "./EqpObserver";
import TipObserver from "./TipObserver";
import CtttmObserver from "./CtttmObserver";
import RacbObserver from "./RacbObserver";
import EsopObserver from "./EsopObserver";
import { useObserverRange } from "../hooks/useObserverRange";
import { filterTipLogsByGroups } from "../utils/tipUtils";

export default function ObserverBoard({
  showLegend,
  selectedTipGroups,
  eqpLogs = [],
  tipLogs = [],
  ctttmLogs = [],
  racbLogs = [],
  esopLogs = [],
  typeFilters,
}) {
  const visibleTipLogs = filterTipLogsByGroups(tipLogs, selectedTipGroups);

  const visibleLogs = [
    ...(typeFilters?.EQP ? eqpLogs : []),
    ...(typeFilters?.TIP ? visibleTipLogs : []),
    ...(typeFilters?.CTTTM ? ctttmLogs : []),
    ...(typeFilters?.RACB ? racbLogs : []),
    ...(typeFilters?.ESOP ? esopLogs : []),
  ];

  const range = useObserverRange(visibleLogs);
  const hasVisibleLogs = visibleLogs.length > 0;

  // 아무 데이터도 없는 경우
  if (!hasVisibleLogs) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        표시할 로그 데이터가 없습니다. 필터를 확인해주세요.
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* Observer이 많아질 때를 위한 스크롤 컨테이너 - absolute로 부모의 전체 영역을 차지 */}
      <div className="absolute inset-0 overflow-y-auto space-y-0 scroll-smooth px-3 mt-5 mb-10 z-[1]">
        {/* EQP Observer */}
        {typeFilters?.EQP && (
          <EqpObserver
            range={range}
            showLegend={showLegend}
            showTimeAxis={true}
            eqpLogs={eqpLogs}
          />
        )}

        {/* TIP Observer */}
        {typeFilters?.TIP && (
          <TipObserver
            range={range}
            showLegend={showLegend}
            showTimeAxis={true}
            totalTipLogCount={tipLogs.length}
            tipLogs={visibleTipLogs}
          />
        )}

        {/* CTTTM Observer */}
        {typeFilters?.CTTTM && (
          <CtttmObserver
            range={range}
            showLegend={showLegend}
            showTimeAxis={true}
            ctttmLogs={ctttmLogs}
          />
        )}

        {/* RACB Observer */}
        {typeFilters?.RACB && (
          <RacbObserver
            range={range}
            showLegend={showLegend}
            showTimeAxis={true}
            racbLogs={racbLogs}
          />
        )}

        {/* ESOP Observer */}
        {typeFilters?.ESOP && (
          <EsopObserver
            range={range}
            showLegend={showLegend}
            showTimeAxis={true}
            esopLogs={esopLogs}
          />
        )}
      </div>
    </div>
  );
}
