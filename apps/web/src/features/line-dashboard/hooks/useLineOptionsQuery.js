// 파일 경로: src/features/line-dashboard/hooks/useLineOptionsQuery.js
// 라인 선택 드롭다운에서 사용할 옵션을 React Query로 관리합니다.

import { useQuery } from "@tanstack/react-query"

import { lineDashboardQueryKeys } from "../api/queryKeys"
import { getDistinctLineIds } from "../api/getLineIds"

function toLineOptions(rawLineIds) {
  const normalized = (Array.isArray(rawLineIds) ? rawLineIds : [])
    .map((lineId) => (typeof lineId === "string" ? lineId.trim() : ""))
    .filter(Boolean)
  return Array.from(new Set(normalized)).sort()
}

export function useLineOptionsQuery(options = {}) {
  const { enabled = true } = options

  const lineOptionsQuery = useQuery({
    queryKey: lineDashboardQueryKeys.lineOptions(),
    queryFn: getDistinctLineIds,
    // 탭으로 돌아올 때 홈 진입 페이지가 새로고침처럼 보이지 않도록 포커스 refetch를 끕니다.
    refetchOnWindowFocus: false,
    enabled,
  })

  return {
    ...lineOptionsQuery,
    data: toLineOptions(lineOptionsQuery.data),
  }
}
