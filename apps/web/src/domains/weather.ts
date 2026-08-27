import type {
  CanonicalWeatherRecord,
  CurrentResponse,
  ForecastResponse,
} from "@/api/types";
import type { Weather, WeatherRecord } from "@/types/schema";

export function weatherFromApi(
  current: CurrentResponse,
  forecast: ForecastResponse,
): Weather {
  const toRecord = (record: CanonicalWeatherRecord): WeatherRecord => ({
    timestamp: record.timestamp,
    source: record.source as WeatherRecord["source"],
    model: record.model,
    recordType: record.record_type,
    spatialKey: record.spatial_key,
    qualityFlags: record.quality_flags,
    canonical: record,
    temperatureC: record.temperature ?? null,
    windSpeedMs: record.wind_speed ?? null,
    windDirectionDeg: record.wind_direction ?? null,
    precipitationMm: record.precipitation ?? null,
    visibilityM: record.visibility ?? null,
  });
  return {
    current: (current.records ?? []).map(toRecord),
    forecast: (forecast.records ?? []).map(toRecord),
    streamlines: [],
  };
}
