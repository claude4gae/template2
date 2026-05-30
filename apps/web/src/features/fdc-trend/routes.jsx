// 파일 경로: src/features/fdc-trend/routes.jsx
import { FdcTrendShell } from "./components/FdcTrendShell"
import { FdcTrendPage } from "./pages/FdcTrendPage"
import { L0SpiderHomePage } from "./pages/L0SpiderHomePage"
import { SpiderComingSoonPage } from "./pages/SpiderComingSoonPage"

export const fdcTrendRoutes = [
  {
    path: "fdc_trend",
    element: <FdcTrendShell />,
    children: [
      {
        index: true,
        element: <L0SpiderHomePage />,
      },
      {
        path: "self-equipment",
        element: <FdcTrendPage />,
      },
      {
        path: "matching-anomaly",
        element: <SpiderComingSoonPage title="동일성 이상감지" category="Matching" />,
      },
      {
        path: "common-anomaly",
        element: <SpiderComingSoonPage title="공통부 이상감지" category="Common" />,
      },
      {
        path: "fdc-hard-limit",
        element: <SpiderComingSoonPage title="FDC Hard Limit추천" category="Limit" />,
      },
      {
        path: "yield-hard-limit",
        element: <SpiderComingSoonPage title="수율기반 Hard Limit추천" category="Yield" />,
      },
      {
        path: "defect-spider",
        element: <SpiderComingSoonPage title="Defect SPIDER" category="Defect" />,
      },
      {
        path: "l1-spider",
        element: <SpiderComingSoonPage title="L1 SPIDER" category="Level 1" />,
      },
      {
        path: "l3-spider",
        element: <SpiderComingSoonPage title="L3 SPIDER" category="Level 3" />,
      },
    ],
  },
]
