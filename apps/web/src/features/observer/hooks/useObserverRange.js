import { calcRange, addBuffer } from "../utils/observerUtils";

/**
 * 로그 배열을 받아서 Observer 범위를 계산하는 훅
 * @param {Array} logs - 모든 로그 데이터가 합쳐진 배열
 */
export function useObserverRange(logs = []) {
  if (logs.length === 0) {
    const today = new Date();
    const startOfToday = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate()
    );
    const endOfToday = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() + 1
    );
    return addBuffer(startOfToday.getTime(), endOfToday.getTime());
  }

  const { min, max } = calcRange(logs);
  return addBuffer(min.getTime(), max.getTime());
}
