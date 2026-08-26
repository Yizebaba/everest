import { describe, expect, it } from "vitest";

import {
  AOI_CENTER,
  METERS_PER_DEGREE_LATITUDE,
  compassPoint,
  metersToDegrees,
  oxygenFractionAtAltitude,
  slopeDegrees,
  summitBasisRecord,
  vincentyDistanceMeters,
  windVector,
  withinAoi,
} from "./geo";
import { isUtcIso, validateUtcRange } from "./utc";

describe("vincentyDistanceMeters", () => {
  it("returns ~0 for identical coordinates", () => {
    expect(
      vincentyDistanceMeters(27.98806, 86.92528, 27.98806, 86.92528),
    ).toBeLessThan(1);
  });

  it("returns a large distance across the globe", () => {
    const distance = vincentyDistanceMeters(27.98806, 86.92528, 0, 0);
    expect(distance).toBeGreaterThan(9_000_000);
    expect(distance).toBeLessThan(10_000_000);
  });
});

describe("withinAoi", () => {
  it("accepts the AOI center", () => {
    expect(withinAoi(AOI_CENTER.latitude, AOI_CENTER.longitude)).toBe(true);
  });

  it("rejects a point ~2000 km away", () => {
    expect(withinAoi(20, 90)).toBe(false);
  });
});

describe("summitBasisRecord", () => {
  it("picks the freshest record within 25 km", () => {
    const records = [
      {
        latitude: 27.96,
        longitude: 86.9,
        altitude: 5000,
        timestamp: "2026-08-24T00:00:00Z",
      },
      {
        latitude: 27.988,
        longitude: 86.925,
        altitude: 8700,
        timestamp: "2026-08-25T06:00:00Z",
      },
      {
        latitude: 27.76,
        longitude: 86.6,
        altitude: 8900,
        timestamp: "2026-08-23T00:00:00Z",
      },
    ];
    const basis = summitBasisRecord(records);
    expect(basis?.altitude).toBe(8700);
  });

  it("uses distance as tie-break when timestamps are equal", () => {
    const records = [
      {
        latitude: 27.96,
        longitude: 86.9,
        altitude: 5000,
        timestamp: "2026-08-25T06:00:00Z",
      },
      {
        latitude: 27.988,
        longitude: 86.925,
        altitude: 8700,
        timestamp: "2026-08-25T06:00:00Z",
      },
      {
        latitude: 27.76,
        longitude: 86.6,
        altitude: 8900,
        timestamp: "2026-08-25T06:00:00Z",
      },
    ];
    const basis = summitBasisRecord(records);
    expect(basis?.altitude).toBe(8700);
  });

  it("prefers the freshest record over a nearer older one", () => {
    const records = [
      {
        latitude: 27.9881,
        longitude: 86.9253,
        altitude: 4000,
        timestamp: "2026-08-26T12:00:00Z",
      },
      {
        latitude: 27.77,
        longitude: 86.7,
        altitude: 6500,
        timestamp: "2026-08-25T00:00:00Z",
      },
    ];
    const basis = summitBasisRecord(records);
    expect(basis?.altitude).toBe(4000);
  });

  it("falls back to nearest when records have no timestamps", () => {
    const records = [
      { latitude: 27.9881, longitude: 86.9253, altitude: 4000 },
      { latitude: 27.77, longitude: 86.7, altitude: 6500 },
    ];
    const basis = summitBasisRecord(records);
    expect(basis?.altitude).toBe(4000);
  });

  it("returns null when no record is within 25 km", () => {
    expect(
      summitBasisRecord([{ latitude: 20, longitude: 90, altitude: 1000 }]),
    ).toBeNull();
  });
});

describe("oxygenFractionAtAltitude", () => {
  it("returns ~100% at sea level", () => {
    expect(oxygenFractionAtAltitude(0)).toBeCloseTo(1, 3);
  });

  it("returns roughly 50% at ~5,500 m (Everest Base Camp area)", () => {
    expect(oxygenFractionAtAltitude(5364)).toBeCloseTo(0.53, 1);
  });

  it("returns roughly 33% near the summit (~8,800 m)", () => {
    expect(oxygenFractionAtAltitude(8848)).toBeCloseTo(0.35, 1);
  });

  it("decays monotonically with altitude", () => {
    expect(oxygenFractionAtAltitude(3000)).toBeGreaterThan(
      oxygenFractionAtAltitude(6000),
    );
    expect(oxygenFractionAtAltitude(6000)).toBeGreaterThan(
      oxygenFractionAtAltitude(9000),
    );
  });
});

