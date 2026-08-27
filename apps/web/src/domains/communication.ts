import type { Communication } from "@/types/schema";

export const RESERVED_COMMUNICATION: Communication = {
  availability: "reserved",
  links: [],
  primary: "offline",
};

export function getCommunication(): Communication {
  return RESERVED_COMMUNICATION;
}
