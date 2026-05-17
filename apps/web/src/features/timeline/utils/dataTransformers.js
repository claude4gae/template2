// src/features/timeline/utils/dataTransformers.js
import { formatDateTime } from "./dateUtils";
import { formatDuration } from "./logs";
import { getTipGroupKey } from "./tipUtils";

function isLogVisible(log, typeFilters, selectedTipGroups) {
  if (!typeFilters[log.logType]) return false;

  if (log.logType === "TIP" && !selectedTipGroups.includes("__ALL__")) {
    return selectedTipGroups.includes(getTipGroupKey(log));
  }

  return true;
}

function buildTableRow(log) {
  const row = {
    id: log.id,
    timestamp: new Date(log.eventTime).getTime(),
    displayTimestamp: formatDateTime(log.eventTime),
    logType: log.logType,
    info1: log.eventType,
    info2: log.operator || "-",
    duration: formatDuration(log.duration),
    url: log.url || null,
  };

  if (log.logType === "TIP" && (log.process || log.step || log.ppid)) {
    row.info1 = `${log.eventType} (${log.process || "N/A"}/${
      log.step || "N/A"
    })`;
  }

  return row;
}

export function transformLogsToTableData(
  logs,
  typeFilters,
  selectedTipGroups = ["__ALL__"]
) {
  return logs
    .filter((log) => isLogVisible(log, typeFilters, selectedTipGroups))
    .map((log) => buildTableRow(log))
    .sort((a, b) => b.timestamp - a.timestamp);
}
