import type { WindFieldFrame } from "@/api/types";

export interface WindSeed {
  longitude: number;
  latitude: number;
  u: number;
  v: number;
}

export interface RegionalSeedOptions {
  /** Sample every Nth latitude row and longitude column. */
  stride?: number;
  /** Hard cap on the total number of seeds. */
  maxSeeds?: number;
}

const DEFAULT_STRIDE = 1;
const DEFAULT_MAX_SEEDS = 256;
const MAX_STRIDE = 64;

function boundedInteger(
  name: keyof RegionalSeedOptions,
  value: number | undefined,
  fallback: number,
  maximum: number,
): number {
  if (value === undefined) return fallback;
  if (!Number.isFinite(value)) throw new Error(`${name} must be finite`);
  return Math.floor(Math.min(maximum, Math.max(1, value)));
}

/**
 * Select a bounded subset of exact backend grid nodes. No coordinates or wind
 * vectors are interpolated. A node is omitted only when either component is
 * missing; longitude varies fastest as declared by the frame contract.
 */
export function buildRegionalSeeds(
  frame: WindFieldFrame,
  options: RegionalSeedOptions = {},
): WindSeed[] {
  const stride = boundedInteger(
    "stride",
    options.stride,
    DEFAULT_STRIDE,
    MAX_STRIDE,
  );
  const maxSeeds = boundedInteger(
    "maxSeeds",
    options.maxSeeds,
    DEFAULT_MAX_SEEDS,
    DEFAULT_MAX_SEEDS,
  );
  const seeds: WindSeed[] = [];
  const latitudeCount = frame.latitude.length;
  const longitudeCount = frame.longitude.length;
  for (let j = 0; j < latitudeCount; j += stride) {
    for (let i = 0; i < longitudeCount; i += stride) {
      if (seeds.length >= maxSeeds) {
        return seeds;
      }
      const index = j * longitudeCount + i;
      const u = frame.u[index];
      const v = frame.v[index];
      if (u === null || v === null) {
        continue;
      }
      seeds.push({
        longitude: frame.longitude[i],
        latitude: frame.latitude[j],
        u,
        v,
      });
    }
  }
  return seeds;
}
