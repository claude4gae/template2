// 파일 경로: src/features/pm-comparison/api/queryKeys.js
// PM SPIDER React Query 키 정의입니다.

export const pmComparisonQueryKeys = {
  all: ["pm-comparison"],
  meta: (selectionKey = "all") => ["pm-comparison", "meta", selectionKey],
  result: (payloadKey) => ["pm-comparison", "result", payloadKey],
  category: (pattern, payloadKey) => ["pm-comparison", "category", pattern, payloadKey],
  detail: (categoryId, itemKey, payloadKey) => [
    "pm-comparison",
    "detail",
    categoryId,
    itemKey,
    payloadKey,
  ],
}
