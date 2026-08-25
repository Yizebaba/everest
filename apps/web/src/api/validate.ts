import type {
  CanonicalWeatherRecord,
  CurrentResponse,
  ForecastResponse,
  ObservationsResponse,
  ProfileLabel,
  ProfileResponse,
  SatelliteResponse,
  SourceFact,
  SourcesResponse,
  TerrainTileResponse,
} from "./types";

const RECORD_TYPES = new Set([
  "forecast",
  "observation",
  "satellite",
  "derived",
]);

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function validateRecord(value: unknown): CanonicalWeatherRecord {
  if (typeof value !== "object" || value === null) {
    throw new Error("record must be an object");
  }
  const record = value as Record<string, unknown>;
  if (
    typeof record.record_type !== "string" ||
    !RECORD_TYPES.has(record.record_type)
  ) {
    throw new Error("record_type invalid");
  }
  if (typeof record.timestamp !== "string" || !record.timestamp.endsWith("Z")) {
    throw new Error("timestamp must be UTC ISO-8601 with trailing Z");
  }
  if (!isFiniteNumber(record.latitude) || !isFiniteNumber(record.longitude)) {
    throw new Error("coordinate missing");
  }
  if (typeof record.source !== "string") {
    throw new Error("source missing");
  }
  if (!Array.isArray(record.quality_flags)) {
    throw new Error("quality_flags must be an array");
  }
  return record as unknown as CanonicalWeatherRecord;
}

export function validateRecords(payload: unknown): CanonicalWeatherRecord[] {
  const body = payload as { records?: unknown };
  if (!Array.isArray(body.records)) {
    throw new Error("response body missing records array");
  }
  return body.records.map(validateRecord);
}

export function validateCurrent(payload: unknown): CurrentResponse {
  return { records: validateRecords(payload) };
}

export function validateForecast(payload: unknown): ForecastResponse {
  return { records: validateRecords(payload) };
}

export function validateProfile(payload: unknown): ProfileResponse {
  const body = payload as ProfileResponse;
  return { profile: String(body.profile), records: validateRecords(payload) };
}

export function validateSources(payload: unknown): SourcesResponse {
  const body = payload as { sources?: unknown };
  if (!Array.isArray(body.sources)) {
    throw new Error("response body missing sources array");
  }
  return { sources: body.sources as SourceFact[] };
}

export function validateTerrainTile(payload: unknown): TerrainTileResponse {
  const body = payload as TerrainTileResponse;
  if (body.tile !== null && typeof body.tile !== "object") {
    throw new Error("tile must be object or null");
  }
  return body;
}

export function validateObservations(payload: unknown): ObservationsResponse {
  const body = payload as ObservationsResponse;
  return body;
}

export function validateSatellite(payload: unknown): SatelliteResponse {
  const body = payload as { segments?: unknown };
  if (!Array.isArray(body.segments)) {
    throw new Error("response body missing segments array");
  }
  return { segments: body.segments as SatelliteResponse["segments"] };
}

export const PROFILE_LABELS: readonly ProfileLabel[] = [
  "EBC",
  "C1",
  "C2",
  "C3",
  "C4",
  "SUMMIT",
];

export function isProfileLabel(value: string): value is ProfileLabel {
  return (PROFILE_LABELS as readonly string[]).includes(value.toUpperCase());
}
