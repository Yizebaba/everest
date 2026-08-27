import { describe, expect, it } from "vitest";

import type { CanonicalWeatherRecord, EverestCamp } from "@/api/types";
import {
  nearestRouteVertex,
  sceneSelectionFromEntity,
  type SceneEntitySelections,
} from "./selection";

const CAMP: EverestCamp = {
  name: "Camp 4S South Col",
  latitude: 27.9733654,
  longitude: 86.9302508,
  elevation_m: 7920,
  osm_ref: "576713400",
};

const WEATHER = {
  source: "dwd-icon",
  timestamp: "2026-08-27T00:00:00Z",
} as CanonicalWeatherRecord;

describe("sceneSelectionFromEntity", () => {
  it("returns the exact API camp object registered for a Cesium entity", () => {
    const entities: SceneEntitySelections = {
      weather: new Map(),
      camps: new Map([["render-id-17", CAMP]]),
      routes: new Map(),
    };

    const selection = sceneSelectionFromEntity("render-id-17", entities);

    expect(selection).toEqual({ kind: "camp", camp: CAMP });
    expect(selection?.kind === "camp" && selection.camp).toBe(CAMP);
  });

  it("returns the exact weather record and preserves provenance", () => {
    const entities: SceneEntitySelections = {
      weather: new Map([["opaque-weather-id", WEATHER]]),
      camps: new Map(),
      routes: new Map(),
    };

    const selection = sceneSelectionFromEntity("opaque-weather-id", entities);

    expect(selection?.kind === "weather" && selection.record).toBe(WEATHER);
  });

  it("selects the nearest real route vertex rather than an interpolated point", () => {
    const route: [number, number][] = [
      [27.98, 86.89],
      [27.975, 86.92],
      [27.97, 86.94],
    ];
    const entities: SceneEntitySelections = {
      weather: new Map(),
      camps: new Map(),
      routes: new Map([["opaque-route-id", route]]),
    };

    const selection = sceneSelectionFromEntity("opaque-route-id", entities, {
      latitude: 27.974,
      longitude: 86.921,
    });

    expect(selection?.kind).toBe("route");
    expect(selection?.kind === "route" && selection.route).toBe(route);
    expect(selection?.kind === "route" && selection.coordinate).toBe(route[1]);
    expect(nearestRouteVertex(route, 27.974, 86.921)).toBe(route[1]);
  });

  it("clears selection for the background or an unregistered entity", () => {
    const entities: SceneEntitySelections = {
      weather: new Map(),
      camps: new Map(),
      routes: new Map(),
    };

    expect(sceneSelectionFromEntity(null, entities)).toBeNull();
    expect(sceneSelectionFromEntity("aoi-boundary", entities)).toBeNull();
  });
});
