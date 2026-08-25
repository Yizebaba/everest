import { describe, expect, it } from "vitest";

import {
  AOI_CENTER,
  summitBasisRecord,
  vincentyDistanceMeters,
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
  it("picks the nearest record within 25 km, altitude as tie-break", () => {
    const records = [
      { latitude: 27.96, longitude: 86.9, altitude: 5000 },
      { latitude: 27.988, longitude: 86.925, altitude: 8700 },
      { latitude: 27.76, longitude: 86.6, altitude: 8900 },
    ];
    const basis = summitBasisRecord(records);
    expect(basis?.altitude).toBe(8700);
  });

  it("prefers a nearer lower record over a farther higher one", () => {
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
