// src/features/line-dashboard/pages/LineDashboardSettingsPage.jsx
// 기존 설정 URL은 알림 설정 페이지로 이동합니다.
import { Navigate, useParams } from "react-router-dom"

export function LineDashboardSettingsPage() {
  const { lineId = "" } = useParams()

  return <Navigate to={`/ESOP_Dashboard/settings/notification/${encodeURIComponent(lineId)}`} replace />
}
