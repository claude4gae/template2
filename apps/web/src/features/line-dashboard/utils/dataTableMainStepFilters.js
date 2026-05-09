export function normalizeMainStep(value) {
  if (value == null) return null
  const trimmed = String(value).trim()
  return trimmed.length > 0 ? trimmed : null
}

export function extractMainStepSuffix(value) {
  const normalized = normalizeMainStep(value)
  if (!normalized) return null
  const match = normalized.match(/(\d+)\s*$/)
  return match ? match[1] : null
}

export function extractMainStepPrefix(value) {
  const normalized = normalizeMainStep(value)
  if (!normalized) return ""
  const match = normalized.match(/^([A-Za-z]+)/)
  return match ? match[1] : ""
}

export function toMainStepFilterValue(value) {
  const normalized = normalizeMainStep(value)
  if (!normalized) return null
  return extractMainStepSuffix(normalized) ?? normalized
}

export function buildMainStepToken(suffix, prefix = "*") {
  const normalizedSuffix = toMainStepFilterValue(suffix)
  if (!normalizedSuffix) return null
  const normalizedPrefix =
    prefix === null || prefix === undefined || prefix === "" ? "*" : String(prefix).trim()
  return `${normalizedSuffix}|${normalizedPrefix || "*"}`
}

export function parseMainStepToken(token) {
  if (token === null || token === undefined) return null

  if (typeof token === "object" && "suffix" in token) {
    const suffix = toMainStepFilterValue(token.suffix)
    if (!suffix) return null
    const prefix =
      token.prefix === undefined || token.prefix === null || token.prefix === ""
        ? "*"
        : String(token.prefix).trim()
    return { suffix, prefix }
  }

  const raw = typeof token === "string" ? token.trim() : String(token)
  if (!raw) return null

  const [maybeSuffix, maybePrefix] = raw.split("|")
  const suffix = toMainStepFilterValue(maybeSuffix)
  if (!suffix) return null

  const prefix =
    maybePrefix === undefined || maybePrefix === null || maybePrefix === ""
      ? "*"
      : maybePrefix === "*"
        ? "*"
        : String(maybePrefix).trim()

  return { suffix, prefix }
}

function parseMainStepParts(value) {
  const normalized = normalizeMainStep(value) ?? ""
  const suffix = extractMainStepSuffix(normalized)
  const prefix = suffix ? normalized.slice(0, normalized.length - suffix.length) : ""
  const numericSource = suffix ?? normalized
  const number = Number.parseInt(numericSource, 10)
  return {
    prefix: prefix || "",
    number: Number.isFinite(number) ? number : Number.POSITIVE_INFINITY,
    raw: normalized,
    suffix,
  }
}

export function compareMainStepOptions(a, b) {
  const left = parseMainStepParts(a.value)
  const right = parseMainStepParts(b.value)

  if (left.number !== right.number) {
    return left.number - right.number
  }

  const prefixCompare = left.prefix.localeCompare(right.prefix, undefined, { sensitivity: "base" })
  if (prefixCompare !== 0) return prefixCompare

  return a.label.localeCompare(b.label, undefined, { sensitivity: "base" })
}

export function buildMainStepOptionLabel(value, _prefixes, _hasSuffix) {
  return value
}

export function sanitizeMainStepFilters(values, section, preserveMissing = false) {
  const normalizedArray = Array.isArray(values)
    ? values
    : values === null || values === undefined
      ? []
      : [values]

  const options = Array.isArray(section?.options) ? section.options : []
  const optionValues = options.map((option) => option.value)
  const optionSet = new Set(optionValues)
  const availablePrefixes = new Map(
    options.map((option) => [option.value, new Set(option.prefixes ?? [])]),
  )
  const resolved = []

  normalizedArray.forEach((value) => {
    const parsed = parseMainStepToken(value)
    if (!parsed?.suffix) return

    const suffixAllowed = optionSet.size === 0 || optionSet.has(parsed.suffix) || preserveMissing
    if (!suffixAllowed) return

    const prefixSet = availablePrefixes.get(parsed.suffix) ?? new Set()
    const hasPrefix = parsed.prefix && parsed.prefix !== "*"
    const prefixAllowed =
      !hasPrefix || prefixSet.size === 0 || prefixSet.has(parsed.prefix) || preserveMissing

    if (prefixAllowed) {
      const token = buildMainStepToken(parsed.suffix, hasPrefix ? parsed.prefix : "*")
      if (token) resolved.push(token)
    }
  })

  return Array.from(new Set(resolved))
}
