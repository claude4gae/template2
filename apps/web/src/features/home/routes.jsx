import { PortalHomeShell } from "@/components/layout"

import HomePage from "./pages/HomePage"

export const homeRoutes = [
  {
    element: <PortalHomeShell />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
    ],
  },
]
