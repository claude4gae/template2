import {
  CATEGORY_COLORS,
  DEFAULT_BIN,
  DIMENSION_ALIASES,
  METRIC_LABELS,
  METRIC_OPTIONS,
} from "./lineHistoryConfig"

const MS_PER_DAY = 24 * 60 * 60 * 1000
const KST_OFFSET = "+09:00"
const METRIC_KEYS = METRIC_OPTIONS.map((option) => option.value)

const KST_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  year: "2-digit",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  hour12: false,
  timeZone: "Asia/Seoul",
})

const KST_PARTS_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Seoul",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  hour12: false,
})

const KST_DATE_LABEL_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  month: "2-digit",
  day: "2-digit",
})

const KST_YEAR_MONTH_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  year: "2-digit",
  month: "2-digit",
})

const KST_FULL_DATE_FORMATTER = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  year: "2-digit",
  month: "2-digit",
  day: "2-digit",
})

function parseDateTime(value) {
  if (!value) return null
  if (value instanceof Date) return value

  const normalized =
    typeof value === "string" && value.includes("T")
      ? value
      : typeof value === "string"
        ? value.replace(" ", "T")
        : String(value)

  const parsed = new Date(normalized)
  return Number.isFinite(parsed.getTime()) ? parsed : null
}

function formatKstDateTimeLabel(value) {
  const date = parseDateTime(value)
  if (!date) return typeof value === "string" ? value : String(value ?? "")

  const parts = Object.fromEntries(
    KST_FORMATTER.formatToParts(date).map((part) => [part.type, part.value]),
  )
  const month = parts.month ?? ""
  const day = parts.day ?? ""
  const hour = parts.hour ?? ""

  return `${month}/${day} ${hour}:00`
}

function formatKstTooltipTime(value) {
  const date = parseDateTime(value)
  if (!date) return typeof value === "string" ? value : String(value ?? "")

  const parts = Object.fromEntries(
    KST_FORMATTER.formatToParts(date).map((part) => [part.type, part.value]),
  )

  const year = parts.year ?? ""
  const month = parts.month ?? ""
  const day = parts.day ?? ""
  const hour = parts.hour ?? ""

  return `${year}/${month}/${day} ${hour}:00`
}

function pad2(value) {
  return String(value ?? "").padStart(2, "0")
}

function getKstParts(value) {
  const date = parseDateTime(value)
  if (!date) return null

  const parts = Object.fromEntries(
    KST_PARTS_FORMATTER.formatToParts(date).map((part) => [part.type, part.value]),
  )

  const year = Number(parts.year)
  const month = Number(parts.month)
  const day = Number(parts.day)
  const hour = Number(parts.hour)

  if (![year, month, day, hour].every((partValue) => Number.isFinite(partValue))) return null
  return { year, month, day, hour }
}

function buildKstIsoDate({ year, month, day, hour = 0 }) {
  return `${year}-${pad2(month)}-${pad2(day)}T${pad2(hour)}:00:00${KST_OFFSET}`
}

function getBucketInfo(value, bin = DEFAULT_BIN) {
  const parts = getKstParts(value)
  if (!parts) return null

  let { year, month, day, hour } = parts
  const startHour = bin === "hour" ? hour : 0

  if (bin === "week") {
    const baseDate = new Date(Date.UTC(year, month - 1, day))
    const dayOfWeek = baseDate.getUTCDay()
    const diffToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek
    baseDate.setUTCDate(baseDate.getUTCDate() + diffToMonday)
    year = baseDate.getUTCFullYear()
    month = baseDate.getUTCMonth() + 1
    day = baseDate.getUTCDate()
  } else if (bin === "month") {
    day = 1
  }

  const bucketDate = buildKstIsoDate({ year, month, day, hour: startHour })
  const startDate = parseDateTime(bucketDate)
  if (!startDate) return null

  let endDate = startDate
  if (bin === "week") {
    endDate = new Date(startDate.getTime() + 6 * MS_PER_DAY)
  } else if (bin === "month") {
    const daysInMonth = new Date(year, month, 0).getDate()
    const endDateString = buildKstIsoDate({
      year,
      month,
      day: daysInMonth,
      hour: startHour,
    })
    endDate = parseDateTime(endDateString) ?? startDate
  }

  return { key: bucketDate, startDate, endDate }
}

const sortByDateValue = (a, b) => {
  if (a?.date < b?.date) return -1
  if (a?.date > b?.date) return 1
  return 0
}

export function aggregateTotalsByBin(records, bin = DEFAULT_BIN) {
  if (!Array.isArray(records)) return []
  if (bin === "hour") return [...records].sort(sortByDateValue)

  const bucketMap = new Map()
  for (const record of records) {
    const bucket = getBucketInfo(record?.date, bin)
    if (!bucket) continue
    const existing = bucketMap.get(bucket.key) ?? { date: bucket.key }
    for (const metricKey of METRIC_KEYS) {
      const value = Number(record?.[metricKey] ?? 0) || 0
      existing[metricKey] = (existing[metricKey] ?? 0) + value
    }
    bucketMap.set(bucket.key, existing)
  }

  return Array.from(bucketMap.keys())
    .sort()
    .map((key) => bucketMap.get(key))
}

