// VOC API 래퍼
import { buildBackendUrl, safeParseJson } from "@/lib/api"

import { DEFAULT_APP_CATEGORY } from "../utils/constants"

function buildApiError(response, payload, fallbackMessage) {
  const apiMessage =
    payload && typeof payload === "object" && typeof payload.error === "string"
      ? payload.error
      : ""
  const message = apiMessage || fallbackMessage
  const error = new Error(message)
  error.status = response.status
  return error
}

function normalizeAuthor(raw) {
  if (!raw || typeof raw !== "object") return null
  const nameCandidate =
    (typeof raw.name === "string" && raw.name.trim()) ||
    (typeof raw.username === "string" && raw.username.trim()) ||
    (typeof raw.usr_id === "string" && raw.usr_id.trim()) ||
    (typeof raw.email === "string" && raw.email.trim()) ||
    ""

  const payload = {
    id: raw.id ?? raw.usr_id ?? null,
    name: nameCandidate || "알 수 없음",
  }
  if (typeof raw.email === "string" && raw.email.trim()) {
    payload.email = raw.email
  }
  return payload
}

function normalizeReply(raw) {
  if (!raw || typeof raw !== "object") return null
  const id = raw.id ?? raw.pk ?? null
  if (id === null) return null

  const createdAt =
    (typeof raw.createdAt === "string" && raw.createdAt) ||
    (typeof raw.created_at === "string" && raw.created_at) ||
    ""

  return {
    id,
    postId: raw.postId ?? raw.post_id ?? null,
    content: typeof raw.content === "string" ? raw.content : "",
    createdAt,
    author: normalizeAuthor(raw.author),
  }
}

function normalizePost(raw) {
  if (!raw || typeof raw !== "object") return null
  const id = raw.id ?? raw.pk ?? null
  if (id === null) return null

  const replies = Array.isArray(raw.replies)
    ? raw.replies.map(normalizeReply).filter(Boolean)
    : []

  const createdAt =
    (typeof raw.createdAt === "string" && raw.createdAt) ||
    (typeof raw.created_at === "string" && raw.created_at) ||
    ""

  const updatedAt =
    (typeof raw.updatedAt === "string" && raw.updatedAt) ||
    (typeof raw.updated_at === "string" && raw.updated_at) ||
    createdAt
  const appValue = typeof raw.app === "string" ? raw.app.trim() : ""

  return {
    id,
    title: typeof raw.title === "string" ? raw.title : "",
    content: typeof raw.content === "string" ? raw.content : "",
    status: typeof raw.status === "string" ? raw.status : "",
    app: appValue || DEFAULT_APP_CATEGORY,
    createdAt,
    updatedAt,
    author: normalizeAuthor(raw.author),
    replies,
  }
}

export async function fetchVocPosts() {
  const endpoint = buildBackendUrl("/api/v1/voc/posts")
  const response = await fetch(endpoint, {
    cache: "no-store",
    credentials: "include",
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(
      response,
      payload,
      `Failed to load posts (status ${response.status})`,
    )
  }

  const posts = Array.isArray(payload?.results)
    ? payload.results.map(normalizePost).filter(Boolean)
    : []
  const statusCounts =
    payload && typeof payload.statusCounts === "object" ? payload.statusCounts : undefined

  return { posts, statusCounts }
}

export async function createVocPost({ title, content, status, app }) {
  const endpoint = buildBackendUrl("/api/v1/voc/posts")
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      title,
      content,
      ...(status ? { status } : {}),
      ...(app ? { app } : {}),
    }),
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(response, payload, "Failed to create post")
  }

  return {
    post: normalizePost(payload?.post),
    statusCounts:
      payload && typeof payload.statusCounts === "object" ? payload.statusCounts : undefined,
  }
}

export async function updateVocPost(postId, updates = {}) {
  const endpoint = buildBackendUrl(`/api/v1/voc/posts/${postId}`)
  const body = {}
  if ("title" in updates) body.title = updates.title
  if ("content" in updates) body.content = updates.content
  if ("status" in updates) body.status = updates.status
  if ("app" in updates) body.app = updates.app

  const response = await fetch(endpoint, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(response, payload, "Failed to update post")
  }

  return {
    post: normalizePost(payload?.post),
    statusCounts:
      payload && typeof payload.statusCounts === "object" ? payload.statusCounts : undefined,
  }
}

export async function deleteVocPost(postId) {
  const endpoint = buildBackendUrl(`/api/v1/voc/posts/${postId}`)
  const response = await fetch(endpoint, {
    method: "DELETE",
    credentials: "include",
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(response, payload, "Failed to delete post")
  }

  return {
    success: true,
    statusCounts:
      payload && typeof payload.statusCounts === "object" ? payload.statusCounts : undefined,
  }
}

export async function createVocReply({ postId, content }) {
  const endpoint = buildBackendUrl(`/api/v1/voc/posts/${postId}/replies`)
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ content }),
  })
  const payload = await safeParseJson(response)

  if (!response.ok) {
    throw buildApiError(response, payload, "Failed to add reply")
  }

  return {
    reply: normalizeReply(payload?.reply),
    post: normalizePost(payload?.post),
  }
}
