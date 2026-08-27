import { CircleEmitter } from "cesium";
import { describe, expect, it, vi } from "vitest";

import {
  installRegionalWindSystems,
  normalizeRegionalWindFieldOptions,
  POINT_EMITTER_RADIUS_METERS,
  regionalParticleSystemOptions,
} from "./RegionalWindField";

describe("regional wind options", () => {
  it("clamps finite values to documented hard bounds", () => {
    expect(
      normalizeRegionalWindFieldOptions({
        stride: -10,
        maxSeeds: 10_000,
        visualAltitudeMeters: 99_000,
        emissionRate: 0,
        particleLifeSeconds: 999,
      }),
    ).toEqual({
      stride: 1,
      maxSeeds: 256,
      visualAltitudeMeters: 20_000,
      emissionRate: 0.1,
      particleLifeSeconds: 60,
    });
  });

  it.each([
    "stride",
    "maxSeeds",
    "visualAltitudeMeters",
    "emissionRate",
    "particleLifeSeconds",
  ] as const)("rejects a non-finite %s", (key) => {
    expect(() =>
      normalizeRegionalWindFieldOptions({ [key]: Number.NaN }),
    ).toThrow(`${key} must be finite`);
  });
});

describe("regional particle velocity", () => {
  it("uses only the update callback for u/v drift", () => {
    const options = regionalParticleSystemOptions({ u: 5, v: -2 });
    expect(options.speed).toBe(0);
    expect(options.emitterRadius).toBe(POINT_EMITTER_RADIUS_METERS);
    expect(options.localDrift).toEqual({ east: 5, north: -2, up: 0 });
    expect(() => new CircleEmitter(options.emitterRadius)).not.toThrow();
  });
});

describe("regional wind lifecycle", () => {
  function system(name: string) {
    return {
      name,
      isDestroyed: vi.fn(() => false),
      destroy: vi.fn(),
    };
  }

  it("rolls back every system when the Nth primitive add fails", () => {
    const systems = [system("a"), system("b"), system("c")];
    const added: typeof systems = [];
    const scene = {
      requestRenderMode: true,
      primitives: {
        add: vi.fn((value: (typeof systems)[number]) => {
          if (value.name === "b") throw new Error("Nth add failed");
          added.push(value);
          return value;
        }),
        contains: vi.fn((value) => added.includes(value)),
        remove: vi.fn((value) => {
          added.splice(added.indexOf(value), 1);
          value.destroy();
          return true;
        }),
      },
    };

    expect(() => installRegionalWindSystems(scene, systems)).toThrow(
      "Nth add failed",
    );
    expect(added).toEqual([]);
    expect(
      systems.every((value) => value.destroy.mock.calls.length === 1),
    ).toBe(true);
    expect(scene.requestRenderMode).toBe(true);
  });

  it("destroys idempotently and restores the original render mode", () => {
    const systems = [system("a")];
    const added = [...systems];
    const scene = {
      requestRenderMode: true,
      primitives: {
        add: vi.fn(),
        contains: vi.fn((value) => added.includes(value)),
        remove: vi.fn((value) => {
          added.splice(added.indexOf(value), 1);
          value.destroy();
          return true;
        }),
      },
    };
    const lifecycle = installRegionalWindSystems(scene, systems, true);

    lifecycle.destroy();
    lifecycle.destroy();

    expect(scene.primitives.remove).toHaveBeenCalledTimes(1);
    expect(scene.requestRenderMode).toBe(true);
  });

  it("does not throw when the scene was already destroyed", () => {
    let destroyed = false;
    const lifecycle = installRegionalWindSystems(
      {
        get requestRenderMode() {
          if (destroyed) throw new Error("destroyed");
          return true;
        },
        set requestRenderMode(_value: boolean) {
          if (destroyed) throw new Error("destroyed");
        },
        primitives: {
          add: vi.fn(),
          contains: vi.fn(() => {
            throw new Error("destroyed");
          }),
          remove: vi.fn(),
        },
      },
      [system("a")],
      true,
    );
    destroyed = true;

    expect(() => lifecycle.destroy()).not.toThrow();
  });
});
