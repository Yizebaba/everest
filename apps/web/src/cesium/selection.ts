export type SceneSelection =
  | { kind: "weather"; recordKey: string }
  | { kind: "camp"; campId: string }
  | { kind: "route"; routeId: string };

export function sceneSelectionFromEntityId(
  entityId: string,
  weatherIds: ReadonlySet<string>,
): SceneSelection | null {
  if (weatherIds.has(entityId)) {
    return { kind: "weather", recordKey: entityId };
  }
  if (entityId.startsWith("osm-camp-")) {
    return { kind: "camp", campId: entityId };
  }
  if (
    entityId === "osm-south-col-route" ||
    entityId.startsWith("route-elevation-")
  ) {
    return { kind: "route", routeId: entityId };
  }
  return null;
}
