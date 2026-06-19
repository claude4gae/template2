import { useObserverLogQuery } from "./useObserverLogQuery";

export const useEsopLogs = (eqpId, logQueryOptions, options) =>
  useObserverLogQuery("esop", eqpId, logQueryOptions, options);
