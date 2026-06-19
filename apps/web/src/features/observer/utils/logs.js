import { getTipGroupKey } from "./tipUtils";

const RANGE_LOG_TYPES = new Set(["EQP", "TIP"]);
const ONE_HOUR_MS = 60 * 60 * 1000;

function getStartOfToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
}

export function getContinuousRangeEnd(start, sortedLogs, index) {
  if (index < sortedLogs.length - 1) {
    return new Date(sortedLogs[index + 1].eventTime);
  }

  const todayStart = getStartOfToday();
  if (start < todayStart) {
    return todayStart;
  }

  return new Date(start.getTime() + ONE_HOUR_MS);
}

export function formatDuration(duration) {
  if (!duration || duration <= 0) return "-";

  const totalSeconds = Math.floor(duration / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return [
    hours.toString().padStart(2, "0"),
    minutes.toString().padStart(2, "0"),
    seconds.toString().padStart(2, "0"),
  ].join(":");
}

/**
 * Observer 로그 가공에 공통으로 사용하는 작은 유틸리티입니다.
 */
export function addDurationToLogs(logs = [], logType) {
  if (!logs.length) return logs;

  const sortedLogs = [...logs].sort(
    (a, b) => new Date(a.eventTime) - new Date(b.eventTime)
  );
  const isRangeType = RANGE_LOG_TYPES.has(logType);

  if (isRangeType && logType === "TIP") {
    const durationByLog = new WeakMap();
    const logsByTipGroup = new Map();

    sortedLogs.forEach((log) => {
      const groupKey = getTipGroupKey(log);
      const groupLogs = logsByTipGroup.get(groupKey) ?? [];
      groupLogs.push(log);
      logsByTipGroup.set(groupKey, groupLogs);
    });

    logsByTipGroup.forEach((groupLogs) => {
      groupLogs.forEach((log, index) => {
        const start = new Date(log.eventTime);
        const end = getContinuousRangeEnd(start, groupLogs, index);
        durationByLog.set(log, {
          duration: end.getTime() - start.getTime(),
          endTime: end.toISOString(),
        });
      });
    });

    return sortedLogs.map((log) => ({
      ...log,
      ...durationByLog.get(log),
    }));
  }

  return sortedLogs.map((log, index) => {
    if (!isRangeType) {
      return { ...log, duration: null, endTime: null };
    }

    const start = new Date(log.eventTime);
    const end = getContinuousRangeEnd(start, sortedLogs, index);
    const duration = end.getTime() - start.getTime();

    return { ...log, duration, endTime: end.toISOString() };
  });
}

export function mergeLogsByTime(logsByType = {}) {
  const {
    eqpLogs = [],
    tipLogs = [],
    ctttmLogs = [],
    racbLogs = [],
    esopLogs = [],
  } = logsByType;

  return [
    ...eqpLogs,
    ...tipLogs,
    ...ctttmLogs,
    ...racbLogs,
    ...esopLogs,
  ]
    .filter((log) => log && log.eventTime)
    .sort(
      (a, b) =>
        new Date(b.eventTime).getTime() - new Date(a.eventTime).getTime()
    );
}
