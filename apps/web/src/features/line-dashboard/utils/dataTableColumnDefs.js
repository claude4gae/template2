// src/features/line-dashboard/utils/dataTableColumnDefs.js
import { mergeConfig } from "./dataTableColumnConfig"
import { renderCellByKey } from "../components/DataTableColumnRenderers"
import { renderMetroStepFlow } from "./dataTableFormatters"
import { STEP_COLUMN_KEY_SET } from "./dataTableConstants"

const ALIGNMENT_VALUES = new Set(["left", "center", "right"])
const DEFAULT_MIN_WIDTH = 50
const DEFAULT_WIDTH = 140

function normalizeAlignment(value, fallback = "left") {
  if (typeof value !== "string") return fallback
  const lowered = value.toLowerCase()
  return ALIGNMENT_VALUES.has(lowered) ? lowered : fallback
}

function inferDefaultAlignment(colKey, sampleValue) {
  if (typeof sampleValue === "number") return "right"
  if (isNumeric(sampleValue)) return "right"
  if (colKey && /(_?id|count|qty|amount|number)$/i.test(colKey)) return "right"
  return "left"
}

function resolveAlignment(colKey, config, sampleValue) {
  const inferred = inferDefaultAlignment(colKey, sampleValue)
  const cellAlignment = normalizeAlignment(config.cellAlign?.[colKey], inferred)
  const headerAlignment = normalizeAlignment(config.headerAlign?.[colKey], cellAlignment)
  return { cell: cellAlignment, header: headerAlignment }
}

function resolveColumnSize(colKey, config) {
  const configuredWidth = Number(config.width?.[colKey])
  const size =
    Number.isFinite(configuredWidth) && configuredWidth > 0
      ? configuredWidth
      : DEFAULT_WIDTH

  return { size, minSize: DEFAULT_MIN_WIDTH, maxSize: Number.MAX_SAFE_INTEGER }
}

function isNumeric(value) {
  if (value == null || value === "") return false
  const numeric = Number(value)
  return Number.isFinite(numeric)
}

function tryDate(value) {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value === "string") {
    const timestamp = Date.parse(value)
    return Number.isNaN(timestamp) ? null : new Date(timestamp)
  }
  return null
}

function cmpText(a, b) {
  const left = a == null ? "" : String(a)
  const right = b == null ? "" : String(b)
  return left.localeCompare(right)
}

function cmpNumber(a, b) {
  const left = Number(a)
  const right = Number(b)
  if (!Number.isFinite(left) && !Number.isFinite(right)) return 0
  if (!Number.isFinite(left)) return -1
  if (!Number.isFinite(right)) return 1
  return left - right
}

function cmpDate(a, b) {
  const left = tryDate(a)
  const right = tryDate(b)
  if (!left && !right) return 0
  if (!left) return -1
  if (!right) return 1
  return left.getTime() - right.getTime()
}

function autoSortType(sample) {
  if (sample == null) return "text"
  if (isNumeric(sample)) return "number"
  if (tryDate(sample)) return "datetime"
  return "text"
}

function getSortingFnForKey(colKey, config, sampleValue) {
  const requestedType = config.sortTypes?.[colKey] ?? "auto"
  const sortType = requestedType === "auto" ? autoSortType(sampleValue) : requestedType

  if (sortType === "number") {
    return (rowA, rowB) => cmpNumber(rowA.getValue(colKey), rowB.getValue(colKey))
  }

  if (sortType === "datetime") {
    return (rowA, rowB) => cmpDate(rowA.getValue(colKey), rowB.getValue(colKey))
  }

  return (rowA, rowB) => cmpText(rowA.getValue(colKey), rowB.getValue(colKey))
}

function pickStepColumnsWithIndex(columns) {
  return columns
    .map((key, index) => ({ key, index }))
    .filter(({ key }) => STEP_COLUMN_KEY_SET.has(key))
}

