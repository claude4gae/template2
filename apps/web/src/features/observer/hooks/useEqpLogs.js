import { useObserverLogQuery } from "./useObserverLogQuery";

export const useEqpLogs = (eqpId, logQueryOptions, options) =>
  useObserverLogQuery("eqp", eqpId, logQueryOptions, options);
