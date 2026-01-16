import { useParams } from "react-router-dom"

import { SidebarNavMain } from "@/components/layout/SidebarNavMain"
import {
  getStoredLineId,
  normalizeTeamId,
  useActiveLineOptional,
  useLineOptionsQuery,
} from "@/lib/affiliation"

function getFirstLineId(lineOptions) {
  if (!Array.isArray(lineOptions)) return null
  for (const value of lineOptions) {
    const lineId = normalizeTeamId(value)
    if (lineId) return lineId
  }
  return null
}

function hasLineScope(items) {
  if (!Array.isArray(items)) return false
  for (const item of items) {
    if (item?.scope === "line") return true
    if (Array.isArray(item?.items) && item.items.some((child) => child?.scope === "line")) {
      return true
    }
  }
  return false
}

function withLineScope(url, scope, lineId) {
  if (!url) return "#"
  const normalized = url.startsWith("/") ? url.replace(/^\/+/, "") : url
  const basePath = `/${normalized}`

  if (scope !== "line" || !lineId) return basePath

  const segments = normalized.split("/").filter(Boolean)
  if (!segments.length) return basePath

  const placeholderIndex = segments.findIndex((segment) => segment.startsWith(":"))
  if (placeholderIndex !== -1) {
    const next = [...segments]
    next[placeholderIndex] = lineId
    return `/${next.join("/")}`
  }

  if (segments[segments.length - 1] !== lineId) {
    segments.push(lineId)
  }
  return `/${segments.join("/")}`
}

function extractLineIdFromParams(params) {
  if (!params) return null
  const raw = params.lineId
  if (Array.isArray(raw)) return normalizeTeamId(raw[0])
  return normalizeTeamId(raw)
}

export function NavMain({ items }) {
  const params = useParams()
  const lineContext = useActiveLineOptional()
  const activeLineId = normalizeTeamId(lineContext?.lineId)
  const safeItems = Array.isArray(items) ? items : []

  const storedLineId = getStoredLineId()
  const paramLineId = extractLineIdFromParams(params)
  const shouldFetchLineOptions =
    hasLineScope(safeItems) && !paramLineId && !activeLineId && !storedLineId
  const { data: lineOptions = [] } = useLineOptionsQuery({ enabled: shouldFetchLineOptions })
  const fallbackLineId = getFirstLineId(lineOptions)

  const resolvedLineId =
    paramLineId ?? activeLineId ?? storedLineId ?? fallbackLineId ?? null

  const resolvedItems = safeItems.map((item) => {
    const next = { ...item, url: withLineScope(item.url, item.scope, resolvedLineId) }
    if (!Array.isArray(item.items)) return next

    return {
      ...next,
      items: item.items.map((sub) => ({
        ...sub,
        url: withLineScope(sub.url, sub.scope ?? item.scope, resolvedLineId),
      })),
    }
  })

  return <SidebarNavMain items={resolvedItems} label="" />
}
