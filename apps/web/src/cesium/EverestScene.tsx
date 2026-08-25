"use client";

// Cesium resolves its Assets/Workers/Widgets relative to CESIUM_BASE_URL.
// They are copied to /public/cesium so the browser loads them over http,
// not from node_modules (which browsers block as file://).
if (typeof window !== "undefined") {
  (window as unknown as { CESIUM_BASE_URL?: string }).CESIUM_BASE_URL =
    "/cesium/";
}

import { useEffect, useRef, useState } from "react";
import {
  Cartesian2,
  Cartesian3,
  Cesium3DTileset,
  Color,
  defined,
  Entity,
  Rectangle,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  SingleTileImageryProvider,
  UrlTemplateImageryProvider,
  Viewer,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

import type {
  CanonicalWeatherRecord,
  SatelliteSegment,
  TerrainTileResponse,
} from "@/api/types";
import { AOI_CENTER } from "@/lib/geo";

export interface EverestSceneProps {
  records: CanonicalWeatherRecord[];
  terrainTile: TerrainTileResponse | null;
  satelliteSegments: SatelliteSegment[];
  onSelectRecord?: (record: CanonicalWeatherRecord | null) => void;
}

const SOURCE_COLORS: Record<string, string> = {
  "ecmwf-ifs": "#38BDF8",
  "ecmwf-aifs": "#818CF8",
  "noaa-gfs": "#C084FC",
  "dwd-icon": "#2DD4BF",
  "everest-aws": "#FB923C",
  himawari: "#F472B6",
  "copernicus-dem": "#94A3B8",
};

export function EverestScene({
  records,
  onSelectRecord,
}: EverestSceneProps): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const terrainTilesetRef = useRef<Cesium3DTileset | null>(null);
  const entityByRecord = useRef(new Map<string, Entity>());
  const onSelectRef = useRef(onSelectRecord);
  onSelectRef.current = onSelectRecord;

  const [showTerrain, setShowTerrain] = useState(true);
  const [showSatellite, setShowSatellite] = useState(false);
  const [webglOk] = useState(() => {
    try {
      const canvas = document.createElement("canvas");
      return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (!webglOk) {
      return undefined;
    }
    const container = containerRef.current;
    if (!container) {
      return undefined;
    }
    let viewer: Viewer | undefined;
    try {
      // OSM standard raster tiles (interactive viewport-only use, per the OSMF
      // Tile Usage Policy). Attribution is shown in the scene footer.
      viewer = new Viewer(container, {
        baseLayer: false,
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        infoBox: false,
        fullscreenButton: false,
      });
      const baseLayer = new UrlTemplateImageryProvider({
        url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        credit: "© OpenStreetMap contributors",
      });
      viewer.imageryLayers.addImageryProvider(baseLayer);
      viewer.scene.camera.setView({
        destination: Cartesian3.fromDegrees(
          AOI_CENTER.longitude,
          AOI_CENTER.latitude,
          230000,
        ),
        orientation: { heading: 0, pitch: -Math.PI / 2, roll: 0 },
      });
    } catch (error) {
      console.error("Cesium viewer init failed:", error);
      return undefined;
    }
    viewerRef.current = viewer;

    void (async () => {
      try {
        const response = await fetch("/aoi.geojson");
        const geo = (await response.json()) as {
          geometry?: { type?: string; coordinates?: unknown };
        };
        const geometry = geo.geometry;
        if (
          geometry?.type !== "Polygon" ||
          !Array.isArray(geometry.coordinates)
        ) {
          return;
        }
        const ring = geometry.coordinates[0] as [number, number][];
        const positions = ring.map(([lon, lat]) =>
          Cartesian3.fromDegrees(lon, lat, 0),
        );
        viewer.entities.add(
          new Entity({
            id: "aoi-boundary",
            polygon: {
              hierarchy: positions,
              material: Color.fromCssColorString("#94A3B8").withAlpha(0.08),
              outline: true,
              outlineColor: Color.fromCssColorString("#94A3B8"),
            },
          }),
        );
      } catch {
        // AOI overlay is best-effort; the scene still renders.
      }
    })();

    return () => {
      viewer?.destroy();
      viewerRef.current = null;
    };
  }, [webglOk]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const toRemove: Entity[] = [];
    entityByRecord.current.forEach((entity, key) => {
      if (!records.some((record) => recordKey(record) === key)) {
        toRemove.push(entity);
      }
    });
    toRemove.forEach((entity) => {
      viewer.entities.remove(entity);
      entityByRecord.current.delete(entity.id);
    });
    for (const record of records) {
      const key = recordKey(record);
      if (entityByRecord.current.has(key)) {
        continue;
      }
      const entity = new Entity({
        id: key,
        position: Cartesian3.fromDegrees(
          record.longitude,
          record.latitude,
          record.altitude,
        ),
        point: {
          pixelSize: 7,
          color: Color.fromCssColorString(
            SOURCE_COLORS[record.source] ?? "#9AA5B8",
          ),
        },
        description: `${record.source} · ${record.timestamp}`,
      });
      viewer.entities.add(entity);
      entityByRecord.current.set(key, entity);
    }
  }, [records]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    if (terrainTilesetRef.current) {
      viewer.scene.primitives.remove(terrainTilesetRef.current);
      terrainTilesetRef.current = null;
    }
    if (showTerrain) {
      // Cesium resource/worker wiring can fail under webpack; never let it
      // crash the whole page — the scene degrades to the base view instead.
      try {
        const tileset = new Cesium3DTileset({
          url: "/tiles/tileset.json",
          maximumScreenSpaceError: 16,
        } as never);
        terrainTilesetRef.current = tileset;
        viewer.scene.primitives.add(tileset);
        const tilesetAny = tileset as unknown as {
          readyPromise?: Promise<unknown>;
          boundingSphere?: { center: Cartesian3 };
        };
        void tilesetAny.readyPromise?.then(() => {
          if (tilesetAny.boundingSphere) {
            viewer.camera.flyTo({
              destination: tilesetAny.boundingSphere.center,
            });
          }
        });
      } catch (error) {
        console.error("terrain tileset load failed:", error);
      }
    }
  }, [showTerrain]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const layers = viewer.imageryLayers;
    for (let i = layers.length - 1; i >= 0; i -= 1) {
      const layer = layers.get(i);
      const provider = (layer as unknown as {
        _provider?: { url?: string };
      })._provider;
      if (provider?.url?.includes("everest-rgb")) {
        layers.remove(layer);
      }
    }
    if (showSatellite) {
      try {
        const provider = new SingleTileImageryProvider({
          url: "/satellite/everest-rgb.png",
          rectangle: Rectangle.fromDegrees(86.8, 27.85, 87.05, 28.05),
        });
        const layer = viewer.imageryLayers.addImageryProvider(provider);
        layer.alpha = 0.85;
      } catch (error) {
        console.error("satellite imagery load failed:", error);
      }
    }
  }, [showSatellite]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: { position: Cartesian2 }) => {
      const picked = viewer.scene.pick(movement.position);
      if (!defined(picked) || !picked.id) {
        onSelectRef.current?.(null);
        return;
      }
      const record = records.find((r) => recordKey(r) === picked.id.id);
      onSelectRef.current?.(record ?? null);
    }, ScreenSpaceEventType.LEFT_CLICK);
    return () => {
      handler.destroy();
    };
  }, [records]);

  return (
    <div className="scene">
      {!webglOk ? (
        <div className="scene__fallback" role="status">
          3D map requires WebGL. Data panels remain available.
        </div>
      ) : (
        <>
          <div
            ref={containerRef}
            className="scene__canvas"
            aria-label="Everest 3D scene"
          />
          <div className="scene__controls" role="group" aria-label="Layers">
            <button
              type="button"
              aria-pressed={showTerrain}
              onClick={() => setShowTerrain((v) => !v)}
            >
              Terrain
            </button>
            <button
              type="button"
              aria-pressed={showSatellite}
              onClick={() => setShowSatellite((v) => !v)}
            >
              Satellite
            </button>
          </div>
        </>
      )}
      <style jsx>{`
        .scene {
          position: relative;
          width: 100%;
          height: 100%;
        }
        .scene__canvas {
          width: 100%;
          height: 100%;
        }
        .scene__fallback {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #9aa5b8;
        }
        .scene__controls {
          position: absolute;
          top: 12px;
          left: 12px;
          display: flex;
          gap: 8px;
        }
      `}</style>
    </div>
  );
}

function recordKey(record: CanonicalWeatherRecord): string {
  return `${record.source}-${record.timestamp}-${record.spatial_key}`;
}
