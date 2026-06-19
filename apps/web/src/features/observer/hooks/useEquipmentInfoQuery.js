import { useQuery } from "@tanstack/react-query"

import { observerQueryKeys } from "../api/queryKeys"
import { observerApi } from "../api/observerApi"

export function useEquipmentInfoQuery(eqpId, options = {}) {
  const enabled = Boolean(eqpId) && (options.enabled ?? true)

  return useQuery({
    queryKey: observerQueryKeys.equipmentInfo(eqpId ?? null),
    queryFn: () => observerApi.fetchEquipmentInfoByEqpId(eqpId),
    enabled,
  })
}
