import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord } from "@/api/types";
import { scoreSummitRecord } from "./SummitWindowPanel";

const RECORD: CanonicalWeatherRecord = {
  record_type: "forecast",
  timestamp: "2026-08-24T06:00:00Z",
  latitude: 27.98806,
  longitude: 86.92528,
  altitude: 8848,
  spatial_key: "summit",
  source: "dwd-icon",
  model: "ICON",
  forecast_cycle: "2026-08-24T00:00:00Z",
  forecast_lead_time: 21600,
  quality_flags: ["clean"],
  wind_speed: 10,
  wind_direction: 200,
  temperature: -30,
  precipitation: 0,
  visibility: 20000,
};

describe("scoreSummitRecord", () => {
  it("scores clean records", () => {
    expect(scoreSummitRecord(RECORD)).toBe("GO");
  });

  it("never scores a dirty QC record", () => {
    for (const windSpeed of [10, 20, 30]) {
      expect(
        scoreSummitRecord({
          ...RECORD,
          wind_speed: windSpeed,
          quality_flags: ["stale"],
        }),
      ).toBeNull();
    }
    expect(scoreSummitRecord({ ...RECORD, quality_flags: [] })).toBeNull();
  });
});
