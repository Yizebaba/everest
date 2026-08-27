import type { WindFieldFrame } from "@/api/types";

export interface WindFieldTextureData {
  width: number;
  height: number;
  levelCount: number;
  u: Float32Array;
  v: Float32Array;
  minimum: readonly [longitude: number, latitude: number, altitude: number];
  maximum: readonly [longitude: number, latitude: number, altitude: number];
  interval: readonly [longitude: number, latitude: number, altitude: number];
  uRange: readonly [minimum: number, maximum: number];
  vRange: readonly [minimum: number, maximum: number];
}

function range(values: readonly number[]): readonly [number, number] {
  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  for (const value of values) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }
  return [minimum, maximum];
}

function axisInterval(minimum: number, maximum: number, count: number): number {
  return count > 1 ? (maximum - minimum) / (count - 1) : 0;
}

/** Converts a validated API frame into the two RED/FLOAT textures used upstream. */
export function adaptWindFieldFrame(
  frame: WindFieldFrame,
): WindFieldTextureData {
  if (
    frame.u.some((value) => value === null) ||
    frame.v.some((value) => value === null)
  ) {
    throw new Error("wind frame contains missing values");
  }
  const longitudeCount = frame.longitude.length;
  const latitudeCount = frame.latitude.length;
  const { bounds } = frame;
  return {
    width: longitudeCount,
    height: latitudeCount,
    levelCount: 1,
    // Own copies prevent API arrays from being mutated or retained by WebGL.
    u: Float32Array.from(frame.u as number[]),
    v: Float32Array.from(frame.v as number[]),
    minimum: [bounds.west, bounds.south, frame.level],
    maximum: [bounds.east, bounds.north, frame.level],
    interval: [
      axisInterval(bounds.west, bounds.east, longitudeCount),
      axisInterval(bounds.south, bounds.north, latitudeCount),
      0,
    ],
    uRange: range(frame.u as number[]),
    vRange: range(frame.v as number[]),
  };
}
