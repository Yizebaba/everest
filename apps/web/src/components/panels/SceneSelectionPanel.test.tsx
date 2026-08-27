import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  BackendRiskAssessment,
  CanonicalWeatherRecord,
  EverestCamp,
} from "@/api/types";
import type { SceneSelection } from "@/cesium/selection";
import {
  nearestDisplayedWeatherRecord,
  SceneSelectionPanel,
} from "./SceneSelectionPanel";

const camp = (name: string): EverestCamp => ({
  name,
  latitude: 27.9733654,
  longitude: 86.9302508,
  elevation_m: 7920,
  osm_ref: "576713400",
});

const weather = (
  latitude: number,
  longitude: number,
  source: string,
): CanonicalWeatherRecord => ({
  record_type: "forecast",
  timestamp: "2026-08-27T00:00:00Z",
  latitude,
  longitude,
  altitude: 7900,
  spatial_key: source,
  source,
  model: source,
  forecast_cycle: "2026-08-27T00:00:00Z",
  forecast_lead_time: 0,
  quality_flags: ["clean"],
  wind_speed: 12,
  wind_direction: 180,
  temperature: -22,
  precipitation: 0,
  visibility: 10000,
  relative_humidity: 47.6,
});

const risk: BackendRiskAssessment = {
  level: "caution",
  confidence: 0.8,
  valid_time: "2026-08-27T00:00:00Z",
  profile: "SUMMIT",
  altitude_metres: 8848,
  factors: [],
  inputs: {},
  basis: "persisted_canonical_weather",
};

describe("SceneSelectionPanel", () => {
  it("uses the nearest currently displayed canonical weather record", () => {
    const far = weather(27.9, 86.8, "far-model");
    const near = weather(27.974, 86.931, "near-model");

    expect(
      nearestDisplayedWeatherRecord([far, near], 27.9733654, 86.9302508),
    ).toBe(near);

    const html = renderToStaticMarkup(
      <SceneSelectionPanel
        selection={{ kind: "camp", camp: camp("Camp 4S South Col") }}
        records={[far, near]}
        risk={risk}
      />,
    );
    expect(html).toContain("Nearest model grid point");
    expect(html).toContain("near-model");
    expect(html).toContain("27.973365°");
    expect(html).toContain("86.930251°");
    expect(html).toContain("Humidity");
    expect(html).toContain("48 %");
  });

  it("does not fabricate weather or risk for a non-C4 camp", () => {
    const selection: SceneSelection = {
      kind: "camp",
      camp: camp("Camp 1S"),
    };
    const html = renderToStaticMarkup(
      <SceneSelectionPanel selection={selection} records={[]} risk={risk} />,
    );

    expect(nearestDisplayedWeatherRecord([], 27.9, 86.9)).toBeNull();
    expect(html).toContain("No displayed canonical weather record");
    expect(html).toContain("Unavailable for this selection");
    expect(html).toContain("non-authoritative");
    expect(html).not.toContain("CAUTION");
    expect(html).not.toContain("-22");
  });

  it("shows backend risk for C4 and SUMMIT selections only", () => {
    for (const name of ["Camp 4S South Col", "Summit"] as const) {
      const html = renderToStaticMarkup(
        <SceneSelectionPanel
          selection={{ kind: "camp", camp: camp(name) }}
          records={[]}
          risk={risk}
        />,
      );
      expect(html).toContain("CAUTION");
      expect(html).toContain("persisted_canonical_weather");
    }
  });

  it("renders the exact API camp objects as keyboard-accessible buttons", () => {
    const c1 = camp("Camp 1S");
    const c2 = camp("Camp 2S");
    const html = renderToStaticMarkup(
      <SceneSelectionPanel
        selection={null}
        records={[]}
        camps={[c1, c2]}
        summit={camp("Summit")}
      />,
    );

    expect(html).toContain('<button type="button">Camp 1S</button>');
    expect(html).toContain('<button type="button">Camp 2S</button>');
    expect(html).toContain('<button type="button">Summit</button>');
  });

  it("renders a keyboard route button from exact API vertices", () => {
    const route: [number, number][] = [
      [27.99, 86.85],
      [27.98, 86.9],
    ];
    const html = renderToStaticMarkup(
      <SceneSelectionPanel selection={null} records={[]} route={route} />,
    );

    expect(html).toContain('<button type="button">South Col route</button>');
  });
});
