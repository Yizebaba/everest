export type RecordType = "forecast" | "observation" | "satellite" | "derived";

export interface CanonicalWeatherRecord {
  record_type: RecordType;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude: number;
  spatial_key: string;
  source: string;
  model: string | null;
  forecast_cycle: string | null;
  forecast_lead_time: number | null;
  route_profile?: string | null;
  quality_flags: string[];
  wind_speed: number | null;
  wind_direction: number | null;
  temperature: number | null;
  precipitation: number | null;
  visibility: number | null;
  pressure?: number | null;
  relative_humidity?: number | null;
  dew_point?: number | null;
  cloud_cover?: number | null;
  cloud_base?: number | null;
  cloud_top?: number | null;
  snowfall?: number | null;
  gust_speed?: number | null;
}

export interface ValidatedRecordsResponse {
  records: CanonicalWeatherRecord[];
  warningCount: number;
}

export type CurrentResponse = ValidatedRecordsResponse;

export type ForecastResponse = ValidatedRecordsResponse;

export type ProfileLabel = "EBC" | "C1" | "C2" | "C3" | "C4" | "SUMMIT";

export interface ProfileResponse {
  profile: string;
  records: CanonicalWeatherRecord[];
  warningCount: number;
}

export type SourceLifecycleStatus =
  "planned" | "configured" | "connected" | "verified" | "degraded" | "disabled";

export type SourceHealthStatus =
  "unknown" | "healthy" | "stale" | "failed" | "degraded" | "disabled";

export interface SourceFact {
  source_id: string;
  status: SourceLifecycleStatus;
  health_status: SourceHealthStatus;
  last_success_at?: string | null;
  last_failure_at?: string | null;
}

export interface SourcesResponse {
  sources: SourceFact[];
}

export interface HealthFact {
  source_id: string;
  health_status: SourceHealthStatus;
  last_success_at?: string | null;
  last_failure_at?: string | null;
}

export interface DataHealthResponse {
  sources: HealthFact[];
}

export interface TerrainTileResponse {
  tile: {
    tile_name: string;
    crs: string;
    bounds: [number, number, number, number];
    resolution_degrees: number;
    min_elevation: number;
    max_elevation: number;
    retrieved_at: string;
  } | null;
}

export interface ObservationCurrent {
  timestamp: string;
  station: string;
  temperature_c: number | null;
  relative_humidity: number | null;
  precipitation: number | null;
  weather_code: string | null;
  missing: boolean;
  quality_flags: string[];
}

export interface ObservationsResponse {
  observations: Record<string, ObservationCurrent>;
}

export interface SatelliteSegment {
  timestamp: string;
  band: number;
  segment: number;
  satellite_name: string;
  observation_area: string;
  size_bytes: number;
}

export interface SatelliteResponse {
  segments: SatelliteSegment[];
}

export interface EverestCamp {
  name: string;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
  osm_ref: string | null;
}

export interface EverestRouteResponse {
  source_id: string;
  dataset: string;
  camps: EverestCamp[];
  route: [number, number][];
  // Null until the OSM peak node has been ingested. The scene leaves the summit
  // unmarked in that case rather than drawing a hard-coded 8848 m point.
  summit: EverestCamp | null;
}

export interface BackendRiskAssessment {
  level: "go" | "caution" | "block" | "unknown";
  confidence: number;
  valid_time: string | null;
  profile: string;
  altitude_metres: number | null;
  factors: unknown[];
  inputs: Record<string, unknown>;
  basis: string;
}

export interface RiskResponse {
  risk: BackendRiskAssessment;
}

/** A bounded, single-level native lon/lat grid returned by the backend. */
export interface WindFieldFrame {
  source: string;
  model: string;
  cycle: string;
  valid_time: string;
  lead_seconds: number;
  level: number;
  level_units: string;
  bounds: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  latitude: number[];
  longitude: number[];
  shape: [latitude: number, longitude: number];
  order: "latitude_longitude_c";
  units: string;
  /** Eastward wind in m/s, flattened with longitude varying fastest. */
  u: Array<number | null>;
  /** Northward wind in m/s, using the same layout as `u`. */
  v: Array<number | null>;
  minimum: { u: number | null; v: number | null };
  maximum: { u: number | null; v: number | null };
  quality_flags: string[];
  schema_version: 1;
}

export type WindFieldResponse =
  | { status: "available"; reason?: never; frame: WindFieldFrame }
  | { status: "unavailable"; reason: string; frame: null };
