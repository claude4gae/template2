import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { RequireAuth } from "@/lib/auth"

export function AssistantShell() {
  return (
    <RequireAuth>
      <HomeLayout
        contentMaxWidthClass="max-w-7xl"
        scrollAreaClassName="overflow-hidden"
      >
        <Outlet />
      </HomeLayout>
    </RequireAuth>
  )
}
