import type {
  CanonicalWeatherRecord,
  CurrentResponse,
  DataHealthResponse,
  EverestRouteResponse,
  ForecastResponse,
  ObservationsResponse,
  ProfileLabel,
  ProfileResponse,
  RiskResponse,
  SatelliteResponse,
  SourceHealthStatus,
  SourceLifecycleStatus,
  SourceFact,
  SourcesResponse,
  TerrainTileResponse,
} from "./types";

const RISK_LEVELS = new Set(["go", "caution", "block", "unknown"]);

const RECORD_TYPES = new Set([
  "forecast",
  "observation",
  "satellite",
  "derived",
]);
const LIFECYCLE_STATUSES = new Set<SourceLifecycleStatus>([
  "planned",
  "configured",
  "connected",
  "verified",
  "degraded",
  "disabled",
]);
const HEALTH_STATUSES = new Set<SourceHealthStatus>([
  "unknown",
  "healthy",
  "stale",
  "failed",
  "degraded",
  "disabled",
]);
type CoreField =
  | "wind_speed"
  | "wind_direction"
  | "temperature"
  | "precipitation"
  | "visibility";
const UTC_Z_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isUtcZ(value: unknown): value is string {
  return (
    typeof value === "string" &&
    UTC_Z_RE.test(value) &&
    !Number.isNaN(Date.parse(value))
  );
}

function requireNullableNumber(
  record: Record<string, unknown>,
  key: CoreField,
  minimum?: number,
  maximumExclusive?: number,
): void {
  if (!(key in record)) {
    throw new Error(`${key} missing`);
  }
  const value = record[key];
  if (value === null) {
    return;
  }
  if (
    !isFiniteNumber(value) ||
    (minimum !== undefined && value < minimum) ||
    (maximumExclusive !== undefined && value >= maximumExclusive)
  ) {
    throw new Error(`${key} invalid`);
  }
}

function validateOptionalNumber(
  record: Record<string, unknown>,
  key: string,
  minimum?: number,
  maximum?: number,
): void {
  const value = record[key];
  if (value === undefined || value === null) {
    return;
  }
  if (
    !isFiniteNumber(value) ||
    (minimum !== undefined && value < minimum) ||
    (maximum !== undefined && value > maximum)
  ) {
    throw new Error(`${key} invalid`);
  }
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
  if (!isUtcZ(record.timestamp)) {
    throw new Error("timestamp must be UTC ISO-8601 with trailing Z");
  }
  if (
    !isFiniteNumber(record.latitude) ||
    record.latitude < -90 ||
    record.latitude > 90 ||
    !isFiniteNumber(record.longitude) ||
    record.longitude < -180 ||
    record.longitude > 180
  ) {
    throw new Error("coordinate invalid");
  }
  if (!isFiniteNumber(record.altitude)) {
    throw new Error("altitude invalid");
  }
  if (
    typeof record.spatial_key !== "string" ||
    record.spatial_key.length === 0
  ) {
    throw new Error("spatial_key missing");
  }
  if (typeof record.source !== "string" || record.source.length === 0) {
    throw new Error("source missing");
  }
  if (
    !("model" in record) ||
    (record.model !== null && typeof record.model !== "string")
  ) {
    throw new Error("model invalid");
  }
  requireNullableNumber(record, "wind_speed", 0);
  requireNullableNumber(record, "wind_direction", 0, 360);
  requireNullableNumber(record, "temperature");
  requireNullableNumber(record, "precipitation", 0);
  requireNullableNumber(record, "visibility", 0);
  validateOptionalNumber(record, "pressure", 0);
  validateOptionalNumber(record, "relative_humidity", 0, 100);
  validateOptionalNumber(record, "dew_point");
  validateOptionalNumber(record, "cloud_cover", 0, 100);
  validateOptionalNumber(record, "cloud_base", 0);
  validateOptionalNumber(record, "cloud_top", 0);
  validateOptionalNumber(record, "snowfall", 0);
  validateOptionalNumber(record, "gust_speed", 0);
  if (
    !Array.isArray(record.quality_flags) ||
    !record.quality_flags.every((flag) => typeof flag === "string")
  ) {
    throw new Error("quality_flags must be a string array");
  }
  if (!("forecast_cycle" in record) || !("forecast_lead_time" in record)) {
    throw new Error("forecast identity missing");
  }
  if (record.record_type === "forecast") {
    if (typeof record.model !== "string" || record.model.length === 0) {
      throw new Error("forecast model invalid");
    }
    if (!isUtcZ(record.forecast_cycle)) {
      throw new Error("forecast_cycle invalid");
    }
    if (
      !isFiniteNumber(record.forecast_lead_time) ||
      record.forecast_lead_time < 0
    ) {
      throw new Error("forecast_lead_time invalid");
    }
    if (
      Date.parse(record.forecast_cycle as string) +
        record.forecast_lead_time * 1000 !==
      Date.parse(record.timestamp as string)
    ) {
      throw new Error("forecast identity inconsistent");
    }
  } else if (
    (record.forecast_cycle !== null && !isUtcZ(record.forecast_cycle)) ||
    (record.forecast_lead_time !== null &&
      (!isFiniteNumber(record.forecast_lead_time) ||
        record.forecast_lead_time < 0))
  ) {
    throw new Error("forecast identity invalid");
  }
  return record as unknown as CanonicalWeatherRecord;
}

