import { describe, expect, it } from "vitest";

import type { WindFieldFrame } from "@/api/types";

import { adaptWindFieldFrame } from "./data";

const FRAME: WindFieldFrame = {
  source: "ecmwf-ifs",
  model: "IFS",
  cycle: "2026-08-27T00:00:00Z",
  valid_time: "2026-08-27T06:00:00Z",
  lead_seconds: 21600,
  level: 400,
  level_units: "hPa",
  bounds: {
    west: 86,
    south: 27,
    east: 88,
    north: 29,
  },
  latitude: [27, 28],
  longitude: [86, 87, 88],
  shape: [2, 3],
  order: "latitude_longitude_c",
  units: "m s-1",
  u: [-2, 0, 1, 2, 3, 4],
  v: [4, 3, 2, 1, 0, -1],
  minimum: { u: -2, v: -1 },
  maximum: { u: 4, v: 4 },
  quality_flags: [],
  schema_version: 1,
};

describe("adaptWindFieldFrame", () => {
  it("packs latitude and altitude into a RED/FLOAT texture height", () => {
    const adapted = adaptWindFieldFrame(FRAME);

    expect([adapted.width, adapted.height, adapted.levelCount]).toEqual([
      3, 2, 1,
    ]);
    expect(adapted.u).toBeInstanceOf(Float32Array);
    expect(adapted.v).toBeInstanceOf(Float32Array);
  });

  it("derives axis intervals and component ranges without mutating the frame", () => {
    const adapted = adaptWindFieldFrame(FRAME);

    expect(adapted.interval).toEqual([1, 2, 0]);
    expect(adapted.uRange).toEqual([-2, 4]);
    expect(adapted.vRange).toEqual([-1, 4]);
    adapted.u[0] = 99;
    expect(FRAME.u[0]).toBe(-2);
  });

  it("refuses to fabricate vectors for missing cells", () => {
    expect(() =>
      adaptWindFieldFrame({ ...FRAME, u: [null, 0, 1, 2, 3, 4] }),
    ).toThrow("wind frame contains missing values");
  });
});
