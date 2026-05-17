import { useTimelineLogQuery } from "./useTimelineLogQuery";

export const useCtttmLogs = (eqpId, logQueryOptions, options) =>
  useTimelineLogQuery("ctttm", eqpId, logQueryOptions, options);
