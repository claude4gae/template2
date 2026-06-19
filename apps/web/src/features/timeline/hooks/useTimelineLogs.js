import { useMemo } from "react";
import { useEqpLogs } from "./useEqpLogs";
import { useTipLogs } from "./useTipLogs";
import { useCtttmLogs } from "./useCtttmLogs";
import { useRacbLogs } from "./useRacbLogs";
import { useEsopLogs } from "./useEsopLogs";
import {
  DEFAULT_LOG_QUERY_OPTIONS,
  DEFAULT_TYPE_FILTERS,
} from "../utils/constants";
import { transformLogsToTableData } from "../utils/dataTransformers";
import { addDurationToLogs, mergeLogsByTime } from "../utils/logs";

export function useTimelineLogs(
  eqpId,
  typeFilters = DEFAULT_TYPE_FILTERS,
  selectedTipGroups = ["__ALL__"],
  logQueryOptions = DEFAULT_LOG_QUERY_OPTIONS
) {
  const enabledTypes = typeFilters || DEFAULT_TYPE_FILTERS;
  const eqpQuery = useEqpLogs(
    eqpId,
    logQueryOptions,
    { enabled: enabledTypes.EQP }
  );
  const tipQuery = useTipLogs(
    eqpId,
    logQueryOptions,
    { enabled: enabledTypes.TIP }
  );
  const ctttmQuery = useCtttmLogs(
    eqpId,
    logQueryOptions,
    { enabled: enabledTypes.CTTTM }
  );
  const racbQuery = useRacbLogs(
    eqpId,
    logQueryOptions,
    { enabled: enabledTypes.RACB }
  );
  const esopQuery = useEsopLogs(
    eqpId,
    logQueryOptions,
    { enabled: enabledTypes.ESOP }
  );

  const logsLoading =
    (enabledTypes.EQP && eqpQuery.isLoading) ||
    (enabledTypes.TIP && tipQuery.isLoading) ||
    (enabledTypes.CTTTM && ctttmQuery.isLoading) ||
    (enabledTypes.RACB && racbQuery.isLoading) ||
    (enabledTypes.ESOP && esopQuery.isLoading);

  // 정렬과 duration 계산은 UI 토글마다 반복되지 않도록 memoized 상태로 유지합니다.
  const logsWithDuration = useMemo(
    () => {
      const eqpLogs = enabledTypes.EQP ? eqpQuery.data ?? [] : [];
      const tipLogs = enabledTypes.TIP ? tipQuery.data ?? [] : [];
      const ctttmLogs = enabledTypes.CTTTM ? ctttmQuery.data ?? [] : [];
      const racbLogs = enabledTypes.RACB ? racbQuery.data ?? [] : [];
      const esopLogs = enabledTypes.ESOP ? esopQuery.data ?? [] : [];

      return {
        eqpLogs: addDurationToLogs(eqpLogs, "EQP"),
        tipLogs: addDurationToLogs(tipLogs, "TIP"),
        ctttmLogs,
        racbLogs,
        esopLogs,
      };
    },
    [
      enabledTypes.EQP,
      enabledTypes.TIP,
      enabledTypes.CTTTM,
      enabledTypes.RACB,
      enabledTypes.ESOP,
      eqpQuery.data,
      tipQuery.data,
      ctttmQuery.data,
      racbQuery.data,
      esopQuery.data,
    ]
  );

  const logErrors = useMemo(
    () =>
      [
        { type: "EQP", enabled: enabledTypes.EQP, query: eqpQuery },
        { type: "TIP", enabled: enabledTypes.TIP, query: tipQuery },
        { type: "CTTTM", enabled: enabledTypes.CTTTM, query: ctttmQuery },
        { type: "RACB", enabled: enabledTypes.RACB, query: racbQuery },
        { type: "ESOP", enabled: enabledTypes.ESOP, query: esopQuery },
      ]
        .filter(({ enabled, query }) => enabled && query.isError)
        .map(({ type, query }) => ({
          type,
          message:
            query.error instanceof Error
              ? query.error.message
              : "로그 조회에 실패했습니다.",
          refetch: query.refetch,
        })),
    [
      enabledTypes.EQP,
      enabledTypes.TIP,
      enabledTypes.CTTTM,
      enabledTypes.RACB,
      enabledTypes.ESOP,
      eqpQuery,
      tipQuery,
      ctttmQuery,
      racbQuery,
      esopQuery,
    ]
  );

  const refetchFailedLogs = () => {
    logErrors.forEach((error) => error.refetch());
  };

  const mergedLogs = useMemo(
    () => (eqpId ? mergeLogsByTime(logsWithDuration) : []),
    [eqpId, logsWithDuration]
  );

  const tableData = useMemo(() => {
    if (!eqpId || logsLoading) return [];
    return transformLogsToTableData(
      mergedLogs,
      typeFilters || DEFAULT_TYPE_FILTERS,
      selectedTipGroups
    );
  }, [eqpId, logsLoading, mergedLogs, typeFilters, selectedTipGroups]);

  const filteredTipLogs = useMemo(
    () => mergedLogs.filter((log) => log.logType === "TIP"),
    [mergedLogs]
  );

  return {
    logsLoading,
    logsWithDuration,
    mergedLogs,
    tableData,
    filteredTipLogs,
    logErrors,
    hasLogErrors: logErrors.length > 0,
    refetchFailedLogs,
  };
}
