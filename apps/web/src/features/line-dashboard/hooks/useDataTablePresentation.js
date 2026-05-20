// src/features/line-dashboard/hooks/useDataTablePresentation.js
import * as React from "react"

import { timeFormatter } from "../utils/dataTableConstants"

function stableStringify(value) {
  if (value == null) return ""
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`
  if (typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${key}:${stableStringify(value[key])}`)
      .join("|")}}`
  }
  return String(value)
}

/**
 * DataTable 렌더링에 필요한 파생 상태를 한 곳에서 계산합니다.
 * - 필터/정렬 변화 시 첫 페이지로 돌려보내고, 페이지 범위를 벗어나지 않도록 가드합니다.
 * - 로딩/새로고침 상태에 맞춰 마지막 업데이트 라벨을 관리합니다.
 * - 페이징/빈 상태/카운트 등 UI에서 바로 쓸 수 있는 값을 제공합니다.
 */
export function useDataTablePresentation({
  table,
  columns,
  rows,
  filteredRows,
  filters,
  filter,
  sorting,
  isLoadingRows,
  rowsError,
  setPagination,
}) {
  const visibleColumns = table.getVisibleLeafColumns()
  const emptyStateColSpan = Math.max(visibleColumns.length, 1)

  const totalLoaded = rows.length
  const filteredTotal = filteredRows.length
  const hasNoRows = !isLoadingRows && rowsError === null && columns.length === 0

  const pageCount = table.getPageCount()
  const currentPage = table.getState().pagination.pageIndex + 1
  const totalPages = Math.max(pageCount, 1)
  const currentPageSize = table.getRowModel().rows.length

  const isRefreshing = isLoadingRows && totalLoaded > 0
  const isInitialLoading = isLoadingRows && totalLoaded === 0

  const pageResetKey = React.useMemo(
    () => stableStringify({ filter, filters, sorting }),
    [filter, filters, sorting]
  )
  const previousPageResetKeyRef = React.useRef(pageResetKey)

  // 필터/정렬이 바뀌면 첫 페이지로 이동해 사용자 혼란을 방지합니다.
  React.useEffect(() => {
    if (previousPageResetKeyRef.current === pageResetKey) return
    previousPageResetKeyRef.current = pageResetKey

    setPagination((previous) =>
      previous.pageIndex === 0 ? previous : { ...previous, pageIndex: 0 }
    )
  }, [pageResetKey, setPagination])

  // 현재 페이지가 전체 페이지 수를 넘어가지 않도록 방어합니다.
  React.useEffect(() => {
    const maxIndex = Math.max(pageCount - 1, 0)
    setPagination((previous) =>
      previous.pageIndex > maxIndex ? { ...previous, pageIndex: maxIndex } : previous
    )
  }, [pageCount, setPagination])

  const [lastUpdatedLabel, setLastUpdatedLabel] = React.useState(null)

  // 새로고침 중이면 "Updating…"을 보여주고, 완료되면 현재 시간을 라벨로 남깁니다.
  React.useEffect(() => {
    if (isRefreshing) {
      setLastUpdatedLabel("Updating…")
      return
    }
    if (!isLoadingRows) {
      setLastUpdatedLabel(timeFormatter.format(new Date()))
    }
  }, [isLoadingRows, isRefreshing])

  return {
    visibleColumns,
    emptyStateColSpan,
    totalLoaded,
    filteredTotal,
    hasNoRows,
    pageCount,
    currentPage,
    totalPages,
    currentPageSize,
    isRefreshing,
    isInitialLoading,
    lastUpdatedLabel,
  }
}
