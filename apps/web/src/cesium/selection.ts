import type { CanonicalWeatherRecord, EverestCamp } from "@/api/types";

export type RouteCoordinate = [number, number];

export type SceneSelection =
  | { kind: "weather"; record: CanonicalWeatherRecord }
  | { kind: "camp"; camp: EverestCamp }
  | {
      kind: "route";
      route: RouteCoordinate[];
      coordinate: RouteCoordinate;
    };

export interface SceneEntitySelections {
  weather: ReadonlyMap<string, CanonicalWeatherRecord>;
  camps: ReadonlyMap<string, EverestCamp>;
  routes: ReadonlyMap<string, RouteCoordinate[]>;
}

export interface PickCoordinate {
  latitude: number;
  longitude: number;
}

export function nearestRouteVertex(
  route: RouteCoordinate[],
  latitude: number,
  longitude: number,
): RouteCoordinate | null {
  let nearest: RouteCoordinate | null = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  for (const vertex of route) {
    const distance = (vertex[0] - latitude) ** 2 + (vertex[1] - longitude) ** 2;
    if (distance < nearestDistance) {
      nearest = vertex;
      nearestDistance = distance;
    }
  }
  return nearest;
}

export function sceneSelectionFromEntity(
  entityId: string | null,
  entities: SceneEntitySelections,
  pickedCoordinate?: PickCoordinate,
): SceneSelection | null {
  if (entityId === null) {
    return null;
  }
  const weather = entities.weather.get(entityId);
  if (weather) {
    return { kind: "weather", record: weather };
  }
  const camp = entities.camps.get(entityId);
  if (camp) {
    return { kind: "camp", camp };
  }
  const route = entities.routes.get(entityId);
  if (!route || route.length === 0) {
    return null;
  }
  const coordinate = pickedCoordinate
    ? nearestRouteVertex(
        route,
        pickedCoordinate.latitude,
        pickedCoordinate.longitude,
      )
    : route[0];
  return coordinate ? { kind: "route", route, coordinate } : null;
}
