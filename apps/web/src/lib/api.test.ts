import { describe, expect, it } from "vitest";

import { validateRecords, isProfileLabel } from "../api/validate";
import {
  formatTemperature,
  formatVisibility,
  formatWindDirection,
} from "./units";

const VALID_RECORD = {
  record_type: "forecast",
  timestamp: "2026-08-24T06:00:00Z",
  latitude: 27.98806,
  longitude: 86.92528,
  altitude: 5000,
  spatial_key: "28.0_87.0",
  source: "dwd-icon",
  model: "ICON",
  quality_flags: ["clean"],
  temperature: -30.2,
};

describe("validateRecords", () => {
  it("accepts a valid record", () => {
    const records = validateRecords({ records: [VALID_RECORD] });
    expect(records).toHaveLength(1);
    expect(records[0].source).toBe("dwd-icon");
  });

  it("rejects an invalid record_type", () => {
    expect(() =>
      validateRecords({ records: [{ ...VALID_RECORD, record_type: "bogus" }] }),
    ).toThrow("record_type");
  });

  it("rejects a non-UTC timestamp", () => {
    expect(() =>
      validateRecords({
        records: [{ ...VALID_RECORD, timestamp: "2026-08-24T06:00:00" }],
      }),
    ).toThrow("timestamp");
  });

  it("ignores unknown fields but requires source", () => {
    const missingSource = { ...VALID_RECORD, source: undefined };
    expect(() => validateRecords({ records: [missingSource] })).toThrow(
      "source",
    );
  });

  it("rejects a missing records array", () => {
    expect(() => validateRecords({})).toThrow("records");
  });
});

describe("isProfileLabel", () => {
  it("accepts all six labels case-insensitively", () => {
    expect(isProfileLabel("EBC")).toBe(true);
    expect(isProfileLabel("summit")).toBe(true);
  });

  it("rejects unknown labels", () => {
    expect(isProfileLabel("CAMP")).toBe(false);
  });
});

describe("unit formatting", () => {
  it("formats temperature with unit", () => {
    expect(formatTemperature(-30.2)).toContain("°C");
    expect(formatTemperature(null)).toBe("unavailable");
  });

  it("formats visibility in meters", () => {
    expect(formatVisibility(22000)).toBe(`22000\u00A0m`);
  });

  it("formats wind direction in degrees", () => {
    expect(formatWindDirection(259)).toBe("259°");
  });
});