function aggregateBreakdownRecordsByBin(records, bin = DEFAULT_BIN) {
  if (!Array.isArray(records)) return []
  if (bin === "hour") return [...records].sort(sortByDateValue)

  const bucketMap = new Map()

  for (const record of records) {
    const bucket = getBucketInfo(record?.date, bin)
    if (!bucket) continue
    const category =
      typeof record?.category === "string" && record.category.trim().length > 0
        ? record.category.trim()
        : "Unspecified"
    const bucketKey = `${bucket.key}__${category}`
    const existing = bucketMap.get(bucketKey) ?? {
      date: bucket.key,
      category,
    }

    for (const metricKey of METRIC_KEYS) {
      const value = Number(record?.[metricKey] ?? 0) || 0
      existing[metricKey] = (existing[metricKey] ?? 0) + value
    }

    bucketMap.set(bucketKey, existing)
  }

  return Array.from(bucketMap.values()).sort((a, b) => {
    if (a.date < b.date) return -1
    if (a.date > b.date) return 1
    return String(a.category).localeCompare(String(b.category))
  })
}

export function aggregateBreakdownsByBin(breakdowns, bin = DEFAULT_BIN) {
  if (!breakdowns || typeof breakdowns !== "object") return {}
  if (bin === "hour") return breakdowns

  return Object.fromEntries(
    Object.entries(breakdowns).map(([dimensionKey, records]) => [
      dimensionKey,
      aggregateBreakdownRecordsByBin(records, bin),
    ]),
  )
}

export function formatAxisLabelByBin(value, bin = DEFAULT_BIN) {
  if (bin === "hour") return formatKstDateTimeLabel(value)
  const bucket = getBucketInfo(value, bin)
  if (!bucket?.startDate) return typeof value === "string" ? value : String(value ?? "")

  if (bin === "day") {
    return KST_DATE_LABEL_FORMATTER.format(bucket.startDate)
  }

  if (bin === "week") {
    return `${KST_DATE_LABEL_FORMATTER.format(bucket.startDate)}~${KST_DATE_LABEL_FORMATTER.format(bucket.endDate)}`
  }

  if (bin === "month") {
    return KST_YEAR_MONTH_FORMATTER.format(bucket.startDate)
  }

  return formatKstDateTimeLabel(value)
}

export function formatTooltipLabelByBin(value, bin = DEFAULT_BIN) {
  if (bin === "hour") return formatKstTooltipTime(value)
  const bucket = getBucketInfo(value, bin)
  if (!bucket?.startDate) return typeof value === "string" ? value : String(value ?? "")

  if (bin === "day") {
    return KST_FULL_DATE_FORMATTER.format(bucket.startDate)
  }

  if (bin === "week") {
    return `${KST_FULL_DATE_FORMATTER.format(bucket.startDate)} ~ ${KST_FULL_DATE_FORMATTER.format(bucket.endDate)}`
  }

  if (bin === "month") {
    const monthLabel = KST_YEAR_MONTH_FORMATTER.format(bucket.startDate)
    const rangeLabel = `${KST_DATE_LABEL_FORMATTER.format(bucket.startDate)}~${KST_DATE_LABEL_FORMATTER.format(bucket.endDate)}`
    return `${monthLabel} (${rangeLabel})`
  }

  return formatKstTooltipTime(value)
}

export function getDefaultDateRange(days = 30) {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - (Number.isFinite(days) ? days : 30) + 1)
  return { from, to }
}

export function formatRangeLabel(range) {
  const { from, to } = range ?? {}
  if (!from || !to) return "날짜 범위 선택"
  const formatter = new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" })
  return `${formatter.format(from)} ~ ${formatter.format(to)}`
}