describe("windVector", () => {
  it("maps a north wind (0 deg, blowing from north) to -y (toward south)", () => {
    const { x, y } = windVector(0);
    expect(Math.abs(x)).toBeLessThan(1e-9);
    expect(y).toBeCloseTo(-1, 6);
  });

  it("maps a west wind (270 deg, blowing from west) to +x (toward east)", () => {
    const { x, y } = windVector(270);
    expect(x).toBeCloseTo(1, 6);
    expect(Math.abs(y)).toBeLessThan(1e-9);
  });

  it("produces a unit-length vector for an arbitrary direction", () => {
    const { x, y } = windVector(123);
    expect(Math.hypot(x, y)).toBeCloseTo(1, 6);
  });
});

describe("compassPoint", () => {
  it("names the cardinal bearings", () => {
    expect(compassPoint(0)).toBe("N");
    expect(compassPoint(90)).toBe("E");
    expect(compassPoint(180)).toBe("S");
    expect(compassPoint(270)).toBe("W");
  });

  it("names a sixteenth-point bearing", () => {
    expect(compassPoint(157)).toBe("SSE");
    expect(compassPoint(116)).toBe("ESE");
  });

  it("wraps a full turn and a negative bearing back to north", () => {
    expect(compassPoint(360)).toBe("N");
    expect(compassPoint(-1)).toBe("N");
    expect(compassPoint(720)).toBe("N");
  });

  it("rounds the sector rather than truncating it", () => {
    // 11.24 deg is still nearer north than north-north-east; 11.26 is not.
    expect(compassPoint(11.24)).toBe("N");
    expect(compassPoint(11.26)).toBe("NNE");
  });
});

describe("metersToDegrees", () => {
  it("scales a northward offset by metres per degree of latitude", () => {
    const { deltaLatitude } = metersToDegrees(27.98806, 0, 50);
    expect(deltaLatitude).toBeCloseTo(50 / METERS_PER_DEGREE_LATITUDE, 12);
  });

  it("widens an eastward offset by 1/cos(latitude) at Everest", () => {
    const { deltaLongitude, deltaLatitude } = metersToDegrees(27.98806, 50, 50);
    // At 28 degN a degree of longitude is ~0.883 of a degree of latitude, so the
    // same 50 m spans more degrees east than north.
    expect(deltaLongitude).toBeGreaterThan(deltaLatitude);
    expect(deltaLongitude / deltaLatitude).toBeCloseTo(
      1 / Math.cos((27.98806 * Math.PI) / 180),
      6,
    );
  });

  it("treats east and north as equal on the equator", () => {
    const { deltaLongitude, deltaLatitude } = metersToDegrees(0, 50, 50);
    expect(deltaLongitude).toBeCloseTo(deltaLatitude, 12);
  });

  it("reports no eastward offset at a pole instead of an infinity", () => {
    expect(metersToDegrees(90, 50, 0).deltaLongitude).toBe(0);
  });

  it("keeps the sign of a westward or southward offset", () => {
    const { deltaLongitude, deltaLatitude } = metersToDegrees(
      27.98806,
      -50,
      -50,
    );
    expect(deltaLongitude).toBeLessThan(0);
    expect(deltaLatitude).toBeLessThan(0);
  });
});

describe("slopeDegrees", () => {
  it("returns 0 on flat terrain", () => {
    expect(slopeDegrees(0, 50)).toBe(0);
  });

  it("returns 45 deg when rise equals run", () => {
    expect(slopeDegrees(50, 50)).toBeCloseTo(45, 9);
  });

  it("treats a descent as equally steep as the matching ascent", () => {
    expect(slopeDegrees(-30, 50)).toBeCloseTo(slopeDegrees(30, 50), 12);
  });

  it("reports the Lhotse Face band as steep but under vertical", () => {
    const angle = slopeDegrees(40, 50);
    expect(angle).toBeGreaterThan(38);
    expect(angle).toBeLessThan(40);
  });
});

describe("utc", () => {
  it("accepts UTC Z timestamps", () => {
    expect(isUtcIso("2026-08-24T06:00:00Z")).toBe(true);
  });

  it("rejects naive datetimes", () => {
    expect(isUtcIso("2026-08-24T06:00:00")).toBe(false);
  });

  it("rejects a non-zero UTC offset range", () => {
    expect(validateUtcRange("2026-08-24T06:00:00+05:45", undefined)).toContain(
      "start must be UTC",
    );
  });

  it("rejects reversed ranges", () => {
    expect(
      validateUtcRange("2026-08-24T09:00:00Z", "2026-08-24T06:00:00Z"),
    ).toBe("start must not exceed end");
  });
});
