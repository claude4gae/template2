const SENT_MAILBOX_ID = "__sent__"

function normalizeValue(value) {
  return typeof value === "string" ? value.trim() : ""
}

function normalizeList(values) {
  if (!Array.isArray(values)) return []
  const normalized = values.map(normalizeValue).filter(Boolean)
  return Array.from(new Set(normalized))
}

function isMailboxAccessible(mailbox, availableMailboxes) {
  const normalizedMailbox = normalizeValue(mailbox)
  if (!normalizedMailbox || normalizedMailbox === SENT_MAILBOX_ID) return false

  const normalizedMailboxes = normalizeList(availableMailboxes)
  if (normalizedMailboxes.length === 0) return true
  return normalizedMailboxes.includes(normalizedMailbox)
}

export function buildEmailSourceUrl(emailId, userSdwtProd, options = {}) {
  const normalizedEmailId = normalizeValue(emailId)
  if (!normalizedEmailId) return "/emails/inbox"

  const availableMailboxes = options?.availableMailboxes
  const mailbox = normalizeValue(userSdwtProd)
  const canUseMailbox = mailbox && isMailboxAccessible(mailbox, availableMailboxes)
  const isExplicitSentMailbox = mailbox === SENT_MAILBOX_ID
  const params = new URLSearchParams()

  if (canUseMailbox) {
    params.set("user_sdwt_prod", mailbox)
  }

  params.set("emailId", normalizedEmailId)
  if (canUseMailbox || !isExplicitSentMailbox) {
    return `/emails/inbox?${params.toString()}`
  }
  return `/emails/sent?${params.toString()}`
}
