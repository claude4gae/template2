import { Outlet } from "react-router-dom"

import { ChatWidget } from "@/features/assistant"
import { RequireAuth } from "@/lib/auth"

export function FdcTrendShell() {
  return (
    <RequireAuth>
      <div className="flex h-full min-h-0 w-full flex-col bg-background">
        <Outlet />
      </div>
      <ChatWidget />
    </RequireAuth>
  )
}
