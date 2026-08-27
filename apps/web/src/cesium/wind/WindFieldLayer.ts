import { PrimitiveCollection, type Scene } from "cesium";

import type { WindFieldFrame } from "@/api/types";

import {
  chooseWindFieldMode,
  DisposableResources,
  type WindFieldCapabilities,
  type WindFieldMode,
} from "./lifecycle";
import { adaptWindFieldFrame, type WindFieldTextureData } from "./data";

// Cesium's renderer command pipeline is exported for engine use, but Scene's
// context/frame-state command list is not a documented public extension point.
// Keep this false until the implementation can avoid those internals.
export const HAS_PUBLIC_CESIUM_GPU_ADAPTER = false;

export type WindFieldLayerStatus = WindFieldMode & {
  source: string;
  validTime: string;
};

/**
 * Lifecycle and validated-data boundary for Everest's GPU wind layer.
 *
 * The compute/render implementation is deliberately disabled on Cesium 1.144:
 * the referenced implementation requires private frame-state renderer APIs.
 * This class still owns its child collection so enabling a future public
 * adapter cannot accidentally remove unrelated scene primitives.
 */
export class WindFieldLayer {
  readonly status: WindFieldLayerStatus;
  readonly primitives: PrimitiveCollection;
  readonly textureData: WindFieldTextureData;

  private readonly resources = new DisposableResources();
  private destroyed = false;

  constructor(
    private readonly scene: Scene,
    frame: WindFieldFrame,
    capabilities: WindFieldCapabilities,
  ) {
    this.primitives = this.resources.own(
      new PrimitiveCollection({ destroyPrimitives: true }),
    );
    this.textureData = adaptWindFieldFrame(frame);
    const mode = chooseWindFieldMode(
      true,
      capabilities,
      HAS_PUBLIC_CESIUM_GPU_ADAPTER,
    );
    this.status = {
      ...mode,
      source: frame.source,
      validTime: frame.valid_time,
    };

    if (mode.mode === "gpu") {
      this.scene.primitives.add(this.primitives);
    }
  }

  isDestroyed(): boolean {
    return this.destroyed;
  }

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    if (this.scene.primitives.contains(this.primitives)) {
      // The scene collection may destroy the child on removal. The resource
      // ledger checks isDestroyed(), so this remains exactly-once either way.
      this.scene.primitives.remove(this.primitives);
    }
    this.resources.destroy();
  }
}
