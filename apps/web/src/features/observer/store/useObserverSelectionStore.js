import { create } from "zustand";

export const useObserverSelectionStore = create((set) => ({
  /* —— A. 테이블·Observer 동기 선택 —— */
  selectedRow: null,
  source: null,
  setSelectedRow: (row, src) => set({ selectedRow: row, source: src }),

  /* —— B. 드릴다운 상태 —— */
  lineId: "",
  sdwtId: "",
  prcGroup: "",
  eqpId: "",
  setLine: (id) => set({ lineId: id, sdwtId: "", prcGroup: "", eqpId: "" }),
  setSdwt: (id) => set({ sdwtId: id, prcGroup: "", eqpId: "" }),
  setPrcGroup: (id) => set({ prcGroup: id, eqpId: "" }),
  setEqp: (id) => set({ eqpId: id }),
  resetSelection: () => set({ selectedRow: null, source: null }),
}));
