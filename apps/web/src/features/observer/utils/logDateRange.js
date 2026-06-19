import {
  DEFAULT_LOG_RANGE_DAYS,
  MAX_LOG_RANGE_DAYS,
  MIN_LOG_RANGE_DAYS,
} from "./constants";

function toValidNumber(value, fallback = DEFAULT_LOG_RANGE_DAYS) {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : fallback;
}

export function clampLogRangeDays(value) {
  const numberValue = Math.round(toValidNumber(value));
  return Math.min(Math.max(numberValue, MIN_LOG_RANGE_DAYS), MAX_LOG_RANGE_DAYS);
}

export function getDefaultLogRange() {
  return {
    startDaysAgo: DEFAULT_LOG_RANGE_DAYS,
    endDaysAgo: MIN_LOG_RANGE_DAYS,
  };
}

export function normalizeLogRange(value) {
  if (typeof value === "number") {
    return {
      startDaysAgo: clampLogRangeDays(value),
      endDaysAgo: MIN_LOG_RANGE_DAYS,
    };
  }

  const fallback = getDefaultLogRange();
  const startCandidate = value?.startDaysAgo ?? fallback.startDaysAgo;
  const endCandidate = value?.endDaysAgo ?? fallback.endDaysAgo;
  const startDaysAgo = clampLogRangeDays(startCandidate);
  const endDaysAgo = clampLogRangeDays(endCandidate);

  return {
    startDaysAgo: Math.max(startDaysAgo, endDaysAgo),
    endDaysAgo: Math.min(startDaysAgo, endDaysAgo),
  };
}

function formatDateParam(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateLabel(date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${month}/${day}`;
}

function getDateFromDaysAgo(daysAgo) {
  const date = new Date();
  date.setDate(date.getDate() - clampLogRangeDays(daysAgo) + 1);
  return date;
}

export function getLogDateRange(rangeValue) {
  const range = normalizeLogRange(rangeValue);
  const from = getDateFromDaysAgo(range.startDaysAgo);
  const to = getDateFromDaysAgo(range.endDaysAgo);

  return { from, to, ...range };
}

export function getLogRangeSpanDays(rangeValue) {
  const range = normalizeLogRange(rangeValue);
  return range.startDaysAgo - range.endDaysAgo + 1;
}

export function getRecentLogDateRange(rangeDays) {
  const days = clampLogRangeDays(rangeDays);
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - days + 1);

  return { from, to, days };
}

export function buildLogDateRangeOptions(rangeValue) {
  const { from, to } = getLogDateRange(rangeValue);
  return {
    from: formatDateParam(from),
    to: formatDateParam(to),
  };
}

export function formatLogRangeLabel(rangeValue) {
  const spanDays = getLogRangeSpanDays(rangeValue);
  return `${spanDays} days`;
}

export function formatLogRangeWindow(rangeValue) {
  const { from, to } = getLogDateRange(rangeValue);
  return `${formatDateLabel(from)} ~ ${formatDateLabel(to)}`;
}
