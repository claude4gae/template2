import { Outlet } from "react-router-dom"

import { portalNavigationItems } from "@/lib/config/portalNavigation"
import { AppAccessTracker } from "@/lib/activity"

import { PortalNavbar } from "./PortalNavbar"

export function PortalGlobalShell({ children }) {
  return (
    <div className="h-screen flex flex-col bg-background">
      <header className="h-14 shrink-0 border-b bg-background">
        <div className="h-full">
          <PortalNavbar navigationItems={portalNavigationItems} />
        </div>
      </header>
      <main className="flex-1 min-h-0 overflow-hidden pt-2">
        <AppAccessTracker />
        {children ?? <Outlet />}
      </main>
    </div>
  )
}
