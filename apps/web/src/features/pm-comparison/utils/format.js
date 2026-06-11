// 파일 경로: src/features/pm-comparison/utils/format.js
// PM SPIDER 화면 표시와 요청 payload 변환 유틸입니다.

export const DEFAULT_PM_FORM = {
  lineId: "LINE_DEMO",
  eqpId: "EQP_DEMO_01",
  fdcBin: "BIN_DEMO",
  pattern: "",
  ppid: "PPID_DEMO",
  recipeId: "RCP_DEMO",
  pmTimestamp: "2026-06-02",
  beforeHours: "6",
  afterHours: "6",
  traceParamNames: "",
  dtValues: "2026-06-02",
  traceDataSource: "trace",
  oesDataSource: "oes",
  limit: "500",
}

export const PM_SPIDER_CATEGORIES = [
  {
    id: "npw-trace",
    label: "NPW TRACE",
    pattern: "NPW",
    patternLabel: "NPW",
    kind: "trace",
    sourceLabel: "Trace",
    description: "non pattern wafer(dummy wafer)",
  },
  {
    id: "npw-oes",
    label: "NPW OES",
    pattern: "NPW",
    patternLabel: "NPW",
    kind: "oes",
    sourceLabel: "OES",
    description: "non pattern wafer(dummy wafer)",
  },
  {
    id: "pw-trace",
    label: "PW TRACE",
    pattern: "PW",
    patternLabel: "PW",
    kind: "trace",
    sourceLabel: "Trace",
    description: "Pattern WAFER",
  },
  {
    id: "pw-oes",
    label: "PW OES",
    pattern: "PW",
    patternLabel: "PW",
    kind: "oes",
    sourceLabel: "OES",
    description: "Pattern WAFER",
  },
]

export function splitCsv(value) {
  if (!value) return []
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

export function hasRequiredPmFilters(form) {
  return Boolean(form.lineId && form.eqpId && form.pmTimestamp)
}

export function buildPmComparisonPayload(form) {
  return {
    lineId: form.lineId.trim(),
    eqpId: form.eqpId.trim(),
    fdcBin: form.fdcBin.trim(),
    pattern: form.pattern.trim(),
    ppid: form.ppid.trim(),
    recipeId: form.recipeId.trim(),
    pmTimestamp: form.pmTimestamp,
    beforeHours: Number(form.beforeHours || 24),
    afterHours: Number(form.afterHours || 24),
    traceParamNames: splitCsv(form.traceParamNames),
    dtValues: splitCsv(form.dtValues),
    traceDataSource: form.traceDataSource.trim() || "trace",
    oesDataSource: form.oesDataSource.trim() || "oes",
    limit: Number(form.limit || 1200),
  }
}

export function buildPmSpiderPatternPayloads(payload) {
  if (!payload) return []
  return ["NPW", "PW"].map((pattern) => ({
    pattern,
    payload: {
      ...payload,
      pattern,
    },
  }))
}

export function formatNumber(value, digits = 3) {
  if (value === null || value === undefined || value === "") return "-"
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
  }).format(numeric)
}

export function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-"
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return "-"
  return `${formatNumber(numeric * 100, 1)}%`
}

export function formatDateTime(value) {
  if (!value) return "-"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

export function normalizeOptions(values) {
  return Array.isArray(values) ? values.filter(Boolean) : []
}