export function validateRecords(payload: unknown): {
  records: CanonicalWeatherRecord[];
  warningCount: number;
} {
  const body = payload as { records?: unknown };
  if (!Array.isArray(body.records)) {
    throw new Error("response body missing records array");
  }
  const records: CanonicalWeatherRecord[] = [];
  let warningCount = 0;
  for (const value of body.records) {
    try {
      records.push(validateRecord(value));
    } catch {
      warningCount += 1;
    }
  }
  return { records, warningCount };
}

export function validateCurrent(payload: unknown): CurrentResponse {
  return validateRecords(payload);
}

export function validateForecast(payload: unknown): ForecastResponse {
  return validateRecords(payload);
}

export function validateRisk(payload: unknown): RiskResponse {
  const body = payload as { risk?: unknown };
  if (typeof body.risk !== "object" || body.risk === null) {
    throw new Error("response body missing risk object");
  }
  const risk = body.risk as Record<string, unknown>;
  if (!RISK_LEVELS.has(String(risk.level)))
    throw new Error("risk level invalid");
  if (
    !isFiniteNumber(risk.confidence) ||
    risk.confidence < 0 ||
    risk.confidence > 1
  ) {
    throw new Error("risk confidence invalid");
  }
  if (risk.valid_time !== null && !isUtcZ(risk.valid_time)) {
    throw new Error("risk valid_time invalid");
  }
  if (typeof risk.profile !== "string" || typeof risk.basis !== "string") {
    throw new Error("risk identity invalid");
  }
  if (risk.altitude_metres !== null && !isFiniteNumber(risk.altitude_metres)) {
    throw new Error("risk altitude invalid");
  }
  if (!Array.isArray(risk.factors)) throw new Error("risk factors invalid");
  if (
    typeof risk.inputs !== "object" ||
    risk.inputs === null ||
    Array.isArray(risk.inputs)
  ) {
    throw new Error("risk inputs invalid");
  }
  return { risk: risk as unknown as RiskResponse["risk"] };
}

export function validateProfile(payload: unknown): ProfileResponse {
  const body = payload as { profile?: unknown };
  if (typeof body.profile !== "string" || !isProfileLabel(body.profile)) {
    throw new Error("profile invalid");
  }
  const validated = validateRecords(payload);
  const profile = body.profile.toUpperCase() as ProfileLabel;
  if (
    validated.records.some(
      (record) =>
        record.route_profile !== undefined &&
        record.route_profile !== null &&
        record.route_profile.toUpperCase() !== profile,
    )
  ) {
    throw new Error("profile record label mismatch");
  }
  return { profile, ...validated };
}

