import { describe, expect, it, vi } from "vitest";

import {
  chooseWindFieldMode,
  detectWindFieldCapabilities,
  DisposableResources,
} from "./lifecycle";

describe("chooseWindFieldMode", () => {
  const supported = {
    webgl2: true,
    floatTexture: true,
    colorBufferFloat: true,
  };

  it("uses the GPU layer only for a valid frame and complete capabilities", () => {
    expect(chooseWindFieldMode(true, supported, true)).toEqual({
      mode: "gpu",
      reason: null,
    });
  });

  it("keeps the lightweight fallback when no valid frame exists", () => {
    expect(chooseWindFieldMode(false, supported, true).mode).toBe("fallback");
  });

  it("keeps the fallback when float render targets are unavailable", () => {
    expect(
      chooseWindFieldMode(
        true,
        { ...supported, colorBufferFloat: false },
        true,
      ),
    ).toEqual({ mode: "fallback", reason: "float-render-target-unavailable" });
  });

  it("reports the public Cesium adapter boundary truthfully", () => {
    expect(chooseWindFieldMode(true, supported, false)).toEqual({
      mode: "fallback",
      reason: "cesium-public-gpu-api-unavailable",
    });
  });
});

describe("detectWindFieldCapabilities", () => {
  it("requires WebGL2 and the float color-buffer extension", () => {
    const getExtension = vi.fn((name: string) =>
      name === "EXT_color_buffer_float" ? {} : null,
    );
    const canvas = {
      getContext: vi.fn(() => ({ getExtension })),
    } as unknown as HTMLCanvasElement;

    expect(detectWindFieldCapabilities(canvas)).toEqual({
      webgl2: true,
      floatTexture: true,
      colorBufferFloat: true,
    });
  });

  it("fails closed when context creation throws", () => {
    const canvas = {
      getContext: vi.fn(() => {
        throw new Error("blocked");
      }),
    } as unknown as HTMLCanvasElement;

    expect(detectWindFieldCapabilities(canvas)).toEqual({
      webgl2: false,
      floatTexture: false,
      colorBufferFloat: false,
    });
  });
});

describe("DisposableResources", () => {
  it("destroys resources and listeners once in reverse ownership order", () => {
    const calls: string[] = [];
    const resources = new DisposableResources();
    resources.own({ destroy: () => calls.push("resource-a") });
    resources.own({ destroy: () => calls.push("resource-b") });
    resources.listen(() => calls.push("listener"));

    resources.destroy();
    resources.destroy();

    expect(calls).toEqual(["listener", "resource-b", "resource-a"]);
    expect(resources.isDestroyed()).toBe(true);
  });
});
