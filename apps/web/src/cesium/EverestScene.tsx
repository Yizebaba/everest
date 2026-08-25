"use client";

import { useEffect, useRef, useState } from "react";
import {
  Cartesian2,
  Cartesian3,
  Cesium3DTileset,
  Color,
  defined,
  Entity,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
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
  satelliteSegments,
  onSelectRecord,
}: EverestSceneProps): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
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
    const viewer = new Viewer(container, {
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
    viewer.scene.camera.setView({
      destination: Cartesian3.fromDegrees(
        AOI_CENTER.longitude,
        AOI_CENTER.latitude,
        230000,
      ),
      orientation: { heading: 0, pitch: -Math.PI / 2, roll: 0 },
    });
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
      viewer.destroy();
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
    const terrainEntities = viewer.entities.values.filter((entity) =>
      String(entity.id).startsWith("terrain-"),
    );
    terrainEntities.forEach((entity) => viewer.entities.remove(entity));
    const existing = viewer.scene.primitives._primitives.find(
      (primitive: { id?: string }) => primitive?.id === "everest-terrain-tiles",
    );
    if (existing) {
      viewer.scene.primitives.remove(existing);
    }
    if (showTerrain) {
      const tileset = new Cesium3DTileset({
        url: "/tiles/tileset.json",
        maximumScreenSpaceError: 16,
      });
      (tileset as unknown as { id: string }).id = "everest-terrain-tiles";
      viewer.scene.primitives.add(tileset);
      void tileset.readyPromise.then(() => {
        viewer.zoomTo(tileset, new Cesium3DTileset.HeadingPitchRange(0, -0.6, 300000));
      });
    }
  }, [showTerrain]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const satelliteEntities = viewer.entities.values.filter((entity) =>
      String(entity.id).startsWith("satellite-"),
    );
    satelliteEntities.forEach((entity) => viewer.entities.remove(entity));
    if (showSatellite && satelliteSegments.length > 0) {
      viewer.entities.add(
        new Entity({
          id: "satellite-note",
          position: Cartesian3.fromDegrees(
            AOI_CENTER.longitude,
            AOI_CENTER.latitude,
            6000,
          ),
          label: {
            text: `Himawari band segments: ${satelliteSegments.length} · decode pending`,
            fillColor: Color.fromCssColorString("#F472B6"),
            scale: 0.8,
          },
        }),
      );
    }
  }, [showSatellite, satelliteSegments]);

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
