// src/features/observer/utils/tipUtils.js 그룹키 생성

export function getTipGroupKey(log) {
  return `${log.lineId || "UNKNOWN_LINE"}_${log.process || "unknown"}_${
    log.step || "unknown"
  }_${log.ppid || "unknown"}`;
}

export function filterTipLogsByGroups(
  tipLogs = [],
  selectedTipGroups = ["__ALL__"]
) {
  if (!Array.isArray(tipLogs) || tipLogs.length === 0) return [];
  if (!selectedTipGroups || selectedTipGroups.includes("__ALL__")) {
    return tipLogs;
  }

  const selectedSet = new Set(selectedTipGroups);
  return tipLogs.filter((log) => selectedSet.has(getTipGroupKey(log)));
}
