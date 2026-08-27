import type { Environment, Locale } from "@/types/schema";
import { AOI_CENTER } from "@/lib/geo";

export const DEFAULT_ENVIRONMENT: Environment = {
  kind: "everest",
  name: "Everest",
  locale: "en",
  center: { latitude: AOI_CENTER.latitude, longitude: AOI_CENTER.longitude },
  radiusMeters: 100_000,
  activeMissionId: null,
};

export function createEnvironment(locale: Locale): Environment {
  return { ...DEFAULT_ENVIRONMENT, locale };
}

export function setLocale(
  environment: Environment,
  locale: Locale,
): Environment {
  return { ...environment, locale };
}
