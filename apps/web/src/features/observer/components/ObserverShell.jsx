import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { RequireAuth } from "@/lib/auth"

export function ObserverShell() {
  return (
    <RequireAuth>
      <HomeLayout
        contentMaxWidthClass="max-w-full"
        scrollAreaClassName="overflow-hidden"
      >
        <Outlet />
      </HomeLayout>
    </RequireAuth>
  )
}
