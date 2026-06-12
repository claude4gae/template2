// /src/features/teamstaff/routes.jsx
// 모델 기능의 라우트 정의를 묶어둡니다.
import { PortalHomeShell } from "@/components/layout"

import TeamStaffPage from "./pages/TeamStaffPage"

export const teamstaffRoutes = [
  {
    element: <PortalHomeShell />,
    children: [
      {
        path: "teamstaff",
        element: <TeamStaffPage />,
      },
    ],
  },
]
