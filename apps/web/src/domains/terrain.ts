import type { Terrain, TerrainTileMeta } from "@/types/schema";
import type { TerrainTileResponse } from "@/api/types";

export function terrainFromTile(
  tile: TerrainTileResponse,
  latitude: number,
  longitude: number,
): Terrain {
  const meta: TerrainTileMeta | null = tile.tile
    ? {
        tileName: tile.tile.tile_name,
        crs: tile.tile.crs,
        bounds: tile.tile.bounds,
        resolutionDegrees: tile.tile.resolution_degrees,
        minElevationM: tile.tile.min_elevation,
        maxElevationM: tile.tile.max_elevation,
        retrievedAt: tile.tile.retrieved_at,
      }
    : null;
  return {
    sourceId: "copernicus-dem",
    dataset: "glo30",
    tile: meta,
    sample: {
      latitude,
      longitude,
      // Tile extrema describe the entire raster and are not a point sample.
      elevationM: null,
    },
    profile: [],
  };
}
