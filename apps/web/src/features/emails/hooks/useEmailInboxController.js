import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { useBulkDeleteEmails, useDeleteEmail, useMoveEmails } from "./useEmailActions"
import { useEmailDetail, useEmailHtml } from "./useEmailDetail"
import { useEmailList } from "./useEmailList"
import { useEmailMailboxes } from "./useEmailMailboxes"
import { DEFAULT_EMAIL_PAGE_SIZE, EMAIL_PAGE_SIZE_OPTIONS } from "../utils/emailPagination"
import {
  getMailboxFromSearchParams,
  isSentMailbox,
  isUnassignedMailbox,
  normalizeMailbox,
  SENT_MAILBOX_ID,
} from "../utils/mailbox"

const INITIAL_FILTERS = {
  page: 1,
  pageSize: DEFAULT_EMAIL_PAGE_SIZE,
  q: "",
  sender: "",
  recipient: "",
  dateFrom: "",
  dateTo: "",
}

const MIN_LIST_WIDTH = 600
const MIN_DETAIL_WIDTH = 420
const DEFAULT_LIST_RATIO = 0.45
const GRID_GAP_PX = 16
const EMPTY_EMAILS = []
const EMPTY_MAILBOXES = []

function parseRoutedEmailId(value) {
  const normalized = typeof value === "string" ? value.trim() : ""
  if (!normalized) return null

  const numericValue = /^\d+$/.test(normalized) ? Number(normalized) : null
  if (Number.isSafeInteger(numericValue) && numericValue > 0) return numericValue

  const ragMatch = normalized.match(/^email-(\d+)$/i)
  if (!ragMatch) return null

  const ragEmailId = Number(ragMatch[1])
  return Number.isSafeInteger(ragEmailId) && ragEmailId > 0 ? ragEmailId : null
}

function clampListWidth(nextWidth, container) {
  if (!container) return nextWidth
  const { width } = container.getBoundingClientRect()
  if (!width) return nextWidth

  const maxWidth = Math.max(MIN_LIST_WIDTH, width - GRID_GAP_PX - MIN_DETAIL_WIDTH)
  return Math.min(Math.max(nextWidth, MIN_LIST_WIDTH), maxWidth)
}

function buildMoveTargets(mailboxes, activeMailbox) {
  const normalizedActive = normalizeMailbox(activeMailbox)
  const options = (Array.isArray(mailboxes) ? mailboxes : EMPTY_MAILBOXES)
    .map(normalizeMailbox)
    .filter(Boolean)
    .filter((mailbox) => !isSentMailbox(mailbox) && !isUnassignedMailbox(mailbox))
    .filter((mailbox) => mailbox !== normalizedActive)

  const unique = Array.from(new Set(options))
  return unique.map((mailbox) => ({ value: mailbox, label: mailbox }))
}

