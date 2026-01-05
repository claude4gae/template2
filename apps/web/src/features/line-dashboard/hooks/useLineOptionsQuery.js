// 파일 경로: src/features/line-dashboard/hooks/useLineOptionsQuery.js
// 라인 선택 드롭다운에서 사용할 옵션을 React Query로 관리합니다.
// - account/lineSdwtOptions 응답을 기반으로 line 목록만 추출합니다.

import { useQuery } from "@tanstack/react-query"

import { lineDashboardQueryKeys } from "../api/queryKeys"
import { getLineSdwtOptions } from "../api/getLineSdwtOptions"

function toLineOptions(payload) {
  const rawLines = Array.isArray(payload?.lines) ? payload.lines : []
  const normalized = rawLines
    .map((line) => (typeof line?.lineId === "string" ? line.lineId.trim() : ""))
    .filter(Boolean)

  return Array.from(new Set(normalized))
}

function normalizeUserSdwtProd(value) {
  if (value === null || value === undefined) return ""
  return typeof value === "string" ? value.trim() : String(value).trim()
}

function buildPreferredLineIds(rawLines, preferredUserSdwtProd) {
  const normalizedUserSdwt = normalizeUserSdwtProd(preferredUserSdwtProd)
  if (!normalizedUserSdwt) return []

  return rawLines
    .filter((line) => Array.isArray(line?.userSdwtProds) && line.userSdwtProds.includes(normalizedUserSdwt))
    .map((line) => (typeof line?.lineId === "string" ? line.lineId.trim() : ""))
    .filter(Boolean)
}

function toPreferredLineOptions(payload, preferredUserSdwtProd) {
  const rawLines = Array.isArray(payload?.lines) ? payload.lines : []
  const allLineIds = toLineOptions(payload)
  const preferredLineIds = buildPreferredLineIds(rawLines, preferredUserSdwtProd)

  const seen = new Set()
  const ordered = []

  preferredLineIds.forEach((lineId) => {
    if (!seen.has(lineId)) {
      seen.add(lineId)
      ordered.push(lineId)
    }
  })

  allLineIds.forEach((lineId) => {
    if (!seen.has(lineId)) {
      seen.add(lineId)
      ordered.push(lineId)
    }
  })

  return ordered
}

export function useLineOptionsQuery(options = {}) {
  const { enabled = true, preferredUserSdwtProd } = options

  return useQuery({
    queryKey: lineDashboardQueryKeys.lineSdwtOptions(),
    queryFn: getLineSdwtOptions,
    select: (payload) => toPreferredLineOptions(payload, preferredUserSdwtProd),
    // 탭으로 돌아올 때 홈 진입 페이지가 "새로고침"처럼 보이지 않도록
    // 포커스 시 자동 refetch를 비활성화합니다.
    refetchOnWindowFocus: false,
    enabled,
  })
}
