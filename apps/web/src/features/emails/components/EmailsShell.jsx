import { useEffect, useRef } from "react"
import { Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { TeamSwitcher } from "@/components/common"
import { AppShellLayout } from "@/components/layout"
import { RequireAuth, useAuth } from "@/lib/auth"
import { buildNavigationConfig } from "@/lib/config/navigationConfig"
import {
  ActiveLineProvider,
  DepartmentProvider,
  SdwtProvider,
  getStoredMailboxId,
  useActiveLineOptional,
  useLineSdwtOptionsQuery,
} from "@/lib/affiliation"

import { useEmailMailboxes } from "../hooks/useEmailMailboxes"
import {
  buildMailboxUrl,
  buildMembersUrl,
  buildSentUrl,
  getMailboxFromSearchParams,
  isSentMailbox,
  isUnassignedMailbox,
  normalizeMailbox,
  resolveUnassignedMailboxId,
  SENT_MAILBOX_ID,
  SENT_MAILBOX_LABEL,
  UNASSIGNED_MAILBOX_LABEL,
} from "../utils/mailbox"

const INBOX_PREFIX = "/emails/inbox"
const SENT_PREFIX = "/emails/sent"
const MEMBERS_PREFIX = "/emails/members"

function normalizeLineId(value) {
  return typeof value === "string" ? value.trim() : ""
}

function buildLineOptions(lineSdwtOptions) {
  const lines = Array.isArray(lineSdwtOptions?.lines) ? lineSdwtOptions.lines : []
  const lineIds = lines
    .map((line) => normalizeLineId(line?.lineId))
    .filter(Boolean)
  return Array.from(new Set(lineIds))
}

function buildAffiliationOptions(
  lineSdwtOptions,
  mailboxes,
  {
    includeSent = false,
    includeUnassigned = false,
    unassignedMailboxId = "",
    unassignedLabel = UNASSIGNED_MAILBOX_LABEL,
  } = {},
) {
  const lines = Array.isArray(lineSdwtOptions?.lines) ? lineSdwtOptions.lines : []
  const mailboxSet = new Set(mailboxes)

  const options = lines.flatMap((line) => {
    const lineId = normalizeLineId(line?.lineId)
    if (!lineId) return []

    const userSdwtProds = Array.isArray(line?.userSdwtProds) ? line.userSdwtProds : []

    return userSdwtProds
      .map((value) => normalizeMailbox(value))
      .filter((value) => value && mailboxSet.has(value))
      .map((userSdwtProd) => ({
        id: userSdwtProd,
        label: `${lineId} / ${userSdwtProd}`,
        lineId,
        userSdwtProd,
      }))
  })

  const normalizedUnassigned = normalizeMailbox(unassignedMailboxId)
  if (includeUnassigned && normalizedUnassigned) {
    options.unshift({
      id: normalizedUnassigned,
      label: unassignedLabel,
      description: "미분류 메일함",
      lineId: null,
      userSdwtProd: normalizedUnassigned,
    })
  }

  if (includeSent) {
    options.unshift({
      id: SENT_MAILBOX_ID,
      label: SENT_MAILBOX_LABEL,
      lineId: null,
      userSdwtProd: null,
    })
  }

  return options
}

export function EmailsShell({ contentMaxWidthClass, scrollAreaClassName }) {
  return (
    <RequireAuth>
      <EmailsShellContent
        contentMaxWidthClass={contentMaxWidthClass}
        scrollAreaClassName={scrollAreaClassName}
      >
        <Outlet />
      </EmailsShellContent>
    </RequireAuth>
  )
}

function EmailsShellContent({ children, contentMaxWidthClass, scrollAreaClassName = "overflow-hidden" }) {
  const {
    data: lineSdwtOptions,
    isError: isLineSdwtError,
    error: lineSdwtError,
  } = useLineSdwtOptionsQuery()

  const lineOptions = buildLineOptions(lineSdwtOptions)

  useEffect(() => {
    if (isLineSdwtError) {
      console.warn("Failed to load line SDWT options", lineSdwtError)
    }
  }, [isLineSdwtError, lineSdwtError])

  return (
    <DepartmentProvider>
      <ActiveLineProvider lineOptions={lineOptions}>
        <EmailsShellLayout
          lineSdwtOptions={lineSdwtOptions}
          contentMaxWidthClass={contentMaxWidthClass}
          scrollAreaClassName={scrollAreaClassName}
        >
          {children}
        </EmailsShellLayout>
      </ActiveLineProvider>
    </DepartmentProvider>
  )
}

function EmailsShellLayout({
  children,
  lineSdwtOptions,
  contentMaxWidthClass,
  scrollAreaClassName,
}) {
  const [searchParams] = useSearchParams()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const lineContext = useActiveLineOptional()
  const invalidMailboxRef = useRef("")

  const {
    data: mailboxData,
    isLoading: isMailboxLoading,
    isError: isMailboxError,
    error: mailboxError,
  } = useEmailMailboxes()

  const mailboxes = Array.isArray(mailboxData?.results) ? mailboxData.results : []
  const mailboxParam = getMailboxFromSearchParams(searchParams)
  const normalizedMailboxParam = normalizeMailbox(mailboxParam)
  const currentUserSdwtProd = normalizeMailbox(user?.user_sdwt_prod)
  const normalizedMailboxes = mailboxes.map(normalizeMailbox).filter(Boolean)
  const baseMailboxes = normalizedMailboxes.filter((mailbox) => !isSentMailbox(mailbox))
  const canViewUnassigned = Boolean(user?.is_superuser)
  const unassignedMailboxId = canViewUnassigned ? resolveUnassignedMailboxId(baseMailboxes) : ""
  const validMailboxes = canViewUnassigned
    ? Array.from(new Set([...baseMailboxes, unassignedMailboxId].filter(Boolean)))
    : baseMailboxes.filter((mailbox) => !isUnassignedMailbox(mailbox))
  const firstMailbox = validMailboxes[0] || ""

  const isSentRoute = pathname.startsWith(SENT_PREFIX)
  const isMembersRoute = pathname.startsWith(MEMBERS_PREFIX)
  const isInboxRoute = pathname.startsWith(INBOX_PREFIX)
  const isMailboxRoute = isMembersRoute || isInboxRoute

  const storedMailboxCandidate = normalizeMailbox(getStoredMailboxId() || "")
  const storedMailbox =
    storedMailboxCandidate && validMailboxes.includes(storedMailboxCandidate)
      ? storedMailboxCandidate
      : ""

  const fallbackMailbox = normalizedMailboxParam || currentUserSdwtProd || firstMailbox
  const activeMailbox = isSentRoute ? SENT_MAILBOX_ID : fallbackMailbox
  const navigationMailbox = isSentRoute ? (storedMailbox || fallbackMailbox) : fallbackMailbox
  const switcherMailbox = isSentRoute ? (storedMailbox || fallbackMailbox) : activeMailbox

  const affiliationOptions = buildAffiliationOptions(lineSdwtOptions, validMailboxes, {
    includeUnassigned: canViewUnassigned,
    unassignedMailboxId,
  })
  const currentLineId = lineContext?.lineId ?? null
  const setLineId = lineContext?.setLineId
  const switcherOption = affiliationOptions.find((item) => item.id === switcherMailbox)
  const switcherLineId = switcherOption?.lineId ?? null

  useEffect(() => {
    if (isMailboxError && mailboxError) {
      toast.error(mailboxError?.message || "메일함 목록을 불러오지 못했습니다.")
    }
  }, [isMailboxError, mailboxError])

  useEffect(() => {
    if (!switcherLineId || !setLineId) return
    if (switcherLineId === currentLineId) return
    setLineId(switcherLineId)
  }, [currentLineId, setLineId, switcherLineId])

  useEffect(() => {
    if (!isMailboxRoute) return
    if (!normalizedMailboxParam) return
    if (isMailboxLoading) return
    if (isMailboxError) return
    if (validMailboxes.length === 0) return
    if (validMailboxes.includes(normalizedMailboxParam)) {
      invalidMailboxRef.current = ""
      return
    }

    if (invalidMailboxRef.current === normalizedMailboxParam) return
    invalidMailboxRef.current = normalizedMailboxParam
    toast.error("권한이 없는 메일함 입니다.")

    const nextMailbox =
      (currentUserSdwtProd && validMailboxes.includes(currentUserSdwtProd) && currentUserSdwtProd) ||
      validMailboxes[0] ||
      ""

    if (!nextMailbox) return

    const nextUrl = isMembersRoute ? buildMembersUrl(nextMailbox) : buildMailboxUrl(nextMailbox)
    navigate(nextUrl, { replace: true })
  }, [
    currentUserSdwtProd,
    isMailboxError,
    isMailboxLoading,
    isMailboxRoute,
    isMembersRoute,
    navigate,
    normalizedMailboxParam,
    validMailboxes,
  ])

  useEffect(() => {
    if (!isMailboxRoute) return
    if (normalizedMailboxParam) return
    if (!fallbackMailbox) return

    const nextUrl = isMembersRoute ? buildMembersUrl(fallbackMailbox) : buildMailboxUrl(fallbackMailbox)
    navigate(nextUrl, { replace: true })
  }, [fallbackMailbox, isMailboxRoute, isMembersRoute, navigate, normalizedMailboxParam])

  const handleSelectMailbox = (mailbox) => {
    const nextMailbox = normalizeMailbox(mailbox)
    if (!nextMailbox) return

    if (isSentMailbox(nextMailbox)) {
      navigate(buildSentUrl())
      return
    }

    if (isMailboxRoute && nextMailbox === normalizedMailboxParam) return

    const nextUrl = isMembersRoute ? buildMembersUrl(nextMailbox) : buildMailboxUrl(nextMailbox)
    navigate(nextUrl)
  }

  const navigation = buildNavigationConfig({
    mailbox: navigationMailbox,
    disableEmailMembers: isUnassignedMailbox(navigationMailbox),
  })

  return (
    <SdwtProvider userSdwtProd={activeMailbox} onChange={handleSelectMailbox}>
      <AppShellLayout
        navItems={navigation.navMain}
        sidebarHeader={(
          <TeamSwitcher
            options={affiliationOptions}
            activeId={switcherMailbox}
            onSelect={handleSelectMailbox}
            menuLabel="Line / SDWT"
            manageLabel="Manage mailboxes"
            ariaLabel="메일함(SDWT) 선택"
            disabled={isSentRoute}
          />
        )}
        contentMaxWidthClass={contentMaxWidthClass}
        scrollAreaClassName={scrollAreaClassName}
      >
        {children}
      </AppShellLayout>
    </SdwtProvider>
  )
}