function useEmailListController({ scope, mailboxParam, searchParams, setSearchParams }) {
  const [filters, setFilters] = useState(INITIAL_FILTERS)
  const [selectedIds, setSelectedIds] = useState([])
  const [activeEmailId, setActiveEmailId] = useState(null)
  const [listWidth, setListWidth] = useState(420)
  const [isDragging, setIsDragging] = useState(false)
  const splitPaneRef = useRef(null)
  const dragCleanupRef = useRef(null)
  const mailboxChangeRef = useRef("")
  const mailboxInitializedRef = useRef(false)

  const normalizedMailbox = normalizeMailbox(mailboxParam)
  const listEnabled = scope === "sent" ? true : Boolean(normalizedMailbox)
  const listFilters = {
    ...filters,
    scope,
    userSdwtProd: scope === "sent" ? "" : normalizedMailbox,
  }

  const {
    data: listData,
    isLoading: isListLoading,
    isFetching: isListFetching,
    isError: isListError,
    error: listError,
    refetch,
  } = useEmailList(listFilters, { enabled: listEnabled })
  const emails = Array.isArray(listData?.results) ? listData.results : EMPTY_EMAILS

  const {
    data: detailData,
    isLoading: isDetailLoading,
  } = useEmailDetail(activeEmailId)
  const {
    data: htmlData,
    isLoading: isHtmlLoading,
  } = useEmailHtml(activeEmailId)

  const deleteMutation = useDeleteEmail()
  const bulkDeleteMutation = useBulkDeleteEmails()
  const moveMutation = useMoveEmails()

  const { data: mailboxData } = useEmailMailboxes()
  const mailboxes = Array.isArray(mailboxData?.results) ? mailboxData.results : EMPTY_MAILBOXES
  const moveTargets = buildMoveTargets(mailboxes, normalizedMailbox)
  const emailIdParam = (searchParams.get("emailId") || "").trim()
  const routedEmailId = parseRoutedEmailId(emailIdParam)

  useEffect(() => {
    if (isListError && listError) {
      toast.error(listError?.message || "메일 목록을 불러오지 못했습니다.")
    }
  }, [isListError, listError])

  useEffect(() => {
    if (scope !== "inbox") return
    if (mailboxChangeRef.current === normalizedMailbox) return
    mailboxChangeRef.current = normalizedMailbox

    if (!normalizedMailbox) return
    setFilters((prev) => ({ ...prev, page: 1 }))
    setSelectedIds([])
    setActiveEmailId(null)

    if (!mailboxInitializedRef.current) {
      mailboxInitializedRef.current = true
      return
    }

    if (searchParams.has("emailId")) {
      const nextParams = new URLSearchParams(searchParams)
      nextParams.delete("emailId")
      setSearchParams(nextParams, { replace: true })
    }
  }, [normalizedMailbox, scope, searchParams, setSearchParams])

  useEffect(() => {
    if (!routedEmailId) return
    setActiveEmailId((current) => (current === routedEmailId ? current : routedEmailId))
  }, [routedEmailId])

  const handleToggleSelectAll = () => {
    if (emails.length === 0) return
    const allSelected = emails.every((item) => selectedIds.includes(item.id))
    if (allSelected) {
      setSelectedIds([])
    } else {
      setSelectedIds(emails.map((item) => item.id))
    }
  }

  const handleToggleSelect = (emailId) => {
    setSelectedIds((prev) =>
      prev.includes(emailId) ? prev.filter((id) => id !== emailId) : [...prev, emailId],
    )
  }

  const handleSelectEmail = (emailId) => {
    setActiveEmailId(emailId)
    const next = new URLSearchParams(searchParams)
    next.set("emailId", String(emailId))
    setSearchParams(next)
  }

  const clearActiveEmailParam = () => {
    if (!searchParams.has("emailId")) return
    const next = new URLSearchParams(searchParams)
    next.delete("emailId")
    setSearchParams(next)
  }

  const handleDeleteEmail = async (emailId) => {
    try {
      await deleteMutation.mutateAsync(emailId)
      toast.success("메일을 삭제했습니다.")
      setSelectedIds((prev) => prev.filter((id) => id !== emailId))
      if (activeEmailId === emailId) {
        setActiveEmailId(null)
        clearActiveEmailParam()
      }
    } catch (error) {
      toast.error(error?.message || "메일 삭제에 실패했습니다.")
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return
    try {
      await bulkDeleteMutation.mutateAsync(selectedIds)
      toast.success(`${selectedIds.length}개의 메일을 삭제했습니다.`)
      setSelectedIds([])
      if (selectedIds.includes(activeEmailId)) {
        setActiveEmailId(null)
        clearActiveEmailParam()
      }
    } catch (error) {
      toast.error(
        error?.message || "RAG 삭제 실패 등으로 메일 삭제에 실패했습니다. 다시 시도해주세요.",
      )
    }
  }

  const handleMoveEmails = async (targetMailbox) => {
    if (selectedIds.length === 0) return

    const normalizedTarget = normalizeMailbox(targetMailbox)
    if (!normalizedTarget) {
      toast.error("이동할 메일함을 선택해주세요.")
      return
    }
    if (normalizedTarget === normalizedMailbox) {
      toast.error("이미 선택한 메일함입니다.")
      return
    }

    try {
      await moveMutation.mutateAsync({
        emailIds: selectedIds,
        toUserSdwtProd: normalizedTarget,
      })
      toast.success(`${selectedIds.length}개의 메일을 이동했습니다.`)
      setSelectedIds([])
      if (selectedIds.includes(activeEmailId)) {
        setActiveEmailId(null)
        clearActiveEmailParam()
      }
    } catch (error) {
      toast.error(error?.message || "메일 이동에 실패했습니다. 다시 시도해주세요.")
    }
  }

  const handleResetFilters = () => {
    setFilters(INITIAL_FILTERS)
  }

  useEffect(() => {
    if (emailIdParam) return
    if (!isListLoading && emails.length > 0 && activeEmailId === null) {
      setActiveEmailId(emails[0].id)
    }
  }, [emailIdParam, isListLoading, emails, activeEmailId])

  useEffect(() => {
    if (!emailIdParam || emails.length === 0) return

    const targetEmail = emails.find(
      (email) =>
        String(email.id) === emailIdParam ||
        (typeof email.ragDocId === "string" && email.ragDocId.trim() === emailIdParam),
    )
    if (targetEmail) {
      setActiveEmailId(targetEmail.id)
    }
  }, [emailIdParam, emails])

  const pageSize = listData?.pageSize ?? filters.pageSize
  const totalCount = listData?.total ?? 0
  const currentPage = listData?.page ?? filters.page
  const effectivePageSize = Math.max(1, pageSize || 1)
  const totalPages = listData?.totalPages ?? Math.max(1, Math.ceil(totalCount / effectivePageSize))

  const handleExactPageChange = (nextPage) => {
    setFilters((prev) => {
      const safePage = Math.min(Math.max(1, nextPage), totalPages)
      return { ...prev, page: safePage }
    })
  }

  const handlePageSizeChange = (value) => {
    const parsed = Number(value)
    if (Number.isNaN(parsed)) return
    setFilters((prev) => ({ ...prev, pageSize: parsed, page: 1 }))
  }

  const handleReload = () => {
    if (!listEnabled) return
    refetch()
  }

  const isReloading = isListFetching
  const stopDragging = () => {
    if (dragCleanupRef.current) {
      dragCleanupRef.current()
      dragCleanupRef.current = null
    }
  }

  const handleResizeStart = (event) => {
    if (!splitPaneRef.current) return
    event.preventDefault()
    stopDragging()
    setIsDragging(true)

    const handlePointerMove = (moveEvent) => {
      const container = splitPaneRef.current
      if (!container) return
      const { left } = container.getBoundingClientRect()
      const proposedWidth = moveEvent.clientX - left
      setListWidth(clampListWidth(proposedWidth, container))
    }

    const handlePointerEnd = () => {
      setIsDragging(false)
      stopDragging()
    }

    dragCleanupRef.current = () => {
      window.removeEventListener("pointermove", handlePointerMove)
      window.removeEventListener("pointerup", handlePointerEnd)
      window.removeEventListener("pointercancel", handlePointerEnd)
    }

    window.addEventListener("pointermove", handlePointerMove)
    window.addEventListener("pointerup", handlePointerEnd)
    window.addEventListener("pointercancel", handlePointerEnd)
  }

  useEffect(() => {
    const container = splitPaneRef.current
    if (!container) return
    const { width } = container.getBoundingClientRect()
    if (!width) return

    const proposedWidth = width * DEFAULT_LIST_RATIO
    setListWidth(clampListWidth(proposedWidth, container))
  }, [])

  useEffect(() => {
    const handleResize = () => {
      const container = splitPaneRef.current
      if (!container) return
      setListWidth((current) => clampListWidth(current, container))
    }
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  useEffect(
    () => () => {
      if (dragCleanupRef.current) {
        dragCleanupRef.current()
        dragCleanupRef.current = null
      }
    },
    [],
  )

  const splitPaneStyles = {
    "--email-list-width": `${listWidth}px`,
    "--email-handle-offset": `${listWidth + GRID_GAP_PX / 2}px`,
  }

  return {
    scope,
    filters,
    setFilters,
    handleResetFilters,
    mailboxParam: normalizedMailbox,
    emails,
    selectedIds,
    activeEmailId,
    isListLoading,
    detailData,
    htmlData,
    isDetailLoading,
    isHtmlLoading,
    handleToggleSelectAll,
    handleToggleSelect,
    handleSelectEmail,
    handleDeleteEmail,
    handleBulkDelete,
    handleMoveEmails,
    moveTargets,
    isBulkDeleting: bulkDeleteMutation.isPending,
    isMoving: moveMutation.isPending,
    currentPage,
    totalPages,
    pageSize,
    pageSizeOptions: EMAIL_PAGE_SIZE_OPTIONS,
    handleExactPageChange,
    handlePageSizeChange,
    handleReload,
    isReloading,
    splitPaneRef,
    splitPaneStyles,
    isDragging,
    handleResizeStart,
  }
}

export function useEmailInboxController() {
  const [searchParams, setSearchParams] = useSearchParams()
  const mailboxParam = getMailboxFromSearchParams(searchParams)

  return useEmailListController({
    scope: "inbox",
    mailboxParam,
    searchParams,
    setSearchParams,
  })
}

export function useEmailSentController() {
  const [searchParams, setSearchParams] = useSearchParams()

  return useEmailListController({
    scope: "sent",
    mailboxParam: SENT_MAILBOX_ID,
    searchParams,
    setSearchParams,
  })
}
