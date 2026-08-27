import { describe, expect, it } from "vitest";

import { sceneSelectionFromEntityId } from "./selection";

describe("sceneSelectionFromEntityId", () => {
  it("classifies weather, camp, route and unknown entities", () => {
    expect(
      sceneSelectionFromEntityId("weather:key", new Set(["weather:key"])),
    ).toEqual({
      kind: "weather",
      recordKey: "weather:key",
    });
    expect(sceneSelectionFromEntityId("osm-camp-Camp 2", new Set())).toEqual({
      kind: "camp",
      campId: "osm-camp-Camp 2",
    });
    expect(
      sceneSelectionFromEntityId("osm-south-col-route", new Set()),
    ).toEqual({
      kind: "route",
      routeId: "osm-south-col-route",
    });
    expect(sceneSelectionFromEntityId("aoi-boundary", new Set())).toBeNull();
  });
});
