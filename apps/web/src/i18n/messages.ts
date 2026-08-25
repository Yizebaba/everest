export const en = {
  app: {
    title: "Everest · Summit Window",
    refresh: "Refresh",
    noData: "No data for this selection",
    apiError: "API unreachable",
    retry: "Retry",
  },
  summit: {
    window: "Summit Window",
    basis: "basis",
    nonAuthoritative: "non-authoritative presentation layer",
    go: "GO",
    caution: "CAUTION",
    stop: "STOP",
    unavailable: "unavailable",
    agreement: "source agreement",
    stale: "stale",
  },
  units: {
    temperature: "°C",
    windSpeed: "m/s",
    windDirection: "°",
    precipitation: "mm",
    visibility: "m",
    altitude: "m",
  },
  layers: {
    terrain: "Terrain",
    satellite: "Satellite",
    observations: "Observations",
    decodePending: "segment metadata available · full decode pending",
  },
  sources: {
    lifecycle: "Lifecycle",
    health: "Health",
    lastSuccess: "Last success",
    lastFailure: "Last failure",
  },
} as const;

export type MessageKey = keyof typeof en;
