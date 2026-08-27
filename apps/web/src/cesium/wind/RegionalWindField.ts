import {
  Cartesian2,
  Cartesian3,
  CircleEmitter,
  Color,
  Matrix4,
  ParticleBurst,
  ParticleSystem,
  Transforms,
  type Scene,
} from "cesium";

import type { WindFieldFrame } from "@/api/types";

import { buildRegionalSeeds, type WindSeed } from "./regional";

export interface RegionalWindFieldOptions {
  stride?: number;
  maxSeeds?: number;
  /**
   * Bounded display-only plane height. This is not the geometric altitude of
   * the pressure surface and must not be presented as measured atmosphere data.
   */
  visualAltitudeMeters?: number;
  emissionRate?: number;
  particleLifeSeconds?: number;
}

export interface NormalizedRegionalWindFieldOptions {
  stride: number;
  maxSeeds: number;
  visualAltitudeMeters: number;
  emissionRate: number;
  particleLifeSeconds: number;
}

interface DestroyableSystem {
  isDestroyed(): boolean;
  destroy(): void;
}

interface PrimitiveScene<System extends DestroyableSystem> {
  requestRenderMode: boolean;
  primitives: {
    add(system: System): unknown;
    contains(system: System): boolean;
    remove(system: System): unknown;
  };
}

const DEFAULT_OPTIONS: NormalizedRegionalWindFieldOptions = {
  stride: 1,
  maxSeeds: 256,
  visualAltitudeMeters: 7_500,
  emissionRate: 2,
  particleLifeSeconds: 1.5,
};
const STREAM_COLOR = "#38BDF8";

let spriteDataUrl: string | undefined;

function finiteBounded(
  name: keyof RegionalWindFieldOptions,
  value: number | undefined,
  fallback: number,
  minimum: number,
  maximum: number,
  integer = false,
): number {
  if (value === undefined) return fallback;
  if (!Number.isFinite(value)) throw new Error(`${name} must be finite`);
  const bounded = Math.min(maximum, Math.max(minimum, value));
  return integer ? Math.floor(bounded) : bounded;
}

export function normalizeRegionalWindFieldOptions(
  options: RegionalWindFieldOptions = {},
): NormalizedRegionalWindFieldOptions {
  return {
    stride: finiteBounded("stride", options.stride, 1, 1, 64, true),
    maxSeeds: finiteBounded("maxSeeds", options.maxSeeds, 256, 1, 256, true),
    visualAltitudeMeters: finiteBounded(
      "visualAltitudeMeters",
      options.visualAltitudeMeters,
      DEFAULT_OPTIONS.visualAltitudeMeters,
      0,
      20_000,
    ),
    emissionRate: finiteBounded(
      "emissionRate",
      options.emissionRate,
      DEFAULT_OPTIONS.emissionRate,
      0.1,
      60,
    ),
    particleLifeSeconds: finiteBounded(
      "particleLifeSeconds",
      options.particleLifeSeconds,
      DEFAULT_OPTIONS.particleLifeSeconds,
      0.1,
      60,
    ),
  };
}

export function regionalParticleSystemOptions(seed: Pick<WindSeed, "u" | "v">) {
  return {
    speed: 0,
    emitterRadius: 0,
    localDrift: { east: seed.u, north: seed.v, up: 0 },
  } as const;
}

function windParticleSprite(): string | undefined {
  if (spriteDataUrl !== undefined) return spriteDataUrl;
  if (typeof document === "undefined") return undefined;
  const canvas = document.createElement("canvas");
  canvas.width = 16;
  canvas.height = 16;
  const context = canvas.getContext("2d");
  if (!context) return undefined;
  const gradient = context.createRadialGradient(8, 8, 0, 8, 8, 8);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.5, "rgba(255,255,255,0.55)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, 16, 16);
  spriteDataUrl = canvas.toDataURL("image/png");
  return spriteDataUrl;
}

