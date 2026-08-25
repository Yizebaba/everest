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
  Color,
  defined,
  Entity,
  ImageryLayer,
  Ion,
  PolylineGraphics,
  Rectangle,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  SingleTileImageryProvider,
  Terrain,
  UrlTemplateImageryProvider,
  Viewer,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

import type { CanonicalWeatherRecord } from "@/api/types";
import type { EverestCamp } from "@/api/types";
import { AOI_CENTER } from "@/lib/geo";

// Optional Cesium ion token (gitignored via .env.local). When present, the
// scene enables Cesium World Terrain (real global terrain) and can load
// ion-hosted 3D Tiles. When absent, the scene renders on the WGS84 ellipsoid
// with OSM imagery only — no network calls to ion are made.
const CESIUM_ION_TOKEN = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN?.trim() ?? "";
if (typeof window !== "undefined" && CESIUM_ION_TOKEN) {
  Ion.defaultAccessToken = CESIUM_ION_TOKEN;
}

export interface EverestSceneProps {
  records: CanonicalWeatherRecord[];
  camps?: EverestCamp[];
  route?: [number, number][];
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

const CAMP_COLOR = "#FBBF24";

export function EverestScene({
  records,
  camps = [],
  route = [],
  onSelectRecord,
}: EverestSceneProps): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const entityByRecord = useRef(new Map<string, Entity>());
  const onSelectRef = useRef(onSelectRecord);
  onSelectRef.current = onSelectRecord;

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
      const options: ConstructorParameters<typeof Viewer>[1] = {
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
      };
      if (CESIUM_ION_TOKEN) {
        // Cesium World Terrain (requires a valid ion token). Falls back to
        // ellipsoid automatically if the asset stream errors.
        options.terrain = Terrain.fromWorldTerrain();
      }
      viewer = new Viewer(container, options);
      if (CESIUM_ION_TOKEN) {
        // Cesium World Imagery (ion-hosted Bing global imagery) replaces the
        // OSM raster base when an ion token is configured. See
        // EV-VIS-004 / docs/design for the base-map rationale.
        viewer.imageryLayers.add(ImageryLayer.fromWorldImagery({}));
      } else {
        // OSM standard raster tiles (interactive viewport-only use, per the OSMF
        // Tile Usage Policy). Attribution is shown in the scene footer.
        const baseLayer = new UrlTemplateImageryProvider({
          url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
          credit: "© OpenStreetMap contributors",
        });
        viewer.imageryLayers.addImageryProvider(baseLayer);
      }
      viewer.scene.camera.setView({
        destination: Cartesian3.fromDegrees(
          AOI_CENTER.longitude,
          AOI_CENTER.latitude,
          45000,
        ),
        orientation: { heading: 0, pitch: -Math.PI / 3.5, roll: 0 },
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
    if (!viewer || route.length < 2) {
      return;
    }
    const existing = viewer.entities.getById("osm-south-col-route");
    if (existing) {
      viewer.entities.remove(existing);
    }
    const positions = route.map(([latitude, longitude]) =>
      Cartesian3.fromDegrees(longitude, latitude, 0),
    );
    viewer.entities.add(
      new Entity({
        id: "osm-south-col-route",
        polyline: new PolylineGraphics({
          positions,
          width: 3,
          material: Color.fromCssColorString("#FBBF24").withAlpha(0.9),
          clampToGround: true,
        }),
      }),
    );
  }, [route, webglOk]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    // OSM South Col camp markers (EV-OSM-002). Re-synced whenever the camps
    // array changes so the scene stays consistent with the persisted snapshot.
    const existing = viewer.entities.getById("osm-camps");
    if (existing) {
      viewer.entities.remove(existing);
    }
    if (camps.length === 0) {
      return;
    }
    const campGroup = new Entity({
      id: "osm-camps",
    });
    for (const camp of camps) {
      viewer.entities.add(
        new Entity({
          id: `osm-camp-${camp.name}`,
          parent: campGroup,
          position: Cartesian3.fromDegrees(
            camp.longitude,
            camp.latitude,
            camp.elevation_m ?? 0,
          ),
          point: {
            pixelSize: 9,
            color: Color.fromCssColorString(CAMP_COLOR),
            outlineColor: Color.fromCssColorString("#0B0E14"),
            outlineWidth: 2,
          },
          label: {
            text: camp.name,
            font: "11px Inter, system-ui, sans-serif",
            fillColor: Color.fromCssColorString("#E6EAF2"),
            outlineColor: Color.fromCssColorString("#0B0E14"),
            outlineWidth: 2,
            pixelOffset: new Cartesian2(0, -14),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          description: `${camp.name} (OSM ${camp.osm_ref ?? "—"})`,
        }),
      );
    }
    return () => {
      if (!viewer.isDestroyed()) {
        viewer.entities.remove(campGroup);
      }
    };
  }, [camps, webglOk]);

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
    const layers = viewer.imageryLayers;
    for (let i = layers.length - 1; i >= 0; i -= 1) {
      const layer = layers.get(i);
      const provider = (
        layer as unknown as {
          _provider?: { url?: string };
        }
      )._provider;
      if (provider?.url?.includes("everest-rgb")) {
        layers.remove(layer);
      }
    }
    if (showSatellite) {
      try {
        const provider = new SingleTileImageryProvider({
          url: "/satellite/everest-rgb.png",
          rectangle: Rectangle.fromDegrees(86.8, 27.85, 87.05, 28.05),
          tileWidth: 512,
          tileHeight: 512,
        });
        const layer = viewer.imageryLayers.addImageryProvider(provider);
        layer.alpha = 1.0;
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
        .scene__controls button {
          background: #141a24;
          color: #e6eaf2;
          border: 1px solid #2c3a52;
          border-radius: 6px;
          padding: 6px 12px;
          font-size: 13px;
          cursor: pointer;
        }
        .scene__controls button:hover {
          border-color: #3b4c6b;
        }
        .scene__controls button[aria-pressed="true"] {
          background: #2c3a52;
          border-color: #38bdf8;
          color: #38bdf8;
        }
      `}</style>
    </div>
  );
}

function recordKey(record: CanonicalWeatherRecord): string {
  return `${record.source}-${record.timestamp}-${record.spatial_key}-${record.forecast_cycle}`;
}
