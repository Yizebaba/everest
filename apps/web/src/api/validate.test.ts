import { describe, expect, it } from "vitest";

import {
  validateEverestRoute,
  validateRisk,
  validateWindField,
} from "./validate";

const WIND_FIELD = {
  status: "available",
  frame: {
    source: "ecmwf-ifs",
    model: "IFS",
    cycle: "2026-08-27T00:00:00Z",
    valid_time: "2026-08-27T06:00:00Z",
    lead_seconds: 21600,
    level: 400,
    level_units: "hPa",
    bounds: { west: 86.8, south: 27.85, east: 87.05, north: 28.05 },
    latitude: [27.85, 28.05],
    longitude: [86.8, 87.05],
    shape: [2, 2],
    order: "latitude_longitude_c",
    units: "m s-1",
    u: [1, 2, 3, 4],
    v: [4, 3, 2, 1],
    minimum: { u: 1, v: 1 },
    maximum: { u: 4, v: 4 },
    quality_flags: [],
    schema_version: 1,
  },
};

describe("validateWindField", () => {
  it("accepts a bounded, flattened wind frame", () => {
    expect(validateWindField(WIND_FIELD)).toEqual(WIND_FIELD);
  });

  it("accepts an explicit unavailable envelope", () => {
    const unavailable = {
      status: "unavailable",
      reason: "not_configured",
      frame: null,
    };
    expect(validateWindField(unavailable)).toEqual(unavailable);
  });

  it("rejects dimensions whose product does not match flattened arrays", () => {
    expect(() =>
      validateWindField({
        ...WIND_FIELD,
        frame: { ...WIND_FIELD.frame, shape: [2, 3] },
      }),
    ).toThrow("wind frame shape invalid");
  });

  it("rejects flattened arrays whose length does not match the shape", () => {
    expect(() =>
      validateWindField({
        ...WIND_FIELD,
        frame: { ...WIND_FIELD.frame, v: [1, 2, 3] },
      }),
    ).toThrow("wind arrays must match frame dimensions");
  });

  it("rejects non-finite flattened values", () => {
    expect(() =>
      validateWindField({
        ...WIND_FIELD,
        frame: { ...WIND_FIELD.frame, u: [1, 2, Number.NaN, 4] },
      }),
    ).toThrow("u must contain finite numbers or null");
  });

  it("rejects unbounded frame dimensions before allocating GPU resources", () => {
    expect(() =>
      validateWindField({
        ...WIND_FIELD,
        frame: {
          ...WIND_FIELD.frame,
          latitude: [28],
          longitude: Array.from({ length: 1001 }, (_, index) => index / 10),
          shape: [1, 1001],
          u: [],
          v: [],
        },
      }),
    ).toThrow("wind frame dimensions out of bounds");
  });

  it("rejects inverted geographic bounds", () => {
    expect(() =>
      validateWindField({
        ...WIND_FIELD,
        frame: {
          ...WIND_FIELD.frame,
          bounds: { ...WIND_FIELD.frame.bounds, east: 86.7 },
        },
      }),
    ).toThrow("wind frame bounds invalid");
  });
});

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
    expect(() => validateEverestRoute(payload)).toThrow("route vertex invalid");
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

describe("validateRisk", () => {
  it("accepts the bounded backend risk engine response", () => {
    const result = validateRisk({
      risk: {
        level: "go",
        confidence: 0.9,
        valid_time: "2026-08-27T06:00:00Z",
        profile: "SUMMIT",
        altitude_metres: 8848,
        factors: [],
        inputs: { source: "ecmwf-ifs" },
        basis: "persisted_canonical_weather",
      },
    });

    expect(result.risk.level).toBe("go");
  });

  it("rejects fabricated risk levels", () => {
    expect(() =>
      validateRisk({
        risk: {
          level: "safe",
          confidence: 1,
          valid_time: null,
          profile: "SUMMIT",
          altitude_metres: null,
          factors: [],
          inputs: {},
          basis: "no_persisted_record",
        },
      }),
    ).toThrow("risk level invalid");
  });
});
