import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useDroneLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("drone", eqpId, logQueryOptions, options);
