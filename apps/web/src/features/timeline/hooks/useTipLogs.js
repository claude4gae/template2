import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useTipLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("tip", eqpId, logQueryOptions, options);
