import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getCurrent, getWindField } from "./client";

const RECORD = {
  record_type: "observation",
  timestamp: "2026-08-24T06:00:00Z",
  latitude: 27.98806,
  longitude: 86.92528,
  altitude: 8848.86,
  spatial_key: "summit",
  source: "everest-aws",
  model: null,
  forecast_cycle: null,
  forecast_lead_time: null,
  quality_flags: ["clean"],
  wind_speed: 10,
  wind_direction: 250,
  temperature: -30,
  precipitation: 0,
  visibility: 20000,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("requests only the bounded backend wind-field endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
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
            latitude: [28],
            longitude: [86.8, 87.05],
            shape: [1, 2],
            order: "latitude_longitude_c",
            units: "m s-1",
            u: [1, 2],
            v: [3, 4],
            minimum: { u: 1, v: 3 },
            maximum: { u: 2, v: 4 },
            quality_flags: [],
            schema_version: 1,
          },
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getWindField();

    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/weather/wind-field",
    );
  });

  it("sends a correlation ID and validates a successful response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ records: [RECORD] }), {
        status: 200,
        headers: { "X-Correlation-ID": "response-id" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await getCurrent();

    expect(result.records).toHaveLength(1);
    const request = fetchMock.mock.calls[0];
    expect((request[1] as RequestInit).headers).toHaveProperty(
      "X-Correlation-ID",
    );
  });

  it("parses the project error envelope and response correlation ID", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "weather_unavailable",
              message: "Weather unavailable",
              correlation_id: "body-id",
            },
          }),
          {
            status: 503,
            headers: { "X-Correlation-ID": "header-id" },
          },
        ),
      ),
    );

    await expect(getCurrent()).rejects.toMatchObject({
      name: "ApiError",
      message: "Weather unavailable",
      correlationId: "header-id",
      status: 503,
      code: "weather_unavailable",
    });
  });

  it("parses FastAPI detail arrays", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [{ loc: ["query", "source"], msg: "invalid source" }],
          }),
          { status: 422, headers: { "X-Correlation-ID": "validation-id" } },
        ),
      ),
    );

    try {
      await getCurrent();
      throw new Error("expected request to fail");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect(error).toMatchObject({
        message: "query.source: invalid source",
        correlationId: "validation-id",
        status: 422,
        code: "validation_error",
      });
    }
  });

  it("wraps network failures with request correlation metadata", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    await expect(getCurrent()).rejects.toMatchObject({
      name: "ApiError",
      message: "offline",
      status: 0,
      code: "network_error",
    });
  });
});
