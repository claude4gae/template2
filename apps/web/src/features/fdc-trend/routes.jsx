// 파일 경로: src/features/fdc-trend/routes.jsx
// L0 Spider feature 라우트 정의입니다.
import { LineDashboardShell } from "@/features/line-dashboard"

import { FdcTrendPage } from "./pages/FdcTrendPage"

export const fdcTrendRoutes = [
  {
    path: "fdc_trend",
    element: (
      <LineDashboardShell
        contentMaxWidthClass="max-w-none"
        scrollAreaClassName="overflow-hidden"
        paddingClassName="p-0"
        innerClassName="flex h-full w-full flex-col"
      />
    ),
    children: [
      {
        index: true,
        element: <FdcTrendPage />,
      },
    ],
  },
]
