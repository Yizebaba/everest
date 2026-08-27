import { describe, expect, it } from "vitest";

import type { WindFieldFrame } from "@/api/types";

import { buildRegionalSeeds } from "./regional";

function frame(overrides: Partial<WindFieldFrame> = {}): WindFieldFrame {
  return {
    source: "ecmwf-ifs",
    model: "IFS",
    cycle: "2026-08-27T00:00:00Z",
    valid_time: "2026-08-27T06:00:00Z",
    lead_seconds: 21600,
    level: 400,
    level_units: "hPa",
    bounds: { west: 86.4, south: 27.5, east: 87.4, north: 28.5 },
    latitude: [28.5, 28.0, 27.5],
    longitude: [86.4, 86.9, 87.4],
    shape: [3, 3],
    order: "latitude_longitude_c",
    units: "m s-1",
    u: [0, 1, 2, 3, 4, 5, 6, 7, 8],
    v: [8, 7, 6, 5, 4, 3, 2, 1, 0],
    minimum: { u: 0, v: 0 },
    maximum: { u: 8, v: 8 },
    quality_flags: [],
    schema_version: 1,
    ...overrides,
  };
}

describe("buildRegionalSeeds", () => {
  it("seeds exact backend grid nodes without fabricating cell centers", () => {
    const seeds = buildRegionalSeeds(frame(), { stride: 1 });
    expect(seeds).toHaveLength(9);
    expect(seeds[0]).toEqual({
      longitude: 86.4,
      latitude: 28.5,
      u: 0,
      v: 8,
    });
    expect(seeds[4]).toEqual({
      longitude: 86.9,
      latitude: 28,
      u: 4,
      v: 4,
    });
  });

  it("respects a bounded maximum", () => {
    const seeds = buildRegionalSeeds(frame(), { stride: 1, maxSeeds: 2 });
    expect(seeds.length).toBeLessThanOrEqual(2);
  });

  it("skips only missing nodes while retaining remaining exact nodes", () => {
    const grid = frame();
    grid.u[0] = null;
    grid.u[4] = null;
    const seeds = buildRegionalSeeds(grid, { stride: 1 });
    expect(seeds).toHaveLength(7);
    expect(seeds).not.toContainEqual(expect.objectContaining({ u: null }));
  });

  it("yields empty seeds for a trivial grid", () => {
    const grid = frame({
      latitude: [28.0],
      longitude: [87.0],
      shape: [1, 1],
      u: [4],
      v: [4],
    });
    expect(buildRegionalSeeds(grid)).toEqual([
      { longitude: 87, latitude: 28, u: 4, v: 4 },
    ]);
  });

  it("never exceeds the hard 256 seed limit", () => {
    expect(buildRegionalSeeds(frame(), { maxSeeds: 10_000 })).toHaveLength(9);
    const latitude = Array.from({ length: 20 }, (_, index) => 28 + index / 100);
    const longitude = Array.from(
      { length: 20 },
      (_, index) => 87 + index / 100,
    );
    const values = Array.from({ length: 400 }, () => 1);
    expect(
      buildRegionalSeeds(
        frame({
          latitude,
          longitude,
          shape: [20, 20],
          u: values,
          v: values,
        }),
        { maxSeeds: 10_000 },
      ),
    ).toHaveLength(256);
  });

  it.each([
    ["stride", Number.NaN],
    ["stride", Number.POSITIVE_INFINITY],
    ["stride", Number.NEGATIVE_INFINITY],
    ["maxSeeds", Number.NaN],
    ["maxSeeds", Number.POSITIVE_INFINITY],
    ["maxSeeds", Number.NEGATIVE_INFINITY],
  ] as const)("rejects non-finite %s values", (option, value) => {
    expect(() => buildRegionalSeeds(frame(), { [option]: value })).toThrow(
      `${option} must be finite`,
    );
  });

  it("normalizes finite stride values to an integer within 1 through 64", () => {
    expect(buildRegionalSeeds(frame(), { stride: -1 })).toHaveLength(9);
    expect(buildRegionalSeeds(frame(), { stride: 1.9 })).toHaveLength(9);
    const latitude = Array.from({ length: 65 }, (_, index) => index);
    const values = Array.from({ length: 65 }, () => 1);
    expect(
      buildRegionalSeeds(
        frame({
          latitude,
          longitude: [87],
          shape: [65, 1],
          u: values,
          v: values,
        }),
        { stride: 65 },
      ),
    ).toHaveLength(2);
  });

  it("normalizes finite maxSeeds values to an integer within 1 through 256", () => {
    expect(buildRegionalSeeds(frame(), { maxSeeds: -1 })).toHaveLength(1);
    expect(buildRegionalSeeds(frame(), { maxSeeds: 2.9 })).toHaveLength(2);
    expect(buildRegionalSeeds(frame(), { maxSeeds: 257 })).toHaveLength(9);
  });
});
