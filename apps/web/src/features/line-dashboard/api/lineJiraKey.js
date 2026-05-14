// 파일 경로: src/features/line-dashboard/api/lineJiraKey.js
// 알림 target 기반 Jira project key 조회/저장 API 래퍼
import { buildBackendUrl, safeParseJson } from "@/lib/api"

import { buildApiError } from "./apiError"

const DEFAULT_CHANNEL_ENABLED = {
  jira: true,
  messenger: true,
  mail: true,
}
const DEFAULT_NEED_TO_SEND_RULE = {
  commentKeyword: "",
  enabled: false,
  ignoreSampleType: false,
}
const DEFAULT_MESSENGER_FORCE_NEW_CHATROOM = false

function normalizeChannelEnabled(payload) {
  return {
    jira: typeof payload?.jiraEnabled === "boolean" ? payload.jiraEnabled : DEFAULT_CHANNEL_ENABLED.jira,
    messenger:
      typeof payload?.messengerEnabled === "boolean"
        ? payload.messengerEnabled
        : DEFAULT_CHANNEL_ENABLED.messenger,
    mail: typeof payload?.mailEnabled === "boolean" ? payload.mailEnabled : DEFAULT_CHANNEL_ENABLED.mail,
  }
}

function normalizeNeedToSendRule(payload) {
  return {
    commentKeyword:
      typeof payload?.needtosendCommentLastAt === "string" ? payload.needtosendCommentLastAt : "",
    enabled:
      typeof payload?.needtosendEnabled === "boolean"
        ? payload.needtosendEnabled
        : DEFAULT_NEED_TO_SEND_RULE.enabled,
    ignoreSampleType:
      typeof payload?.needtosendIgnoreSampleType === "boolean"
        ? payload.needtosendIgnoreSampleType
        : DEFAULT_NEED_TO_SEND_RULE.ignoreSampleType,
  }
}

export async function fetchUserSdwtJiraKey(userSdwtProd) {
  if (!userSdwtProd) {
    return {
      jiraKey: "",
      channelEnabled: DEFAULT_CHANNEL_ENABLED,
      needToSendRule: DEFAULT_NEED_TO_SEND_RULE,
      messengerForceNewChatroom: DEFAULT_MESSENGER_FORCE_NEW_CHATROOM,
    }
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

  return {
    jiraKey: typeof payload?.jiraKey === "string" ? payload.jiraKey : "",
    channelEnabled: normalizeChannelEnabled(payload),
    needToSendRule: normalizeNeedToSendRule(payload),
    messengerForceNewChatroom:
      typeof payload?.messengerForceNewChatroom === "boolean"
        ? payload.messengerForceNewChatroom
        : DEFAULT_MESSENGER_FORCE_NEW_CHATROOM,
  }
}

export async function updateUserSdwtJiraKey(options) {
  const { lineId, userSdwtProd, channelEnabled, needToSendRule } = options
  const endpoint = buildBackendUrl("/api/v1/line-dashboard/jira-keys")
  const requestBody = {
    lineId,
    targetUserSdwtProd: userSdwtProd,
    userSdwtProd,
  }
  if (Object.prototype.hasOwnProperty.call(options, "jiraKey")) {
    requestBody.jiraKey = typeof options.jiraKey === "string" ? options.jiraKey : ""
  }
  if (channelEnabled) {
    requestBody.jiraEnabled = Boolean(channelEnabled.jira)
    requestBody.messengerEnabled = Boolean(channelEnabled.messenger)
    requestBody.mailEnabled = Boolean(channelEnabled.mail)
  }
  if (needToSendRule) {
    requestBody.needtosendCommentLastAt =
      typeof needToSendRule.commentKeyword === "string" ? needToSendRule.commentKeyword : ""
    requestBody.needtosendEnabled = Boolean(needToSendRule.enabled)
    requestBody.needtosendIgnoreSampleType = Boolean(needToSendRule.ignoreSampleType)
  }
  if (Object.prototype.hasOwnProperty.call(options, "messengerForceNewChatroom")) {
    requestBody.messengerForceNewChatroom = Boolean(options.messengerForceNewChatroom)
  }
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(requestBody),
  })

  const payload = await safeParseJson(response)
  if (!response.ok) {
    throw buildApiError(
      response,
      payload,
      `Failed to update Jira key (status ${response.status})`,
    )
  }

  return {
    jiraKey: typeof payload?.jiraKey === "string" ? payload.jiraKey : "",
    channelEnabled: normalizeChannelEnabled(payload),
    needToSendRule: normalizeNeedToSendRule(payload),
    messengerForceNewChatroom:
      typeof payload?.messengerForceNewChatroom === "boolean"
        ? payload.messengerForceNewChatroom
        : DEFAULT_MESSENGER_FORCE_NEW_CHATROOM,
  }
}
