import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { ChatWidget } from "@/features/assistant"
import { RequireAuth } from "@/lib/auth"

export function TimelineShell() {
  return (
    <RequireAuth>
      <>
        <HomeLayout
          contentMaxWidthClass="max-w-full"
          scrollAreaClassName="overflow-hidden"
        >
          <Outlet />
        </HomeLayout>
        <ChatWidget />
      </>
    </RequireAuth>
  )
}
