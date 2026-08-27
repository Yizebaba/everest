import type { Sensor } from "@/types/schema";

export const RESERVED_SENSOR: Sensor = {
  availability: "reserved",
  readings: [],
  status: "unknown",
};

export function getSensor(): Sensor {
  return RESERVED_SENSOR;
}
