/**
 * Everest OS — 10-dimension domain schema (Phase 1).
 *
 * These are presentation/domain views over canonical API contracts. They are
 * intentionally not a second canonical weather or risk schema. Adapters retain
 * canonical references and reserved domains remain explicitly empty.
 */

import type { CanonicalWeatherRecord } from "@/api/types";
import type { Locale } from "@/i18n/locale";

export type { Locale } from "@/i18n/locale";
export type DomainAvailability = "available" | "empty" | "reserved";

export type EnvironmentKind = "everest" | "cave" | "mine" | "wilderness";

// ---------------------------------------------------------------------------
// 1. Environment — running context
// ---------------------------------------------------------------------------
export interface Environment {
  kind: EnvironmentKind;
  name: string;
  locale: Locale;
  /** AOI center in WGS84 decimal degrees. */
  center: { latitude: number; longitude: number };
  /** AOI radius in meters. */
  radiusMeters: number;
  activeMissionId: string | null;
}

// ---------------------------------------------------------------------------
// 2. Terrain — DEM / elevation / slope / terrain profile
// ---------------------------------------------------------------------------
export interface TerrainTileMeta {
  tileName: string;
  crs: string;
  bounds: [number, number, number, number];
  resolutionDegrees: number;
  minElevationM: number;
  maxElevationM: number;
  retrievedAt: string;
}

export interface TerrainProfilePoint {
  distanceM: number;
  elevationM: number;
  slopeDegrees: number | null;
}

export interface Terrain {
  sourceId: string;
  dataset: "glo30" | "glo90";
  tile: TerrainTileMeta | null;
  /** Point sample at a coordinate, from the retained canonical tile. */
  sample: { latitude: number; longitude: number; elevationM: number | null };
  /** Reserved: 2D/3D terrain profile along a route. */
  profile: TerrainProfilePoint[];
}

// ---------------------------------------------------------------------------
// 3. Weather — multi-source variables and spatial particle streamlines
// ---------------------------------------------------------------------------
export interface WeatherVariable {
  temperatureC: number | null;
  windSpeedMs: number | null;
  windDirectionDeg: number | null;
  precipitationMm: number | null;
  visibilityM: number | null;
  relativeHumidityPct: number | null;
}

export interface WeatherRecord extends WeatherVariable {
  timestamp: string;
  source: string;
  model: string | null;
  recordType: "forecast" | "observation" | "satellite" | "derived";
  spatialKey: string;
  qualityFlags: string[];
  /** Complete validated API record; this view never replaces canonical data. */
  canonical: CanonicalWeatherRecord;
}

export interface WeatherStreamlinePoint {
  latitude: number;
  longitude: number;
  altitudeM: number;
  speedMs: number;
}

export interface Weather {
  current: WeatherRecord[];
  forecast: WeatherRecord[];
  /** Reserved: spatial particle streamlines for wind flow visualization. */
  streamlines: WeatherStreamlinePoint[];
}

// ---------------------------------------------------------------------------
// 4. Sensor — hardware / station collection
// ---------------------------------------------------------------------------
export type SensorKind = "aws" | "pyramid" | "custom";

export interface SensorReading {
  timestamp: string;
  station: string;
  kind: SensorKind;
  temperatureC: number | null;
  relativeHumidityPct: number | null;
  pressureHpa: number | null;
  precipitationMm: number | null;
  qualityFlags: string[];
}

export interface Sensor {
  availability: DomainAvailability;
  readings: SensorReading[];
  status: "ok" | "degraded" | "offline" | "unknown";
}

// ---------------------------------------------------------------------------
// 5. Route — climbing / crossing track routes and vector nodes
// ---------------------------------------------------------------------------
export interface RouteNode {
  index: number;
  latitude: number;
  longitude: number;
  altitudeM: number | null;
  label: string | null;
}

export interface Route {
  availability: DomainAvailability;
  id: string;
  name: string;
  nodes: RouteNode[];
  totalDistanceM: number;
}

// ---------------------------------------------------------------------------
// 6. Hazard — crevasses, avalanche zones, spatial points
// ---------------------------------------------------------------------------
export type HazardKind = "crevasse" | "avalanche" | "icefall" | "rockfall";

export interface HazardPoint {
  id: string;
  kind: HazardKind;
  latitude: number;
  longitude: number;
  severity: 1 | 2 | 3;
}

export interface Hazard {
  availability: DomainAvailability;
  points: HazardPoint[];
}

// ---------------------------------------------------------------------------
// 7. Risk — backend risk-engine presentation view
// ---------------------------------------------------------------------------
export interface SummitWindowAssessment {
  level: "go" | "caution" | "block" | "unknown";
  confidence: number;
  validTime: string | null;
  profile: string;
  altitudeMetres: number | null;
  factors: unknown[];
  inputs: Record<string, unknown>;
  basis: string;
  authority: "backend-risk-engine";
}

export interface Risk {
  summitWindow: SummitWindowAssessment;
  /** Reserved: broader multi-hazard risk Engine (not AI; presentation-layer only). */
  hazards: Hazard;
}

// ---------------------------------------------------------------------------
// 8. Communication — link states
// ---------------------------------------------------------------------------
export type CommunicationChannel = "satellite" | "mesh" | "4g" | "offline";

export interface CommunicationLink {
  channel: CommunicationChannel;
  qualityPct: number | null;
  latencyMs: number | null;
}

export interface Communication {
  availability: DomainAvailability;
  links: CommunicationLink[];
  primary: CommunicationChannel;
}

// ---------------------------------------------------------------------------
// 9. Device — bound terminal device states
// ---------------------------------------------------------------------------
export type DeviceKind = "ar-glasses" | "drone" | "weather-station" | "gps";

export interface Device {
  id: string;
  kind: DeviceKind;
  name: string;
  online: boolean;
  batteryPct: number | null;
  lastSeenAt: string | null;
}

export interface DeviceDomain {
  availability: DomainAvailability;
  items: Device[];
}

// ---------------------------------------------------------------------------
// 10. Mission — current task context
// ---------------------------------------------------------------------------
export type MissionKind = "summit" | "rescue" | "inspection" | "exploration";

export interface Mission {
  id: string;
  kind: MissionKind;
  name: string;
  startedAt: string | null;
  status: "planned" | "active" | "completed" | "paused";
}

export interface MissionDomain {
  availability: DomainAvailability;
  value: Mission | null;
}

// ---------------------------------------------------------------------------
// Everest OS root state (Phase 1 composition)
// ---------------------------------------------------------------------------
export interface EverestOsState {
  locale: Locale;
  environment: Environment;
  terrain: Terrain;
  weather: Weather;
  sensor: Sensor;
  route: Route;
  hazard: Hazard;
  risk: Risk;
  communication: Communication;
  devices: DeviceDomain;
  mission: MissionDomain;
}
