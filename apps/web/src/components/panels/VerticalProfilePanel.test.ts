import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord } from "@/api/types";
import { pressureLevels } from "./VerticalProfilePanel";

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
