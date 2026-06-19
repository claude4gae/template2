import { useObserverLogQuery } from "./useObserverLogQuery";

export const useTipLogs = (eqpId, logQueryOptions, options) =>
  useObserverLogQuery("tip", eqpId, logQueryOptions, options);
