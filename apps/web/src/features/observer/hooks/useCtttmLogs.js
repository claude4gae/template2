import { useObserverLogQuery } from "./useObserverLogQuery";

export const useCtttmLogs = (eqpId, logQueryOptions, options) =>
  useObserverLogQuery("ctttm", eqpId, logQueryOptions, options);
