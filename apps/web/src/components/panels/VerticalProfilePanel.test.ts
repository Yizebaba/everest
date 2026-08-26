import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord } from "@/api/types";
import { pressureLevels, profileRows } from "./VerticalProfilePanel";

function record(
  partial: Partial<CanonicalWeatherRecord>,
): CanonicalWeatherRecord {
  return {
    record_type: "forecast",
    timestamp: "2026-08-24T00:00:00Z",
    latitude: 27.98806,
    longitude: 86.92528,
    altitude: 5000,
    spatial_key: "ifs:0p25:28.0:87.0:500hpa",
    source: "ecmwf-ifs",
    model: "IFS",
    forecast_cycle: "2026-08-24T00:00:00Z",
    forecast_lead_time: 0,
    quality_flags: ["clean"],
    wind_speed: 5,
    wind_direction: 90,
    temperature: -5,
    precipitation: null,
    visibility: null,
    ...partial,
  };
}

describe("pressureLevels", () => {
  it("filters out non-pressure-level records", () => {
    const result = pressureLevels([
      record({ spatial_key: "ifs:0p25:28.0:87.0:surface" }),
      record({ spatial_key: "ifs:0p25:28.0:87.0:300hpa" }),
    ]);
    expect(result).toHaveLength(1);
    expect(result[0].spatial_key).toContain("300hpa");
  });

  it("sorts pressure levels by altitude ascending", () => {
    const result = pressureLevels([
      record({ altitude: 9797, spatial_key: "ifs:300hpa" }),
      record({ altitude: 1559, spatial_key: "ifs:850hpa" }),
      record({ altitude: 5888, spatial_key: "ifs:500hpa" }),
    ]);
    expect(result.map((r) => r.altitude)).toEqual([1559, 5888, 9797]);
  });

  it("returns empty when no pressure-level records", () => {
    expect(pressureLevels([record({ spatial_key: "ifs:surface" })])).toEqual(
      [],
    );
  });
});

describe("profileRows", () => {
  const camp = record({
    altitude: 7920,
    route_profile: "C4",
    spatial_key: "ifs:0p25:28.0:87.0:C4@7920m:interp400-300hpa",
  });
  const level = record({
    altitude: 9797,
    spatial_key: "ifs:0p25:28.0:87.0:300hpa",
  });

  it("names a camp row after its route profile", () => {
    const [row] = profileRows([camp]);
    expect(row.label).toBe("C4");
  });

  it("marks an interpolated camp row as interpolated", () => {
    expect(profileRows([camp])[0].interpolated).toBe(true);
  });

  it("labels a raw model level with its pressure and does not mark it", () => {
    const [row] = profileRows([level]);
    expect(row.label).toBe("300 hPa");
    expect(row.interpolated).toBe(false);
  });

  it("keeps one time column, the one nearest the active time", () => {
    const rows = profileRows(
      [
        record({ timestamp: "2026-08-24T00:00:00Z", altitude: 5888 }),
        record({ timestamp: "2026-08-24T12:00:00Z", altitude: 5888 }),
        record({ timestamp: "2026-08-25T00:00:00Z", altitude: 5888 }),
      ],
      "2026-08-24T13:00:00Z",
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].record.timestamp).toBe("2026-08-24T12:00:00Z");
  });

  it("falls back to the earliest column without a usable active time", () => {
    const records = [
      record({ timestamp: "2026-08-25T00:00:00Z" }),
      record({ timestamp: "2026-08-24T00:00:00Z" }),
    ];
    expect(profileRows(records)[0].record.timestamp).toBe(
      "2026-08-24T00:00:00Z",
    );
    expect(profileRows(records, "not-a-time")[0].record.timestamp).toBe(
      "2026-08-24T00:00:00Z",
    );
  });

  it("orders the column lowest first and drops surface rows", () => {
    const rows = profileRows([
      level,
      camp,
      record({ altitude: 10, spatial_key: "ifs:0p25:28.0:87.0:surface" }),
    ]);
    expect(rows.map((r) => r.label)).toEqual(["C4", "300 hPa"]);
  });

  it("returns empty when there are no pressure-level records", () => {
    expect(profileRows([record({ spatial_key: "ifs:surface" })])).toEqual([]);
  });
});