export function validateSources(payload: unknown): SourcesResponse {
  const body = payload as { sources?: unknown };
  if (!Array.isArray(body.sources)) {
    throw new Error("response body missing sources array");
  }
  const sources = body.sources.map((value): SourceFact => {
    if (typeof value !== "object" || value === null) {
      throw new Error("source must be an object");
    }
    const source = value as Record<string, unknown>;
    if (typeof source.source_id !== "string" || source.source_id.length === 0) {
      throw new Error("source_id invalid");
    }
    if (!LIFECYCLE_STATUSES.has(source.status as SourceLifecycleStatus)) {
      throw new Error("source status invalid");
    }
    if (!HEALTH_STATUSES.has(source.health_status as SourceHealthStatus)) {
      throw new Error("source health invalid");
    }
    for (const key of ["last_success_at", "last_failure_at"] as const) {
      if (
        source[key] !== undefined &&
        source[key] !== null &&
        !isUtcZ(source[key])
      ) {
        throw new Error(`${key} invalid`);
      }
    }
    return source as unknown as SourceFact;
  });
  return { sources };
}

export function validateDataHealth(payload: unknown): DataHealthResponse {
  const body = payload as { sources?: unknown };
  if (!Array.isArray(body.sources)) {
    throw new Error("response body missing sources array");
  }
  return {
    sources: body.sources.map((value) => {
      if (typeof value !== "object" || value === null) {
        throw new Error("health source must be an object");
      }
      const source = value as Record<string, unknown>;
      if (
        typeof source.source_id !== "string" ||
        source.source_id.length === 0
      ) {
        throw new Error("source_id invalid");
      }
      if (!HEALTH_STATUSES.has(source.health_status as SourceHealthStatus)) {
        throw new Error("source health invalid");
      }
      for (const key of ["last_success_at", "last_failure_at"] as const) {
        if (
          source[key] !== undefined &&
          source[key] !== null &&
          !isUtcZ(source[key])
        ) {
          throw new Error(`${key} invalid`);
        }
      }
      return source as unknown as DataHealthResponse["sources"][number];
    }),
  };
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

function validateCamp(value: unknown): EverestRouteResponse["camps"][number] {
  if (typeof value !== "object" || value === null) {
    throw new Error("camp must be an object");
  }
  const camp = value as Record<string, unknown>;
  if (typeof camp.name !== "string" || camp.name.length === 0) {
    throw new Error("camp name invalid");
  }
  if (
    !isFiniteNumber(camp.latitude) ||
    camp.latitude < -90 ||
    camp.latitude > 90 ||
    !isFiniteNumber(camp.longitude) ||
    camp.longitude < -180 ||
    camp.longitude > 180
  ) {
    throw new Error("camp coordinate invalid");
  }
  validateOptionalNumber(camp, "elevation_m");
  for (const key of ["osm_ref"] as const) {
    if (
      camp[key] !== undefined &&
      camp[key] !== null &&
      typeof camp[key] !== "string"
    ) {
      throw new Error(`${key} invalid`);
    }
  }
  return camp as unknown as EverestRouteResponse["camps"][number];
}

export function validateEverestRoute(payload: unknown): EverestRouteResponse {
  const body = payload as Record<string, unknown>;
  if (typeof body.source_id !== "string" || body.source_id.length === 0) {
    throw new Error("source_id invalid");
  }
  if (typeof body.dataset !== "string" || body.dataset.length === 0) {
    throw new Error("dataset invalid");
  }
  if (!Array.isArray(body.camps)) {
    throw new Error("camps must be an array");
  }
  const camps = body.camps.map(validateCamp);
  if (!Array.isArray(body.route)) {
    throw new Error("route must be an array");
  }
  const route = body.route.map((value): [number, number] => {
    if (
      !Array.isArray(value) ||
      value.length !== 2 ||
      !isFiniteNumber(value[0]) ||
      !isFiniteNumber(value[1]) ||
      value[0] < -90 ||
      value[0] > 90 ||
      value[1] < -180 ||
      value[1] > 180
    ) {
      throw new Error("route vertex invalid");
    }
    return [value[0] as number, value[1] as number];
  });
  return {
    source_id: body.source_id,
    dataset: body.dataset,
    camps,
    route,
    // Absent or null means the OSM peak node has not been ingested; the caller
    // must leave the summit unmarked rather than assume a height for it.
    summit:
      body.summit === undefined || body.summit === null
        ? null
        : validateCamp(body.summit),
  };
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
