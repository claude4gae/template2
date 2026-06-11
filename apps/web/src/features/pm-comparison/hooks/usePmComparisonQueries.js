// 파일 경로: src/features/pm-comparison/hooks/usePmComparisonQueries.js
// PM SPIDER 서버 데이터 조회 훅입니다.
import { useQueries, useQuery } from "@tanstack/react-query"

import {
  fetchPmComparisonMeta,
  fetchPmComparisonResult,
  pmComparisonQueryKeys,
} from "../api"
import {
  PM_SPIDER_CATEGORIES,
  buildPmSpiderPatternPayloads,
} from "../utils/format"

function buildPayloadKey(payload) {
  if (!payload) return "empty"
  return JSON.stringify(payload)
}

function withRefPmDates(payload, refPmDates) {
  if (!payload || refPmDates === null || refPmDates === undefined) return payload
  return {
    ...payload,
    refPmDates,
  }
}

export function usePmComparisonMeta() {
  return useQuery({
    queryKey: pmComparisonQueryKeys.meta(),
    queryFn: fetchPmComparisonMeta,
    retry: false,
  })
}

export function usePmComparisonResult(payload) {
  const payloadKey = buildPayloadKey(payload)
  return useQuery({
    queryKey: pmComparisonQueryKeys.result(payloadKey),
    queryFn: () => fetchPmComparisonResult(payload),
    enabled: Boolean(payload),
    retry: false,
  })
}

export function usePmSpiderCategoryResults(payload, refPmDates = null) {
  const patternPayloads = buildPmSpiderPatternPayloads(withRefPmDates(payload, refPmDates))
  const queries = useQueries({
    queries: patternPayloads.map(({ pattern, payload: categoryPayload }) => ({
      queryKey: pmComparisonQueryKeys.category(pattern, buildPayloadKey(categoryPayload)),
      queryFn: () => fetchPmComparisonResult(categoryPayload),
      enabled: Boolean(payload),
      retry: false,
    })),
  })
  const dataByPattern = Object.fromEntries(
    patternPayloads.map(({ pattern }, index) => [pattern, queries[index]?.data]),
  )
  const queryByPattern = Object.fromEntries(
    patternPayloads.map(({ pattern }, index) => [pattern, queries[index]]),
  )
  const categories = PM_SPIDER_CATEGORIES.map((category) => {
    const data = dataByPattern[category.pattern]
    const query = queryByPattern[category.pattern]
    const source = category.kind === "trace" ? data?.trace : data?.oes
    const rows = Array.isArray(source?.summaryRows) ? source.summaryRows : []
    const stepRows = Array.isArray(source?.stepRows) ? source.stepRows : []
    return {
      ...category,
      payload: patternPayloads.find((item) => item.pattern === category.pattern)?.payload,
      data,
      source,
      rows,
      stepRows,
      topRows: rows.slice(0, 5),
      rowCount: Number(source?.rowCount || 0),
      fileCount: Number(source?.fileCount || 0),
      warnings: Array.isArray(data?.warnings) ? data.warnings : [],
      isFetching: Boolean(query?.isFetching),
      isLoading: Boolean(query?.isFetching && !query?.data),
    }
  })

  return {
    categories,
    isFetching: queries.some((query) => query.isFetching),
    isLoading: Boolean(payload) && queries.some((query) => query.isFetching && !query.data),
    error: queries.find((query) => query.error)?.error,
    refetch: () => {
      queries.forEach((query) => query.refetch())
    },
  }
}

function getRowItemKey(category, row) {
  if (!row) return ""
  if (category?.kind === "trace") {
    return row.traceSensor || row.traceParamName || row.itemName || ""
  }
  return `${row.step || ""}:${row.wavelength || ""}`
}

export function usePmSpiderDetailResult(category, row, refPmDates = null) {
  const itemKey = getRowItemKey(category, row)
  let payload = null
  if (category?.payload && row && itemKey) {
    payload = {
      ...withRefPmDates(category.payload, refPmDates),
      traceParamNames: category.kind === "trace" ? [itemKey] : [],
      selectedStep: category.kind === "oes" ? row.step || "" : "",
      selectedWavelength: category.kind === "oes" ? String(row.wavelength || "") : "",
    }
  }
  const payloadKey = buildPayloadKey(payload)

  return useQuery({
    queryKey: pmComparisonQueryKeys.detail(category?.id || "empty", itemKey || "empty", payloadKey),
    queryFn: () => fetchPmComparisonResult(payload),
    enabled: Boolean(payload),
    retry: false,
  })
}
