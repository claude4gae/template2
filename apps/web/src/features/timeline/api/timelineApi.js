import { timelineApiClient } from "./client";

export const timelineApi = {
  // "라인 목록" 엔드포인트
  fetchLines: () => timelineApiClient("/lines"),

  // SDWT 목록
  fetchSDWT: (lineId) => timelineApiClient("/sdwts", { params: { lineId } }),

  // PRC Group 목록
  fetchPrcGroups: (lineId, sdwtId) =>
    timelineApiClient("/prc-groups", { params: { lineId, sdwtId } }),

  // Equipment 목록
  fetchEquipments: (lineId, sdwtId, prcGroup) => {
    const params = { lineId };
    if (sdwtId) params.sdwtId = sdwtId;
    if (prcGroup) params.prcGroup = prcGroup;
    return timelineApiClient("/equipments", { params });
  },

  // 로그 가져오기 - sdwtId 제거
  fetchLogs: ({ lineId, eqpId, ...logQueryOptions }) =>
    timelineApiClient("/logs", {
      params: { lineId, eqpId, ...logQueryOptions },
    }),

  // EQP 정보 조회
  fetchEquipmentInfo: (lineId, eqpId) =>
    timelineApiClient(`/equipment-info/${lineId}/${eqpId}`),

  fetchEquipmentInfoByEqpId: (eqpId) =>
    timelineApiClient(`/equipment-info/${eqpId}`),
};
