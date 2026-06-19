import { observerApiClient } from "./client";

export const observerApi = {
  // "라인 목록" 엔드포인트
  fetchLines: () => observerApiClient("/lines"),

  // SDWT 목록
  fetchSDWT: (lineId) => observerApiClient("/sdwts", { params: { lineId } }),

  // PRC Group 목록
  fetchPrcGroups: (lineId, sdwtId) =>
    observerApiClient("/prc-groups", { params: { lineId, sdwtId } }),

  // Equipment 목록
  fetchEquipments: (lineId, sdwtId, prcGroup) => {
    const params = { lineId };
    if (sdwtId) params.sdwtId = sdwtId;
    if (prcGroup) params.prcGroup = prcGroup;
    return observerApiClient("/equipments", { params });
  },

  // 로그 가져오기 - sdwtId 제거
  fetchLogs: ({ lineId, eqpId, ...logQueryOptions }) =>
    observerApiClient("/logs", {
      params: { lineId, eqpId, ...logQueryOptions },
    }),

  // EQP 정보 조회
  fetchEquipmentInfo: (lineId, eqpId) =>
    observerApiClient(`/equipment-info/${lineId}/${eqpId}`),

  fetchEquipmentInfoByEqpId: (eqpId) =>
    observerApiClient(`/equipment-info/${eqpId}`),
};
