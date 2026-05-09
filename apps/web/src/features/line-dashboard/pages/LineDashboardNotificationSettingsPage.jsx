// 파일 경로: src/features/line-dashboard/pages/LineDashboardNotificationSettingsPage.jsx
// 라인별 E-SOP 알림 설정 페이지입니다.
import { useParams } from "react-router-dom"

import { LineSettingsPage } from "../components/LineSettingsPage"

export function LineDashboardNotificationSettingsPage() {
  const { lineId = "" } = useParams()

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col overflow-hidden">
      <LineSettingsPage lineId={lineId} mode="notification" />
    </div>
  )
}
