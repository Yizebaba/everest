import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord } from "@/api/types";
import { selectMapRecords } from "./weatherFlow";

function record(timestamp: string, source: string): CanonicalWeatherRecord {
  return {
    record_type: "forecast",
    timestamp,
    latitude: 27.98806,
    longitude: 86.92528,
    altitude: 8848,
    spatial_key: source,
    source,
    model: "MODEL",
    forecast_cycle: "2026-08-24T00:00:00Z",
    forecast_lead_time: 21600,
    quality_flags: ["clean"],
    wind_speed: 10,
    wind_direction: 200,
    temperature: -30,
    precipitation: 0,
    visibility: 20000,
  };
}

describe("selectMapRecords", () => {
  it("uses current records only when active time is null", () => {
    const current = [record("2026-08-24T05:00:00Z", "current")];
    const forecast = [record("2026-08-24T06:00:00Z", "forecast")];
    expect(selectMapRecords(current, forecast, null)).toEqual(current);
  });

  it("uses forecast records matching active time", () => {
    const forecast = [
      record("2026-08-24T06:00:00Z", "one"),
      record("2026-08-24T09:00:00Z", "two"),
    ];
    expect(
      selectMapRecords([], forecast, "2026-08-24T09:00:00Z").map(
        (item) => item.source,
      ),
    ).toEqual(["two"]);
  });
});
