import { AccessStatsShell } from "./components/AccessStatsShell"
import { AccessStatsPage } from "./pages/AccessStatsPage"

export const accessStatsRoutes = [
  {
    path: "access-stats",
    element: <AccessStatsShell />,
    children: [
      {
        index: true,
        element: <AccessStatsPage />,
      },
    ],
  },
]
