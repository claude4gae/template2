const ROOT_KEY = ["observer"]

export const observerQueryKeys = {
  all: ROOT_KEY,
  equipmentInfo: (eqpId) => [...ROOT_KEY, "equipment-info", eqpId ?? null],
  logs: (logKey, eqpId, options) => [
    ...ROOT_KEY,
    "logs",
    logKey,
    eqpId ?? null,
    options ?? {},
  ],
}
