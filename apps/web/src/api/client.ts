import { config } from "@/config/env";
import type {
  CurrentResponse,
  DataHealthResponse,
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
  validateDataHealth,
  validateForecast,
  validateObservations,
  validateProfile,
  validateSatellite,
  validateSources,
  validateTerrainTile,
} from "./validate";

export class ApiError extends Error {
  readonly correlationId: string;
  readonly status: number;
  readonly code: string;

  constructor(options: {
    message: string;
    correlationId: string;
    status: number;
    code: string;
  }) {
    super(options.message);
    this.name = "ApiError";
    this.correlationId = options.correlationId;
    this.status = options.status;
    this.code = options.code;
  }
}

interface ErrorEnvelope {
  error?: {
    code?: unknown;
    message?: unknown;
    correlation_id?: unknown;
  };
  detail?: unknown;
}

function detailMessage(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "object" && item !== null) {
          const issue = item as { loc?: unknown; msg?: unknown };
          const location = Array.isArray(issue.loc)
            ? issue.loc.map(String).join(".")
            : "request";
          return typeof issue.msg === "string"
            ? `${location}: ${issue.msg}`
            : location;
        }
        return String(item);
      })
      .join("; ");
  }
  return null;
}

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
  let response: Response;
  try {
    response = await fetch(url, {
      headers: { "X-Correlation-ID": correlationId },
    });
  } catch (error) {
    throw new ApiError({
      message:
        error instanceof Error ? error.message : "Network request failed",
      correlationId,
      status: 0,
      code: "network_error",
    });
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const body = (payload ?? {}) as ErrorEnvelope;
    const envelope = body.error;
    const responseCorrelationId = response.headers.get("X-Correlation-ID");
    throw new ApiError({
      message:
        (typeof envelope?.message === "string" && envelope.message) ||
        detailMessage(body.detail) ||
        `HTTP ${response.status}`,
      correlationId:
        responseCorrelationId ??
        (typeof envelope?.correlation_id === "string"
          ? envelope.correlation_id
          : correlationId),
      status: response.status,
      code:
        typeof envelope?.code === "string"
          ? envelope.code
          : response.status === 422
            ? "validation_error"
            : "http_error",
    });
  }
  try {
    return validate(payload);
  } catch (error) {
    throw new ApiError({
      message:
        error instanceof Error ? error.message : "invalid API response shape",
      correlationId: response.headers.get("X-Correlation-ID") ?? correlationId,
      status: response.status,
      code: "invalid_response",
    });
  }
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

export function getDataHealth(): Promise<DataHealthResponse> {
  return request("/api/data-health", {}, validateDataHealth);
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
