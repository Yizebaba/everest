import type { DeviceDomain } from "@/types/schema";

export const RESERVED_DEVICES: DeviceDomain = {
  availability: "reserved",
  items: [],
};

export function getDevices(): DeviceDomain {
  return RESERVED_DEVICES;
}
