import type { EverestRouteResponse } from "@/api/types";
import type { Route } from "@/types/schema";

export const RESERVED_ROUTE: Route = {
  availability: "reserved",
  id: "everest-south-route",
  name: "Everest South Col route",
  nodes: [],
  totalDistanceM: 0,
};

export function getRoute(): Route {
  return RESERVED_ROUTE;
}

export function routeFromApi(response: EverestRouteResponse): Route {
  return {
    availability: response.route.length > 0 ? "available" : "empty",
    id: response.source_id,
    name: response.dataset,
    nodes: response.route.map(([latitude, longitude], index) => ({
      index,
      latitude,
      longitude,
      altitudeM: null,
      label: null,
    })),
    totalDistanceM: 0,
  };
}
