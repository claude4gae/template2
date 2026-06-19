import React, { Suspense, lazy } from "react";
import { ObserverShell } from "./components/ObserverShell";
import { PageLoader } from "./components/Loaders";

const ObserverPage = lazy(() => import("./pages/ObserverPage"));

const ObserverRoute = () => (
  <Suspense fallback={<PageLoader label="Observer을 불러오는 중입니다" />}>
    <ObserverPage />
  </Suspense>
);

export const observerRoutes = [
  {
    path: "observer",
    element: <ObserverShell />,
    children: [
      { index: true, element: <ObserverRoute /> },
      { path: ":eqpId", element: <ObserverRoute /> },
    ],
  },
];
