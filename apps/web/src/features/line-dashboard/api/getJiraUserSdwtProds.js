// 파일 경로: src/features/line-dashboard/api/getJiraUserSdwtProds.js
// Jira 템플릿에 등록된 user_sdwt_prod 목록을 가져오는 API 래퍼입니다.
import { buildBackendUrl, safeParseJson } from "@/lib/api"

export async function getJiraUserSdwtProds() {
  const endpoint = buildBackendUrl("/api/v1/line-dashboard/jira-user-sdwt-prods")

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5_000)

  let response

  try {
    response = await fetch(endpoint, { credentials: "include", signal: controller.signal })
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Timed out while loading Jira user SDWT prods")
    }

    throw error
  } finally {
    clearTimeout(timeoutId)
  }

  const payload = await safeParseJson(response)
  if (!response.ok) {
    const message =
      typeof payload?.error === "string"
        ? payload.error
        : `Failed to load Jira user SDWT prods (${response.status})`
    throw new Error(message)
  }

  const rawValues = Array.isArray(payload?.userSdwtProds) ? payload.userSdwtProds : []
  const normalized = rawValues
    .filter((value) => typeof value === "string" && value.trim().length > 0)
    .map((value) => value.trim())

  return Array.from(new Set(normalized)).sort()
}
