import {
  IconDeviceFloppy,
  IconPlus,
  IconTrash,
  IconUsers,
  IconX,
} from "@tabler/icons-react"
import { toast } from "sonner"

import { buildToastOptions } from "./toast"

export function showCreateToast() {
  toast.success("추가 완료", {
    description: "새 조기 알림 설정이 저장되었습니다.",
    icon: <IconPlus className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showUpdateToast() {
  toast.success("수정 완료", {
    description: "설정이 업데이트되었습니다.",
    icon: <IconDeviceFloppy className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showJiraKeyToast() {
  toast.success("저장 완료", {
    description: "알람 채널 설정이 저장되었습니다.",
    icon: <IconDeviceFloppy className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showNeedToSendRuleToast() {
  toast.success("저장 완료", {
    description: "자동 예약 코멘트 규칙이 저장되었습니다.",
    icon: <IconDeviceFloppy className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showDeleteToast() {
  toast.warning("삭제 완료", {
    description: "설정이 제거되었습니다.",
    icon: <IconTrash className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "warning" }),
  })
}

export function showRequestErrorToast(message) {
  toast.error("요청 실패", {
    description: message || "요청 처리 중 오류가 발생했습니다.",
    icon: <IconX className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "destructive", duration: 3200 }),
  })
}

export function showTargetCreateToast(targetUserSdwtProd) {
  toast.success("Target 추가 완료", {
    description: `${targetUserSdwtProd} 알림 Target이 추가되었습니다.`,
    icon: <IconPlus className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showTargetMappingCreateToast(userSdwtProd, sdwtProd) {
  toast.success("지정 조합 추가 완료", {
    description: `${userSdwtProd} 분임조원 -> ${sdwtProd} 분임조설비 조합이 추가되었습니다.`,
    icon: <IconPlus className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showRecipientCandidatesToast(count) {
  toast.success("수신인 후보 추가", {
    description: `${count}명을 수신인 목록에 추가했습니다.`,
    icon: <IconUsers className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}

export function showRecipientsSaveToast(description) {
  toast.success("저장 완료", {
    description,
    icon: <IconDeviceFloppy className="h-5 w-5 text-[var(--normal-text)]" />,
    ...buildToastOptions({ intent: "success" }),
  })
}
