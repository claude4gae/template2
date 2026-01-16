import { Outlet } from "react-router-dom"

import { HomeLayout } from "@/components/layout"
import { ChatWidget } from "@/features/assistant"

export function HomeShell() {
  return (
    <>
      <HomeLayout
        innerClassName="mx-auto w-full max-w-10xl flex flex-col gap-8"
      >
        <Outlet />
      </HomeLayout>
      <ChatWidget />
    </>
  )
}
