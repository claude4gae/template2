import { useObserverLogQuery } from "./useObserverLogQuery";

export const useRacbLogs = (eqpId, logQueryOptions, options) =>
  useObserverLogQuery("racb", eqpId, logQueryOptions, options);
