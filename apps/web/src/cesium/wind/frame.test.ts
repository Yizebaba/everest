import { describe, expect, it } from "vitest";

import type { WindFieldFrame } from "@/api/types";

import { selectRenderableWindFrame } from "./frame";

const FRAME: WindFieldFrame = {
  source: "ecmwf-ifs",
  model: "IFS",
  cycle: "2026-08-27T00:00:00Z",
  valid_time: "2026-08-27T06:00:00Z",
  lead_seconds: 21_600,
  level: 400,
  level_units: "hPa",
  bounds: { west: 86, south: 27, east: 88, north: 29 },
  latitude: [28],
  longitude: [87],
  shape: [1, 1],
  order: "latitude_longitude_c",
  units: "m s-1",
  u: [3],
  v: [4],
  minimum: { u: 3, v: 4 },
  maximum: { u: 3, v: 4 },
  quality_flags: [],
  schema_version: 1,
};

describe("selectRenderableWindFrame", () => {
  it("accepts the exact active-time frame", () => {
    expect(
      selectRenderableWindFrame(
        { status: "available", frame: FRAME },
        FRAME.valid_time,
      ),
    ).toBe(FRAME);
  });

  it("falls back when the returned frame does not match active time", () => {
    expect(
      selectRenderableWindFrame(
        { status: "available", frame: FRAME },
        "2026-08-27T12:00:00Z",
      ),
    ).toBeNull();
  });

  it("renders partial frames but falls back when no node is renderable", () => {
    expect(
      selectRenderableWindFrame({
        status: "available",
        frame: {
          ...FRAME,
          longitude: [87, 88],
          shape: [1, 2],
          u: [null, 2],
          v: [1, 3],
        },
      }),
    ).not.toBeNull();
    expect(
      selectRenderableWindFrame({
        status: "available",
        frame: { ...FRAME, u: [null], v: [4] },
      }),
    ).toBeNull();
  });
});
