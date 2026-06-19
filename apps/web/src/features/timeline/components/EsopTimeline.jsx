import React from "react";
import BaseTimeline from "./BaseTimeline";
import TimelineLegend from "./TimelineLegend";
import TimelineEmptyState from "./TimelineEmptyState";
import { buildFixedHeightOptions } from "../utils/timelineUtils";
import { processData } from "../utils/visTimelineItems";
import { makeGroupLabel } from "../utils/groupLabel";
import { timelineLegends } from "../utils/timelineLegends";

const ESOP_GROUP = {
  id: "ESOP",
  content: makeGroupLabel("ESOP", "ESOP"),
  className: "custom-group-label",
  order: 1,
};

export default function EsopTimeline({
  range,
  showLegend,
  showTimeAxis = false,
  esopLogs = [],
}) {
  const items = processData("ESOP", esopLogs);

  const options = buildFixedHeightOptions(range, 76);

  if (esopLogs.length === 0) {
    return (
      <TimelineEmptyState title="🚁 ESOP" message="ESOP 로그가 없습니다" />
    );
  }

  return (
    <BaseTimeline
      groups={[ESOP_GROUP]}
      items={items}
      options={options}
      title="🚁 ESOP"
      showTimeAxis={showTimeAxis}
      headerExtra={
        showLegend ? <TimelineLegend items={timelineLegends.ESOP} /> : null
      }
    />
  );
}