export function buildBreakdownSeries(
  records,
  metrics,
  limit = 5,
  selectedCategories = [],
  dimensionKey = "",
  dimensionLabel = "",
  colorOverrides = {},
) {
  if (
    !Array.isArray(records) ||
    records.length === 0 ||
    !Array.isArray(metrics) ||
    metrics.length === 0
  ) {
    return { data: [], categories: [], config: {}, seriesKeys: [] }
  }

  const safeKeyCache = new Map()
  const getSafeKey = (raw) => {
    const key = String(raw ?? "")
    if (!safeKeyCache.has(key)) {
      const sanitized = key.replace(/[^A-Za-z0-9_-]/g, "_")
      if (sanitized && sanitized === key && sanitized.length <= 64) {
        safeKeyCache.set(key, sanitized)
      } else {
        const hash = Math.abs(
          Array.from(key).reduce(
            (acc, char) => (acc * 31 + char.charCodeAt(0)) | 0,
            0,
          ),
        ).toString(36)
        const trimmed = sanitized
          .slice(0, Math.max(12, 64 - hash.length - 1))
          .replace(/_+$/g, "")
        safeKeyCache.set(
          key,
          [trimmed || "series", hash].filter(Boolean).join("_"),
        )
      }
    }
    return safeKeyCache.get(key)
  }

  const totalsByCategory = new Map()
  const dateSet = new Set()
  const primaryMetric = metrics[0]

  for (const record of records) {
    const category =
      typeof record?.category === "string" && record.category.trim().length > 0
        ? record.category.trim()
        : "Unspecified"
    const value = Number(record?.[primaryMetric] ?? 0) || 0
    dateSet.add(record?.date)
    totalsByCategory.set(category, (totalsByCategory.get(category) ?? 0) + value)
  }

  const normalizedSelected = Array.isArray(selectedCategories)
    ? selectedCategories.filter(Boolean)
    : []

  const categories =
    normalizedSelected.length > 0
      ? normalizedSelected.filter((category) => totalsByCategory.has(category))
      : Array.from(totalsByCategory.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([category]) => category)

  const sortedDates = Array.from(dateSet)
    .filter(Boolean)
    .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))

  const seriesKeyMap = new Map()
  categories.forEach((category) => {
    metrics.forEach((metricKey) => {
      const rawKey = [dimensionKey || "dim", category, metricKey]
        .filter(Boolean)
        .join("__")
      seriesKeyMap.set(rawKey, getSafeKey(rawKey))
    })
  })

  const basePoints = sortedDates.map((date) => {
    const point = { date }
    for (const safeKey of seriesKeyMap.values()) {
      point[safeKey] = 0
    }
    return point
  })

  const pointsByDate = new Map(basePoints.map((point) => [point.date, point]))

  for (const record of records) {
    const category =
      typeof record?.category === "string" && record.category.trim().length > 0
        ? record.category.trim()
        : "Unspecified"
    if (!categories.includes(category)) continue

    const date = record?.date
    if (!date || !pointsByDate.has(date)) continue

    const point = pointsByDate.get(date)
    for (const metricKey of metrics) {
      const value = Number(record?.[metricKey] ?? 0) || 0
      const rawKey = [dimensionKey || "dim", category, metricKey]
        .filter(Boolean)
        .join("__")
      const safeKey = seriesKeyMap.get(rawKey) ?? getSafeKey(rawKey)
      point[safeKey] = (point[safeKey] ?? 0) + value
    }
  }

  const config = {}
  const seriesKeys = []
  categories.forEach((category, categoryIndex) => {
    metrics.forEach((metricKey, metricIndex) => {
      const rawKey = [dimensionKey || "dim", category, metricKey]
        .filter(Boolean)
        .join("__")
      const seriesKey = seriesKeyMap.get(rawKey) ?? getSafeKey(rawKey)
      const paletteIndex =
        (categoryIndex * metrics.length + metricIndex) % CATEGORY_COLORS.length
      const color =
        colorOverrides?.[category] ?? CATEGORY_COLORS[paletteIndex]
      const dimensionLabelText = dimensionLabel || dimensionKey || "분류"

      let label
      if (metrics.length === 1) {
        label = String(category)
      } else {
        label = `${dimensionLabelText} · ${category} · ${METRIC_LABELS[metricKey] ?? metricKey}`
      }

      config[seriesKey] = { label, color, category }
      seriesKeys.push(seriesKey)
    })
  })

  return { data: basePoints, categories, config, seriesKeys }
}

export function buildTotals(records) {
  const totals = new Map()
  for (const record of records) {
    const category =
      typeof record?.category === "string" && record.category.trim().length > 0
        ? record.category.trim()
        : "Unspecified"
    const value = Number(record?.rowCount ?? 0) || 0
    totals.set(category, (totals.get(category) ?? 0) + value)
  }
  return Array.from(totals.entries()).sort((a, b) => b[1] - a[1])
}

export function resolveDimensionRecords(breakdownsByDimension, dimensionKey) {
  if (!breakdownsByDimension || typeof breakdownsByDimension !== "object") {
    return { key: dimensionKey, records: [] }
  }

  const candidates = [dimensionKey, ...(DIMENSION_ALIASES[dimensionKey] ?? [])].filter(
    Boolean,
  )
  const lowerCandidates = new Set(candidates.map((key) => key.toLowerCase()))

  for (const [rawKey, rawRecords] of Object.entries(breakdownsByDimension)) {
    if (!lowerCandidates.has(String(rawKey).toLowerCase())) continue
    if (Array.isArray(rawRecords)) return { key: rawKey, records: rawRecords }
  }

  for (const key of candidates) {
    const records = breakdownsByDimension?.[key]
    if (Array.isArray(records)) return { key, records }
  }

  return { key: dimensionKey, records: [] }
}
