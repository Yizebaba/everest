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
  forecast_cycle?: string | null;
  forecast_lead_time?: number | null;
  route_profile?: string | null;
  quality_flags: string[];
  wind_speed?: number | null;
  wind_direction?: number | null;
  temperature?: number | null;
  precipitation?: number | null;
  visibility?: number | null;
  pressure?: number | null;
  relative_humidity?: number | null;
  dew_point?: number | null;
  cloud_cover?: number | null;
  cloud_base?: number | null;
  cloud_top?: number | null;
  snowfall?: number | null;
  gust_speed?: number | null;
}

export interface CurrentResponse {
  records: CanonicalWeatherRecord[];
}

export interface ForecastResponse {
  records: CanonicalWeatherRecord[];
}

export type ProfileLabel = "EBC" | "C1" | "C2" | "C3" | "C4" | "SUMMIT";

export interface ProfileResponse {
  profile: string;
  records: CanonicalWeatherRecord[];
}

export interface SourceFact {
  source_id: string;
  status: string;
  health_status: string;
  last_success_at?: string | null;
  last_failure_at?: string | null;
}

export interface SourcesResponse {
  sources: SourceFact[];
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
