// 파일 경로: src/features/line-dashboard/api/lineJiraKey.js
// 알림 target 기반 Jira project key 조회/저장 API 래퍼
import { buildBackendUrl, safeParseJson } from "@/lib/api"

import { buildApiError } from "./apiError"

export async function fetchUserSdwtJiraKey(userSdwtProd) {
  if (!userSdwtProd) {
    return { jiraKey: "" }
  }

  const endpoint = buildBackendUrl("/api/v1/line-dashboard/jira-keys", { targetUserSdwtProd: userSdwtProd })
  const response = await fetch(endpoint, {
    cache: "no-store",
    credentials: "include",
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(
      response,
      payload,
      `Failed to load Jira key (status ${response.status})`,
    )
  }

  return { jiraKey: typeof payload?.jiraKey === "string" ? payload.jiraKey : "" }
}

export async function updateUserSdwtJiraKey({ lineId, userSdwtProd, jiraKey }) {
  const endpoint = buildBackendUrl("/api/v1/line-dashboard/jira-keys")
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      lineId,
      targetUserSdwtProd: userSdwtProd,
      userSdwtProd,
      jiraKey: typeof jiraKey === "string" ? jiraKey : "",
    }),
  })

  const payload = await safeParseJson(response)
  if (!response.ok) {
    throw buildApiError(
      response,
      payload,
      `Failed to update Jira key (status ${response.status})`,
    )
  }

  return { jiraKey: typeof payload?.jiraKey === "string" ? payload.jiraKey : "" }
}
