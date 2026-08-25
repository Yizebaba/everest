import { describe, expect, it } from "vitest";

import { validateEverestRoute } from "./validate";

describe("validateEverestRoute", () => {
  it("accepts a valid route payload", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [
        {
          name: "Everest Base Camp",
          latitude: 27.9996646,
          longitude: 86.8487946,
          elevation_m: 5364,
          osm_ref: "5225912921",
        },
      ],
      route: [
        [27.9988062, 86.865107],
        [27.9987493, 86.8673166],
      ],
    };
    const result = validateEverestRoute(payload);
    expect(result.camps).toHaveLength(1);
    expect(result.camps[0].name).toBe("Everest Base Camp");
    expect(result.route).toHaveLength(2);
    expect(result.route[0]).toEqual([27.9988062, 86.865107]);
  });

  it("accepts null elevation_m and osm_ref", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [
        {
          name: "Camp 1S",
          latitude: 27.9864173,
          longitude: 86.8765224,
          elevation_m: null,
          osm_ref: null,
        },
      ],
      route: [],
    };
    const result = validateEverestRoute(payload);
    expect(result.camps[0].elevation_m).toBeNull();
    expect(result.camps[0].osm_ref).toBeNull();
  });

  it("rejects a missing camps array", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      route: [],
    };
    expect(() => validateEverestRoute(payload)).toThrow(
      "camps must be an array",
    );
  });

  it("rejects an out-of-range route vertex", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [],
      route: [[95, 86.9]],
    };
    expect(() => validateEverestRoute(payload)).toThrow(
      "route vertex invalid",
    );
  });

  it("rejects a missing source_id", () => {
    const payload = {
      dataset: "osm-south-col",
      camps: [],
      route: [],
    };
    expect(() => validateEverestRoute(payload)).toThrow("source_id invalid");
  });
});
