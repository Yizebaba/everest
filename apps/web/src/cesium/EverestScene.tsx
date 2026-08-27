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
  Cartographic,
  CircleEmitter,
  ClockRange,
  Color,
  defined,
  Entity,
  GeographicTilingScheme,
  HeadingPitchRange,
  HeightReference,
  ImageryLayer,
  Ion,
  JulianDate,
  Math as CesiumMath,
  Matrix4,
  ParticleBurst,
  ParticleSystem,
  PolylineGraphics,
  Rectangle,
  sampleTerrainMostDetailed,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  SingleTileImageryProvider,
  Terrain,
  TileMapServiceImageryProvider,
  Transforms,
  Viewer,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

import type { CanonicalWeatherRecord } from "@/api/types";
import type { EverestCamp } from "@/api/types";
import type { WindFieldFrame } from "@/api/types";
import { getWindField } from "@/api/client";
import { t, type Locale } from "@/i18n/t";
import {
  sceneSelectionFromEntity,
  type SceneEntitySelections,
  type SceneSelection,
} from "@/cesium/selection";
import {
  createRegionalWindField,
  installRegionalWindSystems,
  selectRenderableWindFrame,
} from "@/cesium/wind";
import {
  AOI_CENTER,
  compassPoint,
  metersToDegrees,
  slopeDegrees,
  windVector,
} from "@/lib/geo";

// Optional Cesium ion token (gitignored via .env.local). When present, the
// scene enables Cesium World Terrain (real global terrain) and can load
// ion-hosted 3D Tiles. When absent, the scene renders on the WGS84 ellipsoid
// with the local NaturalEarthII TMS so the globe is not blank if OSM is
// blocked — no network calls to ion are made.
const CESIUM_ION_TOKEN = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN?.trim() ?? "";
if (typeof window !== "undefined" && CESIUM_ION_TOKEN) {
  Ion.defaultAccessToken = CESIUM_ION_TOKEN;
}

export interface EverestSceneProps {
  records: CanonicalWeatherRecord[];
  activeTime?: string | null;
  camps?: EverestCamp[];
  route?: [number, number][];
  // Null while the OSM peak node is not persisted; the scene then draws no
  // summit marker instead of placing one at an assumed height.
  summit?: EverestCamp | null;
  onSelectRecord?: (record: CanonicalWeatherRecord | null) => void;
  onSelect?: (selection: SceneSelection | null) => void;
  locale?: Locale;
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
const SUMMIT_COLOR = "#F87171";

// ParticleSystem needs a real texture; it was constructed with `image:
// undefined`, which draws nothing, so the wind field was absent from the scene
// rather than merely faint. Generated in-page as a soft dot so no binary asset
// has to be committed, and cached because every emitter shares it.
let windParticleImage: string | undefined;

function windParticleSprite(): string | undefined {
  if (windParticleImage !== undefined) {
    return windParticleImage;
  }
  if (typeof document === "undefined") {
    return undefined;
  }
  const canvas = document.createElement("canvas");
  canvas.width = 16;
  canvas.height = 16;
  const context = canvas.getContext("2d");
  if (!context) {
    return undefined;
  }
  const gradient = context.createRadialGradient(8, 8, 0, 8, 8, 8);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.5, "rgba(255,255,255,0.55)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 16, 16);
  windParticleImage = canvas.toDataURL("image/png");
  return windParticleImage;
}

export function EverestScene({
  records,
  activeTime = null,
  camps = [],
  route = [],
  summit = null,
  onSelectRecord,
  onSelect,
  locale = "en",
}: EverestSceneProps): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const entityByRecord = useRef(new Map<string, Entity>());
  const sceneEntities = useRef<SceneEntitySelections>({
    weather: new Map(),
    camps: new Map(),
    routes: new Map(),
  });
  const satelliteLayerRef = useRef<ImageryLayer | null>(null);
  const onSelectRef = useRef(onSelectRecord);
  onSelectRef.current = onSelectRecord;
  const onSceneSelectRef = useRef(onSelect);
  onSceneSelectRef.current = onSelect;

  const [showSatellite, setShowSatellite] = useState(false);
  const [pickInfo, setPickInfo] = useState<string | null>(null);
  const [windFieldFrame, setWindFieldFrame] = useState<WindFieldFrame | null>(
    null,
  );
  const [webglOk] = useState(() => {
    try {
      const canvas = document.createElement("canvas");
      return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
    } catch {
      return false;
    }
  });

