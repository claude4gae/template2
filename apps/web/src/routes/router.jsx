// 파일 경로: src/routes/router.jsx
import { createBrowserRouter, Outlet } from "react-router-dom"

import { PortalGlobalShell } from "@/components/layout"
import { AuthAutoLoginGate, useAuth } from "@/lib/auth"

import { appstoreRoutes } from "@/features/appstore"
import { authRoutes } from "@/features/auth"
import { RouteErrorPage, errorRoutes } from "@/features/errors"
import { fdcTrendRoutes } from "@/features/fdc-trend"
import { homeRoutes } from "@/features/home"
import { lineDashboardRoutes } from "@/features/line-dashboard"
import { l3SpiderRoutes } from "@/features/l3-spider"
import { pmComparisonRoutes } from "@/features/pm-comparison"
import { teamstaffRoutes } from "@/features/teamstaff"
import { timelineRoutes } from "@/features/timeline"
import { vocRoutes } from "@/features/voc"
import { ChatWidget, assistantRoutes } from "@/features/assistant"
import { emailsRoutes, useEmailMailboxes } from "@/features/emails"
import { accountRoutes } from "@/features/account"

const protectedFeatureRoutes = [
  ...teamstaffRoutes,
  ...lineDashboardRoutes,
  ...fdcTrendRoutes,
  ...l3SpiderRoutes,
  ...pmComparisonRoutes,
  ...appstoreRoutes,
  ...emailsRoutes,
  ...vocRoutes,
  ...accountRoutes,
]

function AssistantWidgetOutlet() {
  const { user } = useAuth()
  const { data: mailboxesData } = useEmailMailboxes({ enabled: Boolean(user) })
  const availableMailboxes = Array.isArray(mailboxesData?.results)
    ? mailboxesData.results
    : []

  return (
    <>
      <Outlet context={{ availableMailboxes }} />
      {user ? <ChatWidget availableMailboxes={availableMailboxes} /> : null}
    </>
  )
}

function AssistantMailboxOutlet() {
  const { user } = useAuth()
  const { data: mailboxesData } = useEmailMailboxes({ enabled: Boolean(user) })
  const availableMailboxes = Array.isArray(mailboxesData?.results)
    ? mailboxesData.results
    : []

  return <Outlet context={{ availableMailboxes }} />
}

const assistantWidgetRoutes = {
  element: <AuthAutoLoginGate />,
  children: [
    {
      element: <AssistantWidgetOutlet />,
      children: [
        ...homeRoutes,
        ...protectedFeatureRoutes,
        ...timelineRoutes,
      ],
    },
  ],
}

const assistantProtectedRoutes = {
  element: <AuthAutoLoginGate />,
  children: [
    {
      element: <AssistantMailboxOutlet />,
      children: assistantRoutes,
    },
  ],
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PortalGlobalShell />,
    errorElement: (
      <PortalGlobalShell>
        <RouteErrorPage />
      </PortalGlobalShell>
    ),
    children: [
      ...authRoutes,
      assistantWidgetRoutes,
      assistantProtectedRoutes,
      ...errorRoutes,
    ],
  },
])
