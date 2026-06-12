import { Outlet } from "react-router-dom"

import { HomeLayout } from "./HomeLayout"

export function PortalHomeShell() {
  return (
    <HomeLayout
      innerClassName="mx-auto w-full max-w-10xl flex flex-col gap-8"
    >
      <Outlet />
    </HomeLayout>
  )
}
