import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useEsopLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("esop", eqpId, logQueryOptions, options);
