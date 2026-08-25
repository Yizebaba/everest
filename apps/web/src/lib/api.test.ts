import { describe, expect, it } from "vitest";

import {
  isProfileLabel,
  validateDataHealth,
  validateProfile,
  validateRecords,
  validateSources,
} from "../api/validate";
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
  forecast_cycle: "2026-08-24T00:00:00Z",
  forecast_lead_time: 21600,
  quality_flags: ["clean"],
  wind_speed: 12,
  wind_direction: 250,
  temperature: -30.2,
  precipitation: 0,
  visibility: 22000,
};

describe("validateRecords", () => {
  it("accepts a valid record", () => {
    const result = validateRecords({ records: [VALID_RECORD] });
    expect(result.records).toHaveLength(1);
    expect(result.records[0].source).toBe("dwd-icon");
    expect(result.warningCount).toBe(0);
  });

  it("isolates invalid records while returning valid records and warning count", () => {
    const result = validateRecords({
      records: [VALID_RECORD, { ...VALID_RECORD, record_type: "bogus" }],
    });
    expect(result.records).toHaveLength(1);
    expect(result.warningCount).toBe(1);
  });

  it("isolates non-UTC timestamps", () => {
    const result = validateRecords({
      records: [{ ...VALID_RECORD, timestamp: "2026-08-24T06:00:00" }],
    });
    expect(result).toEqual({ records: [], warningCount: 1 });
  });

  it("requires nullable core keys and validates ranges", () => {
    const { visibility: _visibility, ...missingVisibility } = VALID_RECORD;
    const result = validateRecords({
      records: [
        missingVisibility,
        { ...VALID_RECORD, latitude: 91 },
        { ...VALID_RECORD, wind_direction: 360 },
      ],
    });
    expect(result.warningCount).toBe(3);
    expect(result.records).toHaveLength(0);
    void _visibility;
  });

  it("accepts required core keys when their values are null", () => {
    const result = validateRecords({
      records: [
        {
          ...VALID_RECORD,
          wind_speed: null,
          wind_direction: null,
          temperature: null,
          precipitation: null,
          visibility: null,
        },
      ],
    });
    expect(result.warningCount).toBe(0);
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

describe("profile and source validation", () => {
  it("validates and normalizes a complete profile response", () => {
    const result = validateProfile({
      profile: "summit",
      records: [{ ...VALID_RECORD, route_profile: "SUMMIT" }],
    });
    expect(result.profile).toBe("SUMMIT");
    expect(result.records).toHaveLength(1);
    expect(result.warningCount).toBe(0);
  });

  it("rejects invalid profile labels and mismatched record labels", () => {
    expect(() =>
      validateProfile({ profile: "CAMP", records: [VALID_RECORD] }),
    ).toThrow("profile");
    expect(() =>
      validateProfile({
        profile: "EBC",
        records: [{ ...VALID_RECORD, route_profile: "SUMMIT" }],
      }),
    ).toThrow("mismatch");
  });

  it("validates lifecycle and health enums with UTC Z timestamps", () => {
    expect(
      validateSources({
        sources: [
          {
            source_id: "dwd-icon",
            status: "verified",
            health_status: "healthy",
            last_success_at: "2026-08-24T06:00:00Z",
          },
        ],
      }).sources,
    ).toHaveLength(1);
    expect(
      validateDataHealth({
        sources: [
          {
            source_id: "dwd-icon",
            health_status: "unknown",
            last_success_at: null,
            last_failure_at: null,
          },
        ],
      }).sources,
    ).toHaveLength(1);
  });

  it("rejects unknown statuses and non-Z source timestamps", () => {
    expect(() =>
      validateSources({
        sources: [
          {
            source_id: "dwd-icon",
            status: "ready",
            health_status: "healthy",
          },
        ],
      }),
    ).toThrow("status");
    expect(() =>
      validateDataHealth({
        sources: [
          {
            source_id: "dwd-icon",
            health_status: "healthy",
            last_success_at: "2026-08-24T06:00:00+00:00",
          },
        ],
      }),
    ).toThrow("last_success_at");
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