function shouldCombineSteps(stepCols) {
  if (!stepCols.length) return false
  return (
    stepCols.some(({ key }) => key === "main_step") ||
    stepCols.some(({ key }) => key === "metro_steps")
  )
}

function getSampleValueForColumns(row, columns) {
  if (!row || typeof row !== "object" || !Array.isArray(columns)) return undefined
  for (const { key } of columns) {
    if (row[key] !== undefined) return row[key]
  }
  return undefined
}

function makeStepFlowColumn(stepCols, label, config, firstRow) {
  const sample = getSampleValueForColumns(firstRow, stepCols)
  const alignment = resolveAlignment("process_flow", config, sample)
  const { size, minSize, maxSize } = resolveColumnSize("process_flow", config)

  return {
    id: "process_flow",
    header: () => label,
    accessorFn: (row) => row?.["main_step"] ?? row?.["metro_steps"] ?? null,
    cell: (info) => renderMetroStepFlow(info.row.original),
    enableSorting: false,
    meta: { isEditable: false, alignment },
    size,
    minSize,
    maxSize,
  }
}

// 단일 컬럼 정의 객체를 생성합니다.
function makeColumnDef(colKey, config, sampleValueFromFirstRow) {
  const label = config.labels?.[colKey] ?? colKey
  const enableSorting =
    typeof config.sortable?.[colKey] === "boolean"
      ? config.sortable[colKey]
      : colKey !== "defect_url" && colKey !== "jira_key"

  const sortingFn = enableSorting
    ? getSortingFnForKey(colKey, config, sampleValueFromFirstRow)
    : undefined

  const { size, minSize, maxSize } = resolveColumnSize(colKey, config)
  const alignment = resolveAlignment(colKey, config, sampleValueFromFirstRow)

  return {
    id: colKey,
    header: () => label,
    accessorFn: (row) => row?.[colKey],
    meta: {
      isEditable: colKey === "comment" || colKey === "needtosend",
      alignment,
    },
    cell: (info) => renderCellByKey(colKey, info),
    enableSorting,
    sortingFn,
    size,
    minSize,
    maxSize,
  }
}

// 데이터 테이블에서 사용할 전체 컬럼 정의 배열을 생성합니다.
export function createColumnDefs(rawColumns, userConfig, firstRowForTypeGuess) {
  const config = mergeConfig(userConfig)
  const columns = Array.isArray(rawColumns) ? rawColumns : []

  const stepCols = pickStepColumnsWithIndex(columns)
  const combineSteps = shouldCombineSteps(stepCols)

  const stepKeySet = new Set(stepCols.map(({ key }) => key))
  const baseKeys = combineSteps ? columns.filter((key) => !stepKeySet.has(key)) : [...columns]

  const defs = baseKeys.map((key) => {
    const sample = firstRowForTypeGuess ? firstRowForTypeGuess?.[key] : undefined
    return makeColumnDef(key, config, sample)
  })

  if (combineSteps) {
    const headerText = config.labels?.process_flow ?? config.processFlowHeader ?? "process_flow"
    const stepFlowCol = makeStepFlowColumn(stepCols, headerText, config, firstRowForTypeGuess)

    const insertionIndex = stepCols.length
      ? Math.min(...stepCols.map(({ index }) => index))
      : defs.length

    defs.splice(Math.min(Math.max(insertionIndex, 0), defs.length), 0, stepFlowCol)
  }

  const order = Array.isArray(config.order) ? config.order : null
  if (order && order.length > 0) {
    const idSet = new Set(defs.map((d) => d.id))
    const head = order.filter((id) => idSet.has(id))
    const tail = defs.map((d) => d.id).filter((id) => !head.includes(id))
    const finalIds = [...head, ...tail]

    finalIds.forEach((id, i) => {
      const idx = defs.findIndex((d) => d.id === id)
      if (idx !== -1 && idx !== i) {
        const [moved] = defs.splice(idx, 1)
        defs.splice(i, 0, moved)
      }
    })
  }

  return defs
}
