// src/features/observer/components/RacbObserver.jsx
import React from "react";
import BaseObserver from "./BaseObserver";
import ObserverLegend from "./ObserverLegend";
import ObserverEmptyState from "./ObserverEmptyState";
import { buildFixedHeightOptions } from "../utils/observerUtils";
import { processData } from "../utils/visObserverItems";
import { makeGroupLabel } from "../utils/groupLabel";
import { observerLegends } from "../utils/observerLegends";

const RACB_GROUP = {
  id: "RACB",
  content: makeGroupLabel("RACB", "RACB"),
  className: "custom-group-label",
  order: 1,
};

export default function RacbObserver({
  range,
  showLegend,
  showTimeAxis = false,
  racbLogs = [],
}) {
  const items = processData("RACB", racbLogs);

  const options = buildFixedHeightOptions(range, 76);

  if (racbLogs.length === 0) {
    return (
      <ObserverEmptyState title="🚨 RACB" message="RACB 로그가 없습니다" />
    );
  }

  return (
    <BaseObserver
      groups={[RACB_GROUP]}
      items={items}
      options={options}
      title="🚨 RACB"
      showTimeAxis={showTimeAxis}
      headerExtra={
        showLegend ? <ObserverLegend items={observerLegends.RACB} /> : null
      }
    />
  );
}
