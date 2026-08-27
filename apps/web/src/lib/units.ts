const NBSP = "\u00A0";

export function formatTemperature(celsius: number | null): string {
  return celsius === null ? "unavailable" : `${celsius.toFixed(1)}${NBSP}°C`;
}

export function formatWindSpeed(speed: number | null): string {
  return speed === null ? "unavailable" : `${speed.toFixed(1)}${NBSP}m/s`;
}

export function formatWindDirection(degrees: number | null): string {
  return degrees === null ? "unavailable" : `${Math.round(degrees)}°`;
}

export function formatPrecipitation(mm: number | null): string {
  return mm === null ? "unavailable" : `${mm.toFixed(1)}${NBSP}mm`;
}

export function formatVisibility(meters: number | null): string {
  return meters === null ? "unavailable" : `${Math.round(meters)}${NBSP}m`;
}

export function formatAltitude(meters: number | null): string {
  return meters === null ? "unavailable" : `${Math.round(meters)}${NBSP}m`;
}

export function formatHumidity(percent: number | null): string {
  return percent === null ? "unavailable" : `${percent.toFixed(0)}${NBSP}%`;
}
