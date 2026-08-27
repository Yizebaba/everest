import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord } from "@/api/types";
import { createEverestOsState } from "@/domains";
import { riskFromApi } from "@/domains/risk";
import { routeFromApi } from "@/domains/route";
import { terrainFromTile } from "@/domains/terrain";
import { weatherFromApi } from "@/domains/weather";

const canonical: CanonicalWeatherRecord = {
  record_type: "forecast",
  timestamp: "2026-08-27T06:00:00Z",
  latitude: 27.988,
  longitude: 86.925,
  altitude: 8848,
  spatial_key: "summit:300hpa",
  source: "future-provider",
  model: "MODEL",
  forecast_cycle: "2026-08-27T00:00:00Z",
  forecast_lead_time: 21600,
  quality_flags: ["clean"],
  wind_speed: 12,
  wind_direction: 220,
  temperature: -28,
  precipitation: 0,
  visibility: null,
};

describe("Phase 1 presentation adapters", () => {
  it("retains a reference to the complete canonical weather record", () => {
    const weather = weatherFromApi(
      { records: [canonical], warningCount: 0 },
      { records: [], warningCount: 0 },
    );

    expect(weather.current[0].canonical).toBe(canonical);
    expect(weather.current[0].source).toBe("future-provider");
  });

  it("does not present a tile maximum as point elevation", () => {
    const terrain = terrainFromTile(
      {
        tile: {
          tile_name: "N27E086",
          crs: "EPSG:4326",
          bounds: [86, 27, 87, 28],
          resolution_degrees: 0.001,
          min_elevation: 100,
          max_elevation: 8848,
          retrieved_at: "2026-08-27T00:00:00Z",
        },
      },
      27.9,
      86.9,
    );

    expect(terrain.sample.elevationM).toBeNull();
  });

  it("maps route coordinates without inventing altitude", () => {
    const route = routeFromApi({
      source_id: "osm",
      dataset: "south-col",
      camps: [],
      route: [[27.9, 86.9]],
      summit: null,
    });

    expect(route.nodes[0].altitudeM).toBeNull();
  });

  it("marks unimplemented domains reserved and empty", () => {
    const state = createEverestOsState("en");

    expect(state.sensor).toMatchObject({
      availability: "reserved",
      readings: [],
    });
    expect(state.hazard).toMatchObject({
      availability: "reserved",
      points: [],
    });
    expect(state.communication).toMatchObject({
      availability: "reserved",
      links: [],
    });
    expect(state.devices).toEqual({ availability: "reserved", items: [] });
    expect(state.mission).toEqual({ availability: "reserved", value: null });
  });

  it("adapts the backend risk response without rescoring weather", () => {
    const risk = riskFromApi({
      risk: {
        level: "caution",
        confidence: 0.75,
        valid_time: canonical.timestamp,
        profile: "SUMMIT",
        altitude_metres: 8848,
        factors: [{ name: "wind", value: 12, risk: "go" }],
        inputs: { source: "ecmwf-ifs", model: "IFS" },
        basis: "persisted_canonical_weather",
      },
    });

    expect(risk.summitWindow.level).toBe("caution");
    expect(risk.summitWindow.authority).toBe("backend-risk-engine");
  });
});
