// src/features/line-dashboard/components/DataTablePagination.jsx
import {
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
} from "@tabler/icons-react"

import { Button } from "components/ui/button"

/**
 * 테이블 하단의 요약/페이지네이션 UI를 분리한 컴포넌트입니다.
 * - 상위(DataTable)는 계산된 값만 넘기고, 여기서는 버튼/라벨만 그립니다.
 */
export function DataTablePagination({
  labels,
  numberFormatter,
  table,
  currentPage,
  totalPages,
  currentPageSize,
  filteredTotal,
  totalLoaded,
  pagination,
  pageSizeOptions = [15, 25, 30, 40, 50],
}) {
  return (
    <div className="flex mt-2 flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span aria-live="polite">
          {labels.showing} {numberFormatter.format(currentPageSize)} {labels.rows}
          {" of "} {numberFormatter.format(filteredTotal)} {labels.rows}
          {filteredTotal !== totalLoaded
            ? `${labels.filteredFrom}${numberFormatter.format(totalLoaded)}${labels.filteredFromSuffix}`
            : ""}
        </span>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
            aria-label={labels.goFirst}
            title={labels.goFirst}
          >
            <IconChevronsLeft className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            aria-label={labels.goPrev}
            title={labels.goPrev}
          >
            <IconChevronLeft className="size-4" />
          </Button>
          <span className="px-2 text-xs text-muted-foreground" aria-live="polite">
            {labels.page} {numberFormatter.format(currentPage)} {labels.of} {numberFormatter.format(totalPages)}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            aria-label={labels.goNext}
            title={labels.goNext}
          >
            <IconChevronRight className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.setPageIndex(totalPages - 1)}
            disabled={!table.getCanNextPage()}
            aria-label={labels.goLast}
            title={labels.goLast}
          >
            <IconChevronsRight className="size-4" />
          </Button>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <span className="text-xs text-muted-foreground">{labels.rowsPerPage}</span>
          <select
            value={pagination.pageSize}
            onChange={(event) => table.setPageSize(Number(event.target.value))}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
            aria-label={labels.rowsPerPage}
            title={labels.rowsPerPage}
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
