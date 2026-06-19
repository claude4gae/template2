import { useQuery } from "@tanstack/react-query";
import { observerApiClient } from "../api/client";
import { observerQueryKeys } from "../api/queryKeys";
import { DEFAULT_LOG_QUERY_OPTIONS } from "../utils/constants";

const LOG_QUERY_STALE_TIME = 1000 * 60 * 5;

export function useObserverLogQuery(
  logKey,
  eqpId,
  logQueryOptions = DEFAULT_LOG_QUERY_OPTIONS,
  options = {}
) {
  const enabled = Boolean(eqpId) && (options.enabled ?? true);

  return useQuery({
    queryKey: observerQueryKeys.logs(logKey, eqpId, logQueryOptions),
    queryFn: () =>
      observerApiClient(`/logs/${logKey}`, {
        params: { eqpId, ...logQueryOptions },
      }),
    enabled,
    staleTime: LOG_QUERY_STALE_TIME,
  });
}
