import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { RequireAuth } from "@/lib/auth"

export function AccessStatsShell() {
  return (
    <RequireAuth>
      <HomeLayout
        scrollAreaClassName="overflow-hidden"
        paddingClassName="px-0 pb-0"
        innerClassName="flex h-full w-full flex-col"
      >
        <Outlet />
      </HomeLayout>
    </RequireAuth>
  )
}
