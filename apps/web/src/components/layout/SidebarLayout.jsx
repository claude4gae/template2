import { ChevronLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { SidebarInset, SidebarProvider, useSidebar } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

import { ContentLayout } from "./ContentLayout"

function SidebarRailToggle() {
  const { toggleSidebar, state } = useSidebar()
  const isCollapsed = state === "collapsed"

  return (
    <div
      className={cn(
        "pointer-events-none absolute left-0 top-1/2 z-20 hidden -translate-y-1/2 md:flex",
        "w-(--sidebar-width) justify-end transition-[width] duration-200 ease-linear",
        "peer-data-[state=collapsed]:w-(--sidebar-width-icon)",
        "peer-data-[collapsible=offcanvas]:hidden",
      )}
    >
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={toggleSidebar}
        className="pointer-events-auto h-6 w-6 translate-x-1/2 rounded-full bg-background shadow-sm"
      >
        <ChevronLeftIcon className={cn("size-3 transition-transform", isCollapsed && "rotate-180")} />
        <span className="sr-only">Toggle sidebar</span>
      </Button>
    </div>
  )
}

export function SidebarLayout({
  children,
  sidebar,
  providerKey,
  defaultOpen = true,
  providerClassName = "relative min-h-0 h-full",
  contentMaxWidthClass = "max-w-10xl",
  scrollAreaClassName = "overflow-y-auto",
  paddingClassName = "px-4 pb-3",
  innerClassName = "mx-auto flex h-full w-full flex-col gap-4",
  insetClassName = "h-full",
  mainClassName = "flex-1 min-h-0 min-w-0 overflow-hidden",
}) {
  return (
    <SidebarProvider key={providerKey} defaultOpen={defaultOpen} className={providerClassName}>
      {sidebar ?? null}
      {sidebar ? <SidebarRailToggle /> : null}
      <SidebarInset className={insetClassName}>
        <main className={mainClassName}>
          <ContentLayout
            contentMaxWidthClass={contentMaxWidthClass}
            scrollAreaClassName={scrollAreaClassName}
            paddingClassName={paddingClassName}
            innerClassName={innerClassName}
          >
            {children}
          </ContentLayout>
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
