export interface WindFieldCapabilities {
  webgl2: boolean;
  floatTexture: boolean;
  colorBufferFloat: boolean;
}

export type WindFieldDisabledReason =
  | "frame-unavailable"
  | "webgl2-unavailable"
  | "float-texture-unavailable"
  | "float-render-target-unavailable"
  | "cesium-public-gpu-api-unavailable";

export type WindFieldMode =
  | { mode: "gpu"; reason: null }
  | { mode: "fallback"; reason: WindFieldDisabledReason };

export function detectWindFieldCapabilities(
  canvas: HTMLCanvasElement,
): WindFieldCapabilities {
  try {
    const context = canvas.getContext("webgl2");
    if (!context) {
      return {
        webgl2: false,
        floatTexture: false,
        colorBufferFloat: false,
      };
    }
    return {
      webgl2: true,
      // Floating-point texture sampling is core in WebGL2.
      floatTexture: true,
      // The upstream compute pipeline renders particle state into RGBA32F.
      colorBufferFloat: Boolean(context.getExtension("EXT_color_buffer_float")),
    };
  } catch {
    return {
      webgl2: false,
      floatTexture: false,
      colorBufferFloat: false,
    };
  }
}

export function chooseWindFieldMode(
  hasValidFrame: boolean,
  capabilities: WindFieldCapabilities,
  hasPublicCesiumGpuAdapter: boolean,
): WindFieldMode {
  if (!hasValidFrame) {
    return { mode: "fallback", reason: "frame-unavailable" };
  }
  if (!capabilities.webgl2) {
    return { mode: "fallback", reason: "webgl2-unavailable" };
  }
  if (!capabilities.floatTexture) {
    return { mode: "fallback", reason: "float-texture-unavailable" };
  }
  if (!capabilities.colorBufferFloat) {
    return { mode: "fallback", reason: "float-render-target-unavailable" };
  }
  if (!hasPublicCesiumGpuAdapter) {
    return {
      mode: "fallback",
      reason: "cesium-public-gpu-api-unavailable",
    };
  }
  return { mode: "gpu", reason: null };
}

interface Destroyable {
  destroy(): unknown;
  isDestroyed?(): boolean;
}

/** Tracks only resources owned by one layer and disposes them deterministically. */
export class DisposableResources {
  private destroyed = false;
  private readonly resources: Destroyable[] = [];
  private readonly removeListeners: Array<() => void> = [];

  own<T extends Destroyable>(resource: T): T {
    if (this.destroyed) {
      resource.destroy();
      throw new Error("cannot own a resource after destruction");
    }
    this.resources.push(resource);
    return resource;
  }

  listen(removeListener: () => void): () => void {
    if (this.destroyed) {
      removeListener();
      throw new Error("cannot own a listener after destruction");
    }
    this.removeListeners.push(removeListener);
    return removeListener;
  }

  isDestroyed(): boolean {
    return this.destroyed;
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    for (let index = this.removeListeners.length - 1; index >= 0; index -= 1) {
      this.removeListeners[index]();
    }
    for (let index = this.resources.length - 1; index >= 0; index -= 1) {
      const resource = this.resources[index];
      if (!resource.isDestroyed?.()) resource.destroy();
    }
    this.removeListeners.length = 0;
    this.resources.length = 0;
  }
}
