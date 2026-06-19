// src/features/observer/components/CtttmObserver.jsx
import React from "react";
import BaseObserver from "./BaseObserver";
import ObserverLegend from "./ObserverLegend";
import ObserverEmptyState from "./ObserverEmptyState";
import { buildFixedHeightOptions } from "../utils/observerUtils";
import { processData } from "../utils/visObserverItems";
import { makeGroupLabel } from "../utils/groupLabel";
import { observerLegends } from "../utils/observerLegends";

const CTTTM_GROUP = {
  id: "CTTTM",
  content: makeGroupLabel("CTTTM", "CTTTM"),
  className: "custom-group-label",
  order: 1,
};

export default function CtttmObserver({
  range,
  showLegend,
  showTimeAxis = false,
  ctttmLogs = [],
}) {
  const items = processData("CTTTM", ctttmLogs);

  const options = buildFixedHeightOptions(range, 76);

  if (ctttmLogs.length === 0) {
    return (
      <ObserverEmptyState
        title="⚠️ CTTTM"
        message="CTTTM 로그가 없습니다"
        bodyClassName="h-[74px]"
      />
    );
  }

  return (
    <BaseObserver
      groups={[CTTTM_GROUP]}
      items={items}
      options={options}
      title="⚠️ CTTTM"
      showTimeAxis={showTimeAxis}
      headerExtra={
        showLegend ? <ObserverLegend items={observerLegends.CTTTM} /> : null
      }
    />
  );
}
