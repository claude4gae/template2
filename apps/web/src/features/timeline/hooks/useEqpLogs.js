import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useEqpLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("eqp", eqpId, logQueryOptions, options);
