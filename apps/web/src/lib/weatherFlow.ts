import type { CanonicalWeatherRecord } from "@/api/types";
import { withinAoi } from "@/lib/geo";

export function selectMapRecords(
  currentRecords: CanonicalWeatherRecord[],
  forecastRecords: CanonicalWeatherRecord[],
  activeTime: string | null,
): CanonicalWeatherRecord[] {
  const records =
    activeTime === null
      ? currentRecords
      : forecastRecords.filter((record) => record.timestamp === activeTime);
  return records.filter((record) =>
    withinAoi(record.latitude, record.longitude),
  );
}
