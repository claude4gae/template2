// 파일 경로: src/features/line-dashboard/api/lineJiraKey.js
// user_sdwt_prod 기반 Jira project key 조회/저장 API 래퍼
import { buildBackendUrl, safeParseJson } from "@/lib/api"

import { buildApiError } from "./apiError"

export async function fetchUserSdwtJiraKey(userSdwtProd) {
  if (!userSdwtProd) {
    return { jiraKey: "" }
  }

  const endpoint = buildBackendUrl("/api/v1/account/affiliation/jira-key", { userSdwtProd })
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

export async function updateUserSdwtJiraKey({ userSdwtProd, jiraKey }) {
  const endpoint = buildBackendUrl("/api/v1/account/affiliation/jira-key")
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
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
