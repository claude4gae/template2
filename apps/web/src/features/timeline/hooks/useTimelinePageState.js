import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { DEFAULT_TYPE_FILTERS } from "../utils/constants";
import { useTimelineSelectionStore } from "../store/useTimelineSelectionStore";
import { useTimelineStore } from "../store/useTimelineStore";
import { useTimelineLogs } from "./useTimelineLogs";
import { useEquipmentInfoQuery } from "./useEquipmentInfoQuery";

/**
 * TimelinePage에서 흩어져 있던 상태/파생 데이터를 한 곳에 모아둔 훅.
 * - URL 검증 및 동기화
 * - 드릴다운/타임라인 전용 전역 상태
 * - 테이블/타임라인에 필요한 파생 데이터 계산
 */
export function useTimelinePageState(params) {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    lineId,
    sdwtId,
    prcGroup,
    eqpId,
    setLine,
    setSdwt,
    setPrcGroup,
    setEqp,
    selectedRow,
    resetSelection,
  } = useTimelineSelectionStore();

  const {
    showLegend,
    selectedTipGroups,
    setShowLegend,
    setSelectedTipGroups,
  } = useTimelineStore();

  // 페이지 로컬 UI 상태
  const [typeFilters, setTypeFilters] = useState({ ...DEFAULT_TYPE_FILTERS });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // URL 파라미터 검증 및 상태 반영 (과도한 파일 분리를 줄이기 위해 이 훅 안에서 처리)
  const [validationError, setValidationError] = useState(null);
  const shouldValidateEqpOnly = Boolean(params.eqpId && !params.lineId);
  const {
    data: equipmentInfo,
    isFetching: isEquipmentInfoFetching,
    isError: isEquipmentInfoError,
    error: equipmentInfoError,
  } = useEquipmentInfoQuery(params.eqpId, { enabled: shouldValidateEqpOnly });

  const isValidating = shouldValidateEqpOnly && isEquipmentInfoFetching;
  const hasValidationResult = !shouldValidateEqpOnly || !isEquipmentInfoFetching;

  useEffect(() => {
    if (!shouldValidateEqpOnly) {
      setValidationError(null);
      return;
    }

    if (equipmentInfo) {
      setValidationError(null);
      setLine(equipmentInfo.lineId);
      setSdwt(equipmentInfo.sdwtId);
      setPrcGroup(equipmentInfo.prcGroup);
      setEqp(params.eqpId);
      return;
    }

    if (isEquipmentInfoError || (!equipmentInfo && !isEquipmentInfoFetching)) {
      const message =
        equipmentInfoError instanceof Error
          ? equipmentInfoError.message
          : "유효하지 않은 EQP ID입니다.";
      setValidationError(message);
      const timeoutId = setTimeout(() => navigate("/timeline"), 1500);
      return () => clearTimeout(timeoutId);
    }
  }, [
    equipmentInfo,
    equipmentInfoError,
    isEquipmentInfoError,
    isEquipmentInfoFetching,
    navigate,
    params.eqpId,
    setEqp,
    setLine,
    setPrcGroup,
    setSdwt,
    shouldValidateEqpOnly,
  ]);

  // 선택한 eqpId와 URL을 동기화
  useEffect(() => {
    if (isValidating || !hasValidationResult) return;

    const currentPath = location.pathname;
    const isParamRoute =
      currentPath.includes("/timeline/") && currentPath.split("/").length > 2;

    if (eqpId) {
      const newPath = `/timeline/${eqpId}`;
      if (currentPath !== newPath) {
        navigate(newPath, { replace: true });
      }
    } else if (isParamRoute) {
      navigate("/timeline", { replace: true });
    }
  }, [eqpId, hasValidationResult, isValidating, location.pathname, navigate]);

  useEffect(() => {
    resetSelection();
  }, [eqpId, resetSelection]);

  // EQP가 바뀔 때마다 TIP 필터를 초기화하여 예전 선택이 남지 않도록 한다.
  useEffect(() => {
    if (eqpId) {
      setSelectedTipGroups(["__ALL__"]);
    }
  }, [eqpId, setSelectedTipGroups]);

  const handleFilterChange = (event) => {
    const { name, checked } = event.target;
    setTypeFilters((prev) => ({ ...prev, [name]: checked }));
  };

  const logs = useTimelineLogs(eqpId, typeFilters, selectedTipGroups);
  const selectedLog =
    logs.mergedLogs.find((log) => String(log.id) === String(selectedRow)) ||
    null;

  return {
    selection: {
      lineId,
      sdwtId,
      prcGroup,
      eqpId,
      setLine,
      setSdwt,
      setPrcGroup,
      setEqp,
      selectedRow,
    },
    timelinePrefs: {
      showLegend,
      selectedTipGroups,
      setShowLegend,
      setSelectedTipGroups,
    },
    filters: {
      typeFilters,
      handleFilterChange,
    },
    settings: {
      isSettingsOpen,
      setIsSettingsOpen,
    },
    validation: { isValidating, validationError },
    logs,
    selectedLog,
    timelineReady: Boolean(eqpId),
  };
}