function makeSeedSystem(
  seed: WindSeed,
  options: NormalizedRegionalWindFieldOptions,
  image: string,
): ParticleSystem {
  const position = Cartesian3.fromDegrees(
    seed.longitude,
    seed.latitude,
    options.visualAltitudeMeters,
  );
  const enuToFixed = Transforms.eastNorthUpToFixedFrame(position);
  const particleOptions = regionalParticleSystemOptions(seed);
  const drift = Matrix4.multiplyByPointAsVector(
    enuToFixed,
    new Cartesian3(
      particleOptions.localDrift.east,
      particleOptions.localDrift.north,
      particleOptions.localDrift.up,
    ),
    new Cartesian3(),
  );
  return new ParticleSystem({
    image,
    startColor: Color.fromCssColorString(STREAM_COLOR).withAlpha(0.75),
    endColor: Color.fromCssColorString(STREAM_COLOR).withAlpha(0),
    startScale: 1.2,
    endScale: 0.15,
    particleLife: options.particleLifeSeconds,
    speed: particleOptions.speed,
    imageSize: new Cartesian2(4, 4),
    emissionRate: options.emissionRate,
    bursts: [new ParticleBurst({ time: 0, minimum: 2, maximum: 4 })],
    emitter: new CircleEmitter(particleOptions.emitterRadius),
    updateCallback: (particle, dt) => {
      particle.position = Cartesian3.add(
        particle.position,
        Cartesian3.multiplyByScalar(drift, dt, new Cartesian3()),
        particle.position,
      );
      return particle;
    },
    modelMatrix: enuToFixed,
  });
}

/** Transactionally installs systems and owns their exactly-once cleanup. */
export function installRegionalWindSystems<System extends DestroyableSystem>(
  scene: PrimitiveScene<System>,
  systems: readonly System[],
  systemsAlreadyAdded = false,
): { destroy(): void } {
  const installed = new Set<System>();
  const disposed = new Set<System>();
  let destroyed = false;
  let originalRequestRenderMode: boolean | undefined;

  const destroySystem = (system: System): void => {
    if (disposed.has(system)) return;
    disposed.add(system);
    try {
      if (!system.isDestroyed()) system.destroy();
    } catch {
      // A destroyed scene may already have destroyed its child primitive.
    }
  };
  const removeSystem = (system: System): void => {
    try {
      if (scene.primitives.contains(system)) {
        scene.primitives.remove(system);
        disposed.add(system);
        return;
      }
    } catch {
      // Scene teardown owns any child that can no longer be inspected.
    }
    destroySystem(system);
  };

  try {
    if (systemsAlreadyAdded) {
      systems.forEach((system) => installed.add(system));
    } else {
      for (const system of systems) {
        scene.primitives.add(system);
        installed.add(system);
      }
    }
    if (installed.size > 0) {
      originalRequestRenderMode = scene.requestRenderMode;
      scene.requestRenderMode = false;
    }
  } catch (error) {
    installed.forEach(removeSystem);
    systems.forEach(destroySystem);
    if (originalRequestRenderMode !== undefined) {
      try {
        scene.requestRenderMode = originalRequestRenderMode;
      } catch {
        // Scene was destroyed during setup.
      }
    }
    throw error;
  }

  return {
    destroy(): void {
      if (destroyed) return;
      destroyed = true;
      installed.forEach(removeSystem);
      installed.clear();
      if (originalRequestRenderMode !== undefined) {
        try {
          scene.requestRenderMode = originalRequestRenderMode;
        } catch {
          // Scene already destroyed.
        }
      }
    },
  };
}

/**
 * Visualize a 400 hPa wind frame on a bounded display plane. Seed positions are
 * exact backend lon/lat nodes; the plane height is explicitly not atmospheric
 * geometry or a factual altitude for the pressure level.
 */
export function createRegionalWindField(
  scene: Scene,
  frame: WindFieldFrame,
  inputOptions: RegionalWindFieldOptions = {},
): { destroy(): void } {
  const options = normalizeRegionalWindFieldOptions(inputOptions);
  const image = windParticleSprite();
  if (image === undefined) return { destroy: () => undefined };
  const seeds = buildRegionalSeeds(frame, options);
  const systems: ParticleSystem[] = [];
  try {
    seeds.forEach((seed) => systems.push(makeSeedSystem(seed, options, image)));
    return installRegionalWindSystems(scene, systems);
  } catch (error) {
    systems.forEach((system) => {
      try {
        if (!system.isDestroyed()) system.destroy();
      } catch {
        // Preserve the original setup failure.
      }
    });
    throw error;
  }
}
