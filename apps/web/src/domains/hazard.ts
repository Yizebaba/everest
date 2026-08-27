import type { Hazard } from "@/types/schema";

export const RESERVED_HAZARD: Hazard = {
  availability: "reserved",
  points: [],
};

export function getHazard(): Hazard {
  return RESERVED_HAZARD;
}
