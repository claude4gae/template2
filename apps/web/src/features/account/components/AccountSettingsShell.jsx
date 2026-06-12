import { Outlet } from "react-router-dom"

import { TeamSwitcher } from "@/components/common"
import { AppShellLayout } from "@/components/layout"
import { RequireAuth } from "@/lib/auth"
import { buildNavigationConfig } from "@/lib/config/navigationConfig"

export function AccountSettingsShell() {
  const navigation = buildNavigationConfig()

  return (
    <RequireAuth>
      <AppShellLayout
        navItems={navigation.navMain}
        sidebarHeader={<TeamSwitcher disabled />}
      >
        <Outlet />
      </AppShellLayout>
    </RequireAuth>
  )
}
