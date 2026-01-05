// 파일 경로: src/features/line-dashboard/hooks/useLineSettings.js
// 라인 조기 알림 설정 데이터를 관리하는 전용 훅 (비동기 로딩 + CRUD 포함)
import * as React from "react"

import {
  createLineSetting,
  deleteLineSetting,
  fetchUserSdwtJiraKey,
  fetchLineSettings,
  updateLineSetting,
  updateUserSdwtJiraKey,
} from "../api"
import { timeFormatter } from "../utils/formatters"
import { sortEntries } from "../utils/lineSettings"

const EMPTY_TIMESTAMP = "-"

const normalizeId = (value) => String(value ?? "")
const nowLabel = () => timeFormatter.format(new Date())

export function useLineSettings({ lineId, userSdwtProd }) {
  const [entries, setEntries] = React.useState([])
  const [userSdwtValues, setUserSdwtValues] = React.useState([])
  const [jiraKey, setJiraKey] = React.useState("")
  const [jiraKeyError, setJiraKeyError] = React.useState(null)
  const [error, setError] = React.useState(null)
  const [isLoading, setIsLoading] = React.useState(false)
  const [isJiraKeyLoading, setIsJiraKeyLoading] = React.useState(false)
  const [hasLoadedOnce, setHasLoadedOnce] = React.useState(false)
  const [lastUpdatedLabel, setLastUpdatedLabel] = React.useState(EMPTY_TIMESTAMP)

  const hasLoadedRef = React.useRef(false)

  const resetForLineChange = React.useCallback(() => {
    setEntries([])
    setUserSdwtValues([])
    setJiraKey("")
    setJiraKeyError(null)
    setError(null)
    setIsLoading(false)
    setIsJiraKeyLoading(false)
    setLastUpdatedLabel(EMPTY_TIMESTAMP)
    setHasLoadedOnce(false)
    hasLoadedRef.current = false
  }, [])

  React.useEffect(() => {
    resetForLineChange()
  }, [lineId, resetForLineChange])

  const refresh = React.useCallback(async () => {
    // 라인을 선택하지 않은 경우: 네트워크 호출을 생략하고 초기 상태만 반환
    if (!lineId) {
      resetForLineChange()
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true
        setHasLoadedOnce(true)
      }
      return { ok: true }
    }

    setIsLoading(true)
    setIsJiraKeyLoading(true)
    setError(null)
    setJiraKeyError(null)
    if (hasLoadedRef.current) {
      setLastUpdatedLabel("Updating…")
    }

    try {
      const [settingsResult, jiraResult] = await Promise.allSettled([
        fetchLineSettings(lineId),
        userSdwtProd ? fetchUserSdwtJiraKey(userSdwtProd) : Promise.resolve({ jiraKey: "" }),
      ])

      let ok = true
      if (settingsResult.status === "fulfilled") {
        const { entries: loadedEntries, userSdwtValues: loadedUsers } = settingsResult.value
        setEntries(sortEntries(loadedEntries || []))
        setUserSdwtValues(loadedUsers || [])
        setLastUpdatedLabel(nowLabel())
      } else {
        const message =
          settingsResult.reason instanceof Error
            ? settingsResult.reason.message
            : "Failed to load settings"
        setError(message)
        setUserSdwtValues([])
        if (!hasLoadedRef.current) {
          setLastUpdatedLabel(EMPTY_TIMESTAMP)
        }
        ok = false
      }

      if (jiraResult.status === "fulfilled") {
        setJiraKey(jiraResult.value?.jiraKey || "")
      } else {
        const message =
          jiraResult.reason instanceof Error
            ? jiraResult.reason.message
            : "Failed to load Jira key"
        setJiraKeyError(message)
        setJiraKey("")
        ok = false
      }

      return { ok }
    } finally {
      setIsLoading(false)
      setIsJiraKeyLoading(false)
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true
        setHasLoadedOnce(true)
      }
    }
  }, [lineId, resetForLineChange, userSdwtProd])

  React.useEffect(() => {
    refresh()
  }, [refresh])

  const createEntry = React.useCallback(
    async ({ mainStep, customEndStep }) => {
      const { entry } = await createLineSetting({ lineId, mainStep, customEndStep })
      if (entry) {
        setEntries((prev) =>
          sortEntries([...prev.filter((item) => item.id !== entry.id), entry]),
        )
        setLastUpdatedLabel(nowLabel())
      }
      return entry
    },
    [lineId],
  )

  const updateEntry = React.useCallback(
    async ({ id, mainStep, customEndStep }) => {
      const { entry } = await updateLineSetting({ id, lineId, mainStep, customEndStep })
      if (entry) {
        setEntries((prev) =>
          sortEntries(prev.map((item) => (item.id === entry.id ? entry : item))),
        )
        setLastUpdatedLabel(nowLabel())
      }
      return entry
    },
    [lineId],
  )

  const deleteEntry = React.useCallback(async ({ id }) => {
    await deleteLineSetting({ id })
    const normalizedId = normalizeId(id)
    setEntries((prev) => prev.filter((item) => normalizeId(item.id) !== normalizedId))
    setLastUpdatedLabel(nowLabel())
    return { ok: true }
  }, [])

  const updateJiraKey = React.useCallback(
    async ({ jiraKey: nextJiraKey }) => {
      if (!userSdwtProd) {
        throw new Error("Select a user SDWT to update Jira key")
      }
      const { jiraKey: savedKey } = await updateUserSdwtJiraKey({
        userSdwtProd,
        jiraKey: nextJiraKey,
      })
      setJiraKey(savedKey || "")
      setJiraKeyError(null)
      setLastUpdatedLabel(nowLabel())
      return savedKey
    },
    [userSdwtProd],
  )

  return {
    entries,
    userSdwtValues,
    jiraKey,
    jiraKeyError,
    error,
    isLoading,
    isJiraKeyLoading,
    hasLoadedOnce,
    lastUpdatedLabel,
    refresh,
    createEntry,
    updateEntry,
    deleteEntry,
    updateJiraKey,
  }
}
