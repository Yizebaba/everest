import { describe, expect, it } from "vitest";

import type { WindFieldFrame } from "@/api/types";

import { destroyWindFieldLayer, WindFieldLayer } from "./WindFieldLayer";

const FRAME: WindFieldFrame = {
  source: "ecmwf-ifs",
  model: "IFS",
  cycle: "2026-08-27T00:00:00Z",
  valid_time: "2026-08-27T06:00:00Z",
  lead_seconds: 21600,
  level: 400,
  level_units: "hPa",
  bounds: { west: 86, south: 27, east: 87, north: 28 },
  latitude: [27],
  longitude: [86],
  shape: [1, 1],
  order: "latitude_longitude_c",
  units: "m s-1",
  u: [1],
  v: [2],
  minimum: { u: 1, v: 2 },
  maximum: { u: 1, v: 2 },
  quality_flags: [],
  schema_version: 1,
};

const CAPABILITIES = {
  webgl2: true,
  floatTexture: true,
  colorBufferFloat: true,
};

describe("WindFieldLayer.destroy", () => {
  it("is safe when the owning scene has already been destroyed", () => {
    const scene = Object.create(null) as { primitives: never };
    Object.defineProperty(scene, "primitives", {
      get: () => {
        throw new Error("This object was destroyed");
      },
    });
    const layer = new WindFieldLayer(scene as never, FRAME, CAPABILITIES);

    expect(() => layer.destroy()).not.toThrow();
    expect(layer.isDestroyed()).toBe(true);
  });

  it("allows repeated cleanup after scene teardown", () => {
    const scene = Object.create(null) as { primitives: never };
    Object.defineProperty(scene, "primitives", {
      get: () => {
        throw new Error("This object was destroyed");
      },
    });
    const layer = new WindFieldLayer(scene as never, FRAME, CAPABILITIES);

    destroyWindFieldLayer(layer);
    expect(() => destroyWindFieldLayer(layer)).not.toThrow();
  });
});
