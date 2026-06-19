// src/features/observer/components/EqpObserver.jsx
import React from "react";
import BaseObserver from "./BaseObserver";
import ObserverLegend from "./ObserverLegend";
import ObserverEmptyState from "./ObserverEmptyState";
import { buildFixedHeightOptions } from "../utils/observerUtils";
import { processData } from "../utils/visObserverItems";
import { makeGroupLabel } from "../utils/groupLabel";
import { observerLegends } from "../utils/observerLegends";

const EQP_GROUP = {
  id: "EQP",
  content: makeGroupLabel("EQP", "EQP 로그"),
  className: "custom-group-label",
  order: 1,
};

export default function EqpObserver({
  range,
  showLegend,
  showTimeAxis = false,
  eqpLogs = [],
}) {
  const items = processData("EQP", eqpLogs, true);

  const options = buildFixedHeightOptions(range, 75, {
    minHeight: 28,
    maxHeight: 75,
    align: "top",
    zoomFriction: 5,
  });

  if (eqpLogs.length === 0) {
    return (
      <ObserverEmptyState title="⚙️ EQP 상태" message="EQP 로그가 없습니다" />
    );
  }

  return (
    <BaseObserver
      groups={[EQP_GROUP]}
      items={items}
      options={options}
      title="⚙️ EQP 상태"
      showTimeAxis={showTimeAxis}
      headerExtra={
        showLegend ? <ObserverLegend items={observerLegends.EQP} /> : null
      }
    />
  );
}
