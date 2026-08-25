import { config } from "@/config/env";
import type {
  CurrentResponse,
  ForecastResponse,
  ObservationsResponse,
  ProfileLabel,
  ProfileResponse,
  SatelliteResponse,
  SourcesResponse,
  TerrainTileResponse,
} from "./types";
import {
  validateCurrent,
  validateForecast,
  validateObservations,
  validateProfile,
  validateSatellite,
  validateSources,
  validateTerrainTile,
} from "./validate";

async function request<T>(
  path: string,
  params: Record<string, string | number | undefined>,
  validate: (payload: unknown) => T,
): Promise<T> {
  const url = new URL(`${config.apiBaseUrl}${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  const correlationId = crypto.randomUUID();
  const response = await fetch(url, {
    headers: { "X-Correlation-ID": correlationId },
  });
  const payload = await response.json();
  if (!response.ok) {
    const detail =
      (payload as { detail?: string } | undefined)?.detail ??
      `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return validate(payload);
}

export function getCurrent(source?: string): Promise<CurrentResponse> {
  return request("/api/weather/current", { source }, validateCurrent);
}

export function getForecast(
  start?: string,
  end?: string,
  source?: string,
): Promise<ForecastResponse> {
  return request(
    "/api/weather/forecast",
    { start, end, source },
    validateForecast,
  );
}

export function getProfile(label: ProfileLabel): Promise<ProfileResponse> {
  return request(`/api/weather/profile?profile=${label}`, {}, validateProfile);
}

export function getSources(): Promise<SourcesResponse> {
  return request("/api/weather/sources", {}, validateSources);
}

export function getDataHealth(): Promise<SourcesResponse> {
  return request("/api/data-health", {}, validateSources);
}

export function getTerrainTile(
  latitude: number,
  longitude: number,
): Promise<TerrainTileResponse> {
  return request(
    "/api/terrain/tile",
    { latitude, longitude },
    validateTerrainTile,
  );
}

export function getObservations(): Promise<ObservationsResponse> {
  return request("/api/observations/current", {}, validateObservations);
}

export function getSatellite(band?: number): Promise<SatelliteResponse> {
  return request("/api/satellite/segments", { band }, validateSatellite);
}
