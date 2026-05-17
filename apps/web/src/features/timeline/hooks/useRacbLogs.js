import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useRacbLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("racb", eqpId, logQueryOptions, options);
