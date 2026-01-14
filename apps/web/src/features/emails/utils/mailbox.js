export const SENT_MAILBOX_ID = "__sent__"
export const SENT_MAILBOX_LABEL = "Sent"
export const UNASSIGNED_MAILBOX_ID = "UNASSIGNED"
export const UNASSIGNED_MAILBOX_LABEL = "미분류"
export const LEGACY_UNASSIGNED_MAILBOX_ID = "rp-unclassified"

export function normalizeMailbox(value) {
  return typeof value === "string" ? value.trim() : ""
}

export function getMailboxFromSearchParams(searchParams) {
  if (!searchParams) return ""

  return normalizeMailbox(
    searchParams.get("user_sdwt_prod") ||
      searchParams.get("userSdwtProd") ||
      searchParams.get("mailbox") ||
      "",
  )
}

export function buildMailboxUrl(mailbox) {
  const trimmed = normalizeMailbox(mailbox)
  if (!trimmed) return "/emails/inbox"
  return `/emails/inbox?user_sdwt_prod=${encodeURIComponent(trimmed)}`
}

export function buildSentUrl() {
  return "/emails/sent"
}

export function buildMembersUrl(mailbox) {
  const trimmed = normalizeMailbox(mailbox)
  if (!trimmed) return "/emails/members"
  return `/emails/members?user_sdwt_prod=${encodeURIComponent(trimmed)}`
}

export function isSentMailbox(value) {
  return normalizeMailbox(value) === SENT_MAILBOX_ID
}

export function isUnassignedMailbox(value) {
  const normalized = normalizeMailbox(value)
  return normalized === UNASSIGNED_MAILBOX_ID || normalized === LEGACY_UNASSIGNED_MAILBOX_ID
}

export function getMailboxLabel(value) {
  const normalized = normalizeMailbox(value)
  if (!normalized) return ""
  if (isSentMailbox(normalized)) return SENT_MAILBOX_LABEL
  if (isUnassignedMailbox(normalized)) return UNASSIGNED_MAILBOX_LABEL
  return normalized
}

export function resolveUnassignedMailboxId(mailboxes = []) {
  const safeMailboxes = Array.isArray(mailboxes) ? mailboxes : []
  const normalized = safeMailboxes.map(normalizeMailbox).filter(Boolean)
  return normalized.find((mailbox) => isUnassignedMailbox(mailbox)) || ""
}
