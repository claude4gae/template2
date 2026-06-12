import { Outlet, useOutletContext } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { RequireAuth } from "@/lib/auth"

export function AssistantShell() {
  const outletContext = useOutletContext()

  return (
    <RequireAuth>
      <HomeLayout
        contentMaxWidthClass="max-w-7xl"
        scrollAreaClassName="overflow-hidden"
      >
        <Outlet context={outletContext} />
      </HomeLayout>
    </RequireAuth>
  )
}
