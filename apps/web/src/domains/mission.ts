import type { MissionDomain } from "@/types/schema";

export const RESERVED_MISSION: MissionDomain = {
  availability: "reserved",
  value: null,
};

export function getMission(): MissionDomain {
  return RESERVED_MISSION;
}
