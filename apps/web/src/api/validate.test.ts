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

  it("keeps the summit when the peak node is present", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [],
      route: [],
      summit: {
        name: "Summit",
        latitude: 27.9880614,
        longitude: 86.92521,
        elevation_m: 8848.86,
        osm_ref: "164979149",
      },
    };
    const result = validateEverestRoute(payload);
    expect(result.summit?.elevation_m).toBe(8848.86);
    expect(result.summit?.osm_ref).toBe("164979149");
  });

  it("returns a null summit when the peak node is absent", () => {
    const base = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [],
      route: [],
    };
    expect(validateEverestRoute(base).summit).toBeNull();
    expect(validateEverestRoute({ ...base, summit: null }).summit).toBeNull();
  });

  it("rejects a summit with an out-of-range coordinate", () => {
    const payload = {
      source_id: "osm-overpass",
      dataset: "osm-south-col",
      camps: [],
      route: [],
      summit: {
        name: "Summit",
        latitude: 127.9880614,
        longitude: 86.92521,
        elevation_m: 8848.86,
        osm_ref: "164979149",
      },
    };
    expect(() => validateEverestRoute(payload)).toThrow(
      "camp coordinate invalid",
    );
  });
});
