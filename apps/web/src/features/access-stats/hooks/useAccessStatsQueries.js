import { useQuery } from "@tanstack/react-query"

import { fetchAppAccessStats } from "../api/accessStatsApi"

export const accessStatsQueryKeys = {
  appAccessStats: (params) => ["access-stats", "app-access", params],
}

export function useAppAccessStatsQuery(params, options = {}) {
  return useQuery({
    queryKey: accessStatsQueryKeys.appAccessStats(params),
    queryFn: () => fetchAppAccessStats(params),
    ...options,
  })
}