  useEffect(() => {
    let cancelled = false;
    // Remove the prior frame immediately so an unavailable exact-time request
    // cannot leave stale particles visible while the lightweight records wait.
    setWindFieldFrame(null);
    void getWindField(activeTime ?? undefined)
      .then((response) => {
        if (!cancelled) {
          setWindFieldFrame(
            selectRenderableWindFrame(response, activeTime ?? undefined),
          );
        }
      })
      .catch(() => {
        // A missing, unavailable, or invalid frame is an expected fail-closed
        // state. The lightweight record ParticleSystem remains active.
        if (!cancelled) setWindFieldFrame(null);
      });
    return () => {
      cancelled = true;
    };
  }, [activeTime]);

  useEffect(() => {
    if (!webglOk) {
      return undefined;
    }
    const container = containerRef.current;
    if (!container) {
      return undefined;
    }
    const recordEntities = entityByRecord.current;
    // Cesium derives the canvas/framebuffer size from the container. If the
    // layout has not settled (or header/rail growth collapses the scene box)
    // the container can report 0, and the first GlobeDepth render then throws
    // "Expected width to be greater than 0" and stops the render loop. Pin a
    // one-pixel minimum so the viewer never starts on a 0-sized canvas; the
    // ResizeObserver below resizes it as soon as the container gets a real box.
    if (container.clientWidth === 0) {
      container.style.minWidth = "1px";
    }
    if (container.clientHeight === 0) {
      container.style.minHeight = "1px";
    }
    let viewer: Viewer | undefined;
    try {
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
        // Render only when the scene changes (camera moves, tiles load) instead
        // of re-drawing every frame; dramatically cuts GPU load on high-res
        // terrain scenes and avoids a constant full-viewport repaint.
        requestRenderMode: true,
        maximumRenderTimeChange: 0.5,
      };
      if (CESIUM_ION_TOKEN) {
        // Cesium World Terrain (requires a valid ion token). Falls back to
        // ellipsoid automatically if the asset stream errors.
        // requestVertexNormals enables per-vertex terrain lighting so mountain
        // relief is visible (otherwise high-altitude terrain looks flat).
        options.terrain = Terrain.fromWorldTerrain({
          requestVertexNormals: true,
        });
      }
      viewer = new Viewer(container, options);
      if (CESIUM_ION_TOKEN) {
        // Sun-position terrain lighting gives the scene its 3D relief shading.
        viewer.scene.globe.enableLighting = true;
        // Pin the scene clock to Everest local solar noon (~05:45 UTC) so the
        // massif is lit with visible ridge shadows. The default clock follows
        // the real wall clock, which at night renders terrain pitch-dark and
        // looks flat.
        viewer.clock.currentTime = JulianDate.fromDate(
          new Date("2026-08-26T05:45:00Z"),
        );
        viewer.clock.clockRange = ClockRange.CLAMPED;
        viewer.clock.shouldAnimate = false;
        // Cesium World Imagery (ion-hosted Bing global imagery) replaces the
        // OSM raster base when an ion token is configured. See
        // EV-VIS-004 / docs/design for the base-map rationale.
        viewer.imageryLayers.add(ImageryLayer.fromWorldImagery({}));
      } else {
        // Local NaturalEarthII TMS shipped under /public/cesium. Cesium 1.130
        // requires fromUrl (the constructor is documented as do-not-call and
        // skips tilemapresource.xml, so it would assume WebMercator on an
        // EPSG:4326 jpg set and paint a blank globe). OSM is optional and
        // often blocked; without this fallback the ellipsoid is blank.
        void (async () => {
          try {
            const tms = await TileMapServiceImageryProvider.fromUrl(
              "/cesium/Assets/Textures/NaturalEarthII/",
              {
                fileExtension: "jpg",
                maximumLevel: 2,
                tilingScheme: new GeographicTilingScheme(),
                credit: "Natural Earth II",
              },
            );
            if (viewer.isDestroyed()) {
              return;
            }
            viewer.imageryLayers.addImageryProvider(tms);
            viewer.scene.requestRender();
          } catch (error) {
            console.error("NaturalEarthII TMS failed:", error);
          }
        })();
      }
      viewer.scene.camera.setView({
        // Initial overview; the lookAt below frames the summit at low angle.
        destination: Cartesian3.fromDegrees(
          AOI_CENTER.longitude,
          AOI_CENTER.latitude,
          12000,
        ),
        orientation: { heading: 0, pitch: -Math.PI / 4, roll: 0 },
      });
      // Frame the Everest massif from the south at a shallow angle. Applied
      // even without ion so the ellipsoid view is not a high nadir overview.
      viewer.scene.camera.lookAt(
        Cartesian3.fromDegrees(AOI_CENTER.longitude, AOI_CENTER.latitude, 7000),
        new HeadingPitchRange(0, -Math.PI / 8, 25000),
      );
      // lookAt leaves the camera locked to the target's reference frame, which
      // keeps every later pan and zoom orbiting that one point. Resetting the
      // transform keeps the framing just computed but hands normal navigation
      // back to the user.
      viewer.scene.camera.lookAtTransform(Matrix4.IDENTITY);
    } catch (error) {
      console.error("Cesium viewer init failed:", error);
      return undefined;
    }
    viewerRef.current = viewer;

    // Keep the Cesium canvas sized to its container. Cesium only re-sizes on
    // window resize; when the header/rail layout changes the scene's box, the
    // canvas would keep a stale size and a transient 0-width framebuffer would
    // throw in GlobeDepth.update and stop the render loop. A ResizeObserver
    // keeps canvas and container in sync (viewer.resize() is the public API).
    const resizeObserver =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(() => {
            if (viewerRef.current !== viewer || viewer.isDestroyed()) {
              return;
            }
            const width = container.clientWidth;
            const height = container.clientHeight;
            if (width > 0 && height > 0) {
              viewer.resize();
            }
          });
    resizeObserver?.observe(container);

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
        if (viewerRef.current !== viewer) {
          return;
        }
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
      resizeObserver?.disconnect();
      recordEntities.clear();
      satelliteLayerRef.current = null;
      viewerRef.current = null;
      viewer?.destroy();
    };
  }, [webglOk]);

  useEffect(() => {
    const viewer = viewerRef.current;
    const selections = sceneEntities.current;
    if (!viewer) {
      return;
    }
    const existing = viewer.entities.getById("osm-south-col-route");
    if (existing) {
      viewer.entities.remove(existing);
    }
    if (route.length < 2) {
      selections.routes = new Map();
      return;
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
    selections.routes = new Map([["osm-south-col-route", route]]);
    return () => {
      selections.routes = new Map();
      // Guard before touching viewer internals: on re-render or unmount the
      // captured viewer may have been replaced or torn down (viewerRef no
      // longer points at this instance), and isDestroyed() on a destroyed
      // Viewer can itself throw.
      if (viewerRef.current !== viewer) {
        return;
      }
      const entity = viewer.entities.getById("osm-south-col-route");
      if (entity) {
        viewer.entities.remove(entity);
      }
    };
  }, [route, webglOk]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    const existing = viewer.entities.getById("route-elevation-markers");
    if (existing) {
      removeEntityTree(viewer, existing);
    }
    if (route.length < 2) return;
    // Sample the route at regular stride and label the real terrain height.
    // The stride keeps the number of markers bounded regardless of route
    // vertex count. Height is the Cesium World Terrain elevation at that point.
    const stride = Math.max(1, Math.floor(route.length / 12));
    const sampled: [number, number][] = [];
    for (let i = 0; i < route.length; i += stride) {
      const [latitude, longitude] = route[i];
      sampled.push([latitude, longitude]);
    }
    const last = route[route.length - 1];
    if (sampled[sampled.length - 1] !== last) {
      sampled.push(last);
    }
    const markers = new Entity({ id: "route-elevation-markers" });
    viewer.entities.add(markers);
    void (async () => {
      try {
        const terrainProvider = viewer.terrainProvider;
        const cartographics = sampled.map(
          ([latitude, longitude]) =>
            new Cartographic(
              CesiumMath.toRadians(longitude),
              CesiumMath.toRadians(latitude),
            ),
        );
        const results = await sampleTerrainMostDetailed(
          terrainProvider,
          cartographics,
        );
        if (
          viewerRef.current !== viewer ||
          !viewer.entities.contains(markers)
        ) {
          return;
        }
        for (let i = 0; i < results.length; i += 1) {
          const [latitude, longitude] = sampled[i];
          const height = results[i].height;
          const valid = Number.isFinite(height);
          viewer.entities.add(
            new Entity({
              parent: markers,
              position: Cartesian3.fromDegrees(
                longitude,
                latitude,
                valid ? height : 0,
              ),
              point: {
                pixelSize: 3,
                color: Color.fromCssColorString("#FBBF24").withAlpha(0.8),
              },
              label: {
                text: valid ? `${Math.round(height)} m` : "—",
                font: "10px Inter, system-ui, sans-serif",
                fillColor: Color.fromCssColorString("#9AA5B8"),
                outlineColor: Color.fromCssColorString("#0B0E14"),
                outlineWidth: 2,
                pixelOffset: new Cartesian2(0, 12),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
                show: valid,
              },
            }),
          );
        }
      } catch {
        // Terrain sampling is best-effort; fall back to silent point markers.
        if (
          viewerRef.current !== viewer ||
          !viewer.entities.contains(markers)
        ) {
          return;
        }
        for (const [latitude, longitude] of sampled) {
          viewer.entities.add(
            new Entity({
              parent: markers,
              position: Cartesian3.fromDegrees(longitude, latitude, 0),
              point: {
                pixelSize: 3,
                color: Color.fromCssColorString("#FBBF24").withAlpha(0.8),
              },
            }),
          );
        }
      }
    })();
    return () => {
      if (viewerRef.current === viewer) {
        removeEntityTree(viewer, markers);
      }
    };
  }, [route, webglOk]);

  useEffect(() => {
    const viewer = viewerRef.current;
    const selections = sceneEntities.current;
    if (!viewer) {
      return;
    }
    // OSM South Col camp markers (EV-OSM-002). Re-synced whenever the camps
    // array changes so the scene stays consistent with the persisted snapshot.
    const existing = viewer.entities.getById("osm-camps");
    if (existing) {
      removeEntityTree(viewer, existing);
    }
    if (camps.length === 0 && !summit) {
      selections.camps = new Map();
      return;
    }
    const campGroup = new Entity({
      id: "osm-camps",
    });
    viewer.entities.add(campGroup);
    const marked: EverestCamp[] = summit ? [...camps, summit] : camps;
    const campSelections = new Map<string, EverestCamp>();
    for (const camp of marked) {
      const isSummit = summit !== null && camp === summit;
      const hasElevation =
        camp.elevation_m !== null && camp.elevation_m !== undefined;
      const weather = nearestWeatherRecord(
        records,
        camp.latitude,
        camp.longitude,
      );
      const lines = [camp.name];
      if (hasElevation) {
        lines.push(`${Math.round(camp.elevation_m as number)} m`);
      } else {
        // An unknown OSM height is stated as unknown; the marker below is
        // clamped to terrain rather than placed at an invented altitude.
        lines.push("elev. unknown");
      }
      if (weather) {
        if (weather.temperature !== null && weather.temperature !== undefined) {
          lines.push(`${weather.temperature.toFixed(1)}°C`);
        }
        if (
          weather.relative_humidity !== null &&
          weather.relative_humidity !== undefined
        ) {
          lines.push(`rh ${weather.relative_humidity.toFixed(0)}%`);
        }
        if (weather.wind_speed !== null && weather.wind_speed !== undefined) {
          const dir =
            weather.wind_direction !== null &&
            weather.wind_direction !== undefined
              ? ` ${compassPoint(weather.wind_direction)}`
              : "";
          lines.push(`w ${weather.wind_speed.toFixed(1)} m/s${dir}`);
        }
        if (weather.visibility !== null && weather.visibility !== undefined) {
          lines.push(`vis ${Math.round(weather.visibility)} m`);
        }
      }
      const entityId = `osm-camp-${camp.osm_ref ?? camp.name}`;
      viewer.entities.add(
        new Entity({
          id: entityId,
          parent: campGroup,
          position: Cartesian3.fromDegrees(
            camp.longitude,
            camp.latitude,
            hasElevation ? (camp.elevation_m as number) : 0,
          ),
          point: {
            pixelSize: isSummit ? 13 : 9,
            color: Color.fromCssColorString(
              isSummit ? SUMMIT_COLOR : CAMP_COLOR,
            ),
            outlineColor: Color.fromCssColorString("#0B0E14"),
            outlineWidth: 2,
            // Only a camp with no published height falls back to the terrain
            // surface; a known height is absolute so the ladder keeps its real
            // vertical spacing.
            heightReference: hasElevation
              ? HeightReference.NONE
              : HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: lines.join("\n"),
            font: isSummit
              ? "12px Inter, system-ui, sans-serif"
              : "11px Inter, system-ui, sans-serif",
            fillColor: Color.fromCssColorString("#E6EAF2"),
            outlineColor: Color.fromCssColorString("#0B0E14"),
            outlineWidth: 2,
            pixelOffset: new Cartesian2(0, -14),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            heightReference: hasElevation
              ? HeightReference.NONE
              : HeightReference.CLAMP_TO_GROUND,
          },
          description: `${camp.name} (OSM ${camp.osm_ref ?? "—"})`,
        }),
      );
      campSelections.set(entityId, camp);
    }
    selections.camps = campSelections;
    return () => {
      selections.camps = new Map();
      if (viewerRef.current === viewer) {
        removeEntityTree(viewer, campGroup);
      }
    };
  }, [camps, records, summit, webglOk]);

  // The map weather layer is the regional grid particle field (see the wind
  // effect below). Single-point records are UI-panel sampling points only and
  // are no longer drawn as point circles or wind barbs; this effect only keeps
  // the selection index in sync for panel-driven camp/weather queries.
  useEffect(() => {
    const selections = sceneEntities.current;
    selections.weather = new Map(
      records.map((record) => [recordKey(record), record]),
    );
    return () => {
      selections.weather = new Map();
    };
  }, [records]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !windFieldFrame) return;
    // Regional wind grid: one emitter per exact renderable backend grid node.
    // Missing nodes are omitted without suppressing the remaining field. This
    // is the map weather layer;
    // single-point records are UI-panel sampling only.
    const field = createRegionalWindField(viewer.scene, windFieldFrame, {
      stride: 1,
    });

    return () => {
      // Same teardown guard as the sibling effects: on unmount the viewer
      // effect's cleanup runs first and destroys the scene, so this layer's
      // scene reference is no longer safe to touch.
      field.destroy();
    };
  }, [windFieldFrame]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || windFieldFrame) {
      // When the regional grid field is live it is the map weather layer; the
      // per-record emitters are only the lightweight fallback for the
      // frame-unavailable case.
      return;
    }
    // Wind particle field: one emitter per weather grid point with a valid
    // wind direction, streaming particles along the meteorological travel
    // vector above the terrain.
    const systems: ParticleSystem[] = [];
    const image = windParticleSprite();
    try {
      for (const record of records) {
        if (
          record.wind_direction === null ||
          record.wind_direction === undefined ||
          record.wind_speed === null ||
          record.wind_speed === undefined ||
          image === undefined
        ) {
          continue;
        }
        const { x, y } = windVector(record.wind_direction);
        const heading = Math.atan2(x, y);
        const speed = record.wind_speed;
        const position = Cartesian3.fromDegrees(
          record.longitude,
          record.latitude,
          record.altitude,
        );
        const sourceColor = Color.fromCssColorString(
          SOURCE_COLORS[record.source] ?? "#9AA5B8",
        );
        const enuToFixed = Transforms.eastNorthUpToFixedFrame(position);
        const drift = Matrix4.multiplyByPointAsVector(
          enuToFixed,
          new Cartesian3(
            Math.sin(heading) * speed,
            Math.cos(heading) * speed,
            0,
          ),
          new Cartesian3(),
        );
        systems.push(
          new ParticleSystem({
            image,
            startColor: sourceColor.withAlpha(0.7),
            endColor: sourceColor.withAlpha(0),
            startScale: 1,
            endScale: 0.15,
            particleLife: 1.2,
            speed: 0,
            imageSize: new Cartesian2(4, 4),
            emissionRate: 3,
            bursts: [new ParticleBurst({ time: 0, minimum: 4, maximum: 6 })],
            emitter: new CircleEmitter(0),
            updateCallback: (particle, dt) => {
              particle.position = Cartesian3.add(
                particle.position,
                Cartesian3.multiplyByScalar(drift, dt, new Cartesian3()),
                particle.position,
              );
              return particle;
            },
            modelMatrix: enuToFixed,
          }),
        );
      }
    } catch {
      systems.forEach((system) => {
        if (!system.isDestroyed()) system.destroy();
      });
      return;
    }
    let field: { destroy(): void };
    try {
      field = installRegionalWindSystems(viewer.scene, systems);
    } catch {
      // Transactional installer has already rolled back all constructed
      // systems. Leave the scene usable even if a primitive add fails.
      return;
    }
    return () => {
      field.destroy();
    };
  }, [records, windFieldFrame]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }
    // Remove the layer this effect added last time, tracked by reference. It
    // used to be located by reading the private `layer._provider.url`; that
    // field is not part of Cesium's public API, so a rename would silently make
    // every toggle stack another copy of the overlay instead of replacing it.
    const previous = satelliteLayerRef.current;
    if (previous) {
      if (viewer.imageryLayers.contains(previous)) {
        viewer.imageryLayers.remove(previous);
      }
      satelliteLayerRef.current = null;
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
        satelliteLayerRef.current = layer;
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
        onSceneSelectRef.current?.(null);
        onSelectRef.current?.(null);
        return;
      }
      const entityId = String(picked.id.id);
      const depthPosition = viewer.scene.pickPositionSupported
        ? viewer.scene.pickPosition(movement.position)
        : undefined;
      const ray = depthPosition
        ? undefined
        : viewer.camera.getPickRay(movement.position);
      const pickedPosition =
        depthPosition ??
        (ray ? viewer.scene.globe.pick(ray, viewer.scene) : undefined);
      const cartographic = pickedPosition
        ? Cartographic.fromCartesian(pickedPosition)
        : null;
      const selection = sceneSelectionFromEntity(
        entityId,
        sceneEntities.current,
        cartographic
          ? {
              latitude: CesiumMath.toDegrees(cartographic.latitude),
              longitude: CesiumMath.toDegrees(cartographic.longitude),
            }
          : undefined,
      );
      onSceneSelectRef.current?.(selection);
      const record =
        selection?.kind === "weather" ? selection.record : undefined;
      onSelectRef.current?.(record ?? null);
    }, ScreenSpaceEventType.LEFT_CLICK);

    // Terrain picking: hover to read elevation and slope at the cursor.
    // Throttled to ~100 ms so sampleHeight raycasts do not run every frame.
    let lastPickAt = 0;
    handler.setInputAction((movement: { endPosition: Cartesian2 }) => {
      const now = performance.now();
      if (now - lastPickAt < 100) {
        return;
      }
      lastPickAt = now;
      // Pick against the terrain surface, not the ellipsoid: pickEllipsoid
      // returns where the ray crosses sea level, which on a 8.8 km massif is
      // kilometres away from the ridge actually under the cursor, so the
      // reported altitude and slope belonged to a different place than the
      // pixel being hovered.
      const ray = viewer.camera.getPickRay(movement.endPosition);
      const cartesian = ray
        ? viewer.scene.globe.pick(ray, viewer.scene)
        : undefined;
      if (!defined(cartesian)) {
        setPickInfo(null);
        return;
      }
      const carto = Cartographic.fromCartesian(cartesian);
      const lonDeg = CesiumMath.toDegrees(carto.longitude);
      const latDeg = CesiumMath.toDegrees(carto.latitude);
      const center = new Cartographic(carto.longitude, carto.latitude);
      const sampled = viewer.scene.sampleHeight(center);
      // On the ellipsoid (no ion World Terrain) sampleHeight is undefined.
      // globe.pick still returns a cartesian; carto.height is sea-level
      // ellipsoid height and is enough to report altitude.
      const height = sampled === undefined ? carto.height : sampled;
      // Slope: sample two orthogonal neighbours RUN_METERS away (east and
      // north) and take the steeper gradient, keeping the per-hover raycast
      // count low. A degree of longitude is only cos(latitude) as long as a
      // degree of latitude, so the two offsets differ; using one value for both
      // made the east run ~44 m at 28 degN while the arctangent divided by 50 m,
      // overstating every east-west slope by ~13%.
      const RUN_METERS = 50;
      const probe = metersToDegrees(latDeg, RUN_METERS, RUN_METERS);
      const probes = [
        [lonDeg + probe.deltaLongitude, latDeg],
        [lonDeg, latDeg + probe.deltaLatitude],
      ];
      let slopeDeg: number | null = null;
      for (const [pLon, pLat] of probes) {
        const neighbor = viewer.scene.sampleHeight(
          new Cartographic(
            CesiumMath.toRadians(pLon),
            CesiumMath.toRadians(pLat),
          ),
        );
        if (neighbor === undefined) {
          continue;
        }
        const degrees = slopeDegrees(neighbor - height, RUN_METERS);
        slopeDeg = slopeDeg === null ? degrees : Math.max(slopeDeg, degrees);
      }
      // With no usable neighbour sample there is no measured gradient. This
      // used to report a flat "0.0 deg", which on a mountain face reads as a
      // measurement rather than as missing terrain detail.
      const slopeText =
        slopeDeg === null ? "slope —" : `slope ${slopeDeg.toFixed(1)}°`;
      const weather = nearestWeatherRecord(records, latDeg, lonDeg);
      const bits = [`alt ${Math.max(height, 0).toFixed(0)} m`, slopeText];
      if (weather) {
        if (weather.temperature !== null && weather.temperature !== undefined) {
          bits.push(`${weather.temperature.toFixed(1)}°C`);
        }
        if (
          weather.relative_humidity !== null &&
          weather.relative_humidity !== undefined
        ) {
          bits.push(`rh ${weather.relative_humidity.toFixed(0)}%`);
        }
        if (weather.wind_speed !== null && weather.wind_speed !== undefined) {
          const dir =
            weather.wind_direction !== null &&
            weather.wind_direction !== undefined
              ? ` ${compassPoint(weather.wind_direction)}`
              : "";
          bits.push(`${weather.wind_speed.toFixed(1)} m/s${dir}`);
        }
      }
      bits.push(`${latDeg.toFixed(4)}°, ${lonDeg.toFixed(4)}°`);
      setPickInfo(bits.join(" · "));
    }, ScreenSpaceEventType.MOUSE_MOVE);

    return () => {
      handler.destroy();
      setPickInfo(null);
    };
  }, [records]);

  return (
    <div className="scene">
      {!webglOk ? (
        <div className="scene__fallback" role="status">
          {t("scene.webglRequired", locale)}
        </div>
      ) : (
        <>
          <div
            ref={containerRef}
            className="scene__canvas"
            aria-label={t("scene.map", locale)}
          />
          {windFieldFrame && (
            <div className="scene__wind-plane" role="status">
              {windFieldFrame.level} {windFieldFrame.level_units} wind ·
              visualization plane
            </div>
          )}
          <div
            className="scene__controls"
            role="group"
            aria-label={t("scene.layers", locale)}
          >
            <button
              type="button"
              aria-pressed={showSatellite}
              onClick={() => setShowSatellite((v) => !v)}
            >
              {t("scene.satellite", locale)}
            </button>
          </div>
          {pickInfo && (
            <div className="scene__pick" role="status" aria-live="polite">
              {pickInfo}
            </div>
          )}
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
        .scene__wind-plane {
          position: absolute;
          top: 12px;
          right: 12px;
          background: rgba(20, 26, 36, 0.92);
          border: 1px solid #2c3a52;
          border-radius: 6px;
          color: #9aa5b8;
          font-size: 11px;
          padding: 5px 8px;
          pointer-events: none;
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
        .scene__pick {
          position: absolute;
          left: 12px;
          bottom: 12px;
          background: rgba(20, 26, 36, 0.92);
          border: 1px solid #2c3a52;
          border-radius: 6px;
          color: #e6eaf2;
          font-size: 12px;
          font-variant-numeric: tabular-nums;
          padding: 6px 10px;
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}

function recordKey(record: CanonicalWeatherRecord): string {
  return `${record.source}-${record.timestamp}-${record.spatial_key}-${record.forecast_cycle}`;
}

function nearestWeatherRecord(
  records: CanonicalWeatherRecord[],
  latitude: number,
  longitude: number,
): CanonicalWeatherRecord | null {
  if (records.length === 0) {
    return null;
  }
  return [...records].sort((a, b) => {
    const da = (a.latitude - latitude) ** 2 + (a.longitude - longitude) ** 2;
    const db = (b.latitude - latitude) ** 2 + (b.longitude - longitude) ** 2;
    if (da !== db) {
      return da - db;
    }
    return a.timestamp < b.timestamp ? 1 : -1;
  })[0];
}

function removeEntityTree(viewer: Viewer, root: Entity): void {
  const children = viewer.entities.values.filter(
    (entity) => entity.parent === root,
  );
  for (const child of children) viewer.entities.remove(child);
  viewer.entities.remove(root);
}
