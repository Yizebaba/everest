import type { EverestOsState, Locale } from "@/types/schema";
import { createEnvironment } from "./environment";
import { getCommunication } from "./communication";
import { getDevices } from "./device";
import { getHazard } from "./hazard";
import { getMission } from "./mission";
import { getRoute } from "./route";
import { getSensor } from "./sensor";

export { createEnvironment } from "./environment";
export { terrainFromTile } from "./terrain";
export { weatherFromApi } from "./weather";
export { riskFromApi } from "./risk";
export { getSensor } from "./sensor";
export { getRoute } from "./route";
export { getHazard } from "./hazard";
export { getCommunication } from "./communication";
export { getDevices } from "./device";
export { getMission } from "./mission";

export function createEverestOsState(locale: Locale): EverestOsState {
  return {
    locale,
    environment: createEnvironment(locale),
    terrain: {
      sourceId: "copernicus-dem",
      dataset: "glo30",
      tile: null,
      sample: { latitude: 0, longitude: 0, elevationM: null },
      profile: [],
    },
    weather: { current: [], forecast: [], streamlines: [] },
    sensor: getSensor(),
    route: getRoute(),
    hazard: getHazard(),
    risk: {
      summitWindow: {
        level: "unknown",
        confidence: 0,
        validTime: null,
        profile: "SUMMIT",
        altitudeMetres: null,
        factors: [],
        inputs: {},
        basis: "not_loaded",
        authority: "backend-risk-engine",
      },
      hazards: { availability: "reserved", points: [] },
    },
    communication: getCommunication(),
    devices: getDevices(),
    mission: getMission(),
  };
}
