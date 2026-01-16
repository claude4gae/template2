import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { ChatWidget } from "@/features/assistant"
import { RequireAuth } from "@/lib/auth"

export function AppstoreShell() {
  return (
    <RequireAuth>
      <>
        <HomeLayout scrollAreaClassName="overflow-hidden">
          <Outlet />
        </HomeLayout>
        <ChatWidget />
      </>
    </RequireAuth>
  )
}
