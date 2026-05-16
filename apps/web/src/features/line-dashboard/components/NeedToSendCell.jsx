// src/features/line-dashboard/components/NeedToSendCell.jsx
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { Check, CalendarCheck2, CalendarX2, XCircle } from "lucide-react"

import { buildToastOptions } from "../utils/toast"
import { makeCellKey } from "../utils/dataTableCellState"
import { deriveFlagState, describeFlagState } from "../utils/dataTableFlagState"

/* ============================================================================
 * NeedToSendCell
 * - needtosend 값을 tinyint 스타일로 표시/토글합니다. (현재는 0/1만 사용)
 * - 서버로는 { needtosend: number } 형태로 전송합니다.
 * - 과거 0/1, "Y"/"N" 등도 안전 변환
 * ========================================================================== */

/* =========================
 * 1) 토스트 도우미
 * ======================= */
function showReserveToast() {
  toast.success("예약 성공", {
    description: "E-SOP Inform 예약 되었습니다.",
    icon: <CalendarCheck2 className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success", duration: 1800 }),
  })
}

function showCancelToast() {
  toast.success("예약 취소", {
    description: "E-SOP Inform 예약 취소 되었습니다.",
    icon: <CalendarX2 className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success", duration: 1800 }),
  })
}

function showErrorToast(message) {
  toast.error("저장 실패", {
    description: message || "저장 중 오류가 발생했습니다.",
    icon: <XCircle className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "destructive", duration: 3000 }),
  })
}

/* =========================
 * 2) 컴포넌트
 * ======================= */
export function NeedToSendCell({
  meta,
  recordId,
  baseValue, // 서버/테이블 원본값 (숫자/불리언 등)
  state,
  sendJiraValue,
  instantInformValue,
  disabled = false,
  disabledReason = "이미 전송 작업이 생성되어 예약 수정 불가",
}) {
  const baseState = state ?? deriveFlagState(baseValue, 0)
  const sendJiraState = deriveFlagState(sendJiraValue, 0)
  const instantInformState = deriveFlagState(instantInformValue, 0)
  const isLockedBySendJira = sendJiraState.numericValue === 1
  const isLockedByInstantInform = instantInformState.numericValue === 1
  const isDisabled = disabled || isLockedBySendJira || isLockedByInstantInform

  const draftValue = meta?.needToSendDrafts?.[recordId]
  const effectiveState = draftValue === undefined ? baseState : deriveFlagState(draftValue, baseState.numericValue)
  const { numericValue, isOn, isError } = effectiveState
  const isChecked = isOn

  const savingKey = makeCellKey(recordId, "needtosend")
  const isSaving = Boolean(meta?.updatingCells?.[savingKey])

  const toggle = async () => {
    if (isDisabled) {
      toast.info(disabledReason, {
        ...buildToastOptions({ intent: "info", duration: 2400 }),
      })
      return
    }
    if (isSaving) return

    const targetValue = isChecked ? 0 : 1
    meta?.setNeedToSendDraftValue?.(recordId, targetValue)
    meta?.clearUpdateError?.(savingKey)

    try {
      const updateSucceeded = await meta?.handleUpdate?.(recordId, { needtosend: targetValue })

      if (updateSucceeded) {
        meta?.removeNeedToSendDraftValue?.(recordId)
        targetValue ? showReserveToast() : showCancelToast()
        return
      }

      const errorMessage = meta?.updateErrors?.[savingKey]
      showErrorToast(errorMessage)
    } catch (error) {
      showErrorToast(error?.message)
    } finally {
      meta?.removeNeedToSendDraftValue?.(recordId)
    }
  }

  const onKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      toggle()
    }
  }

  const titleText = isDisabled
    ? disabledReason
    : describeFlagState(numericValue)

  return (
    <div className="inline-flex justify-center">
      {/* 원형 토글 버튼 */}
      <button
        type="button"
        onClick={toggle}
        onKeyDown={onKeyDown}
        disabled={isDisabled || isSaving}
        role="switch"
        aria-checked={isChecked}
        aria-disabled={isDisabled || isSaving}
        aria-label={titleText}
        title={titleText}
        className={cn(
          "inline-flex h-5 w-5 items-center justify-center rounded-full border text-muted-foreground transition-colors focus:outline-none ",
          isError
            ? "border-destructive/60 bg-destructive/10 text-destructive"
            : isChecked
              ? "bg-primary border-primary text-primary-foreground"
              : "border-border hover:border-primary hover:text-primary",
          !isDisabled && !isSaving && "cursor-pointer",
          (isDisabled || isSaving) && "cursor-not-allowed opacity-60"
        )}
      >
        {isError ? <XCircle className="h-3 w-3" strokeWidth={3} /> : null}
        {!isError && isChecked ? <Check className="h-3 w-3" strokeWidth={3} /> : null}
      </button>
    </div>
  )
}

export default NeedToSendCell
