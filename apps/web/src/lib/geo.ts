export const AOI_CENTER = { latitude: 27.98806, longitude: 86.92528 };
export const AOI_RADIUS_METERS = 100_000;
export const SUMMIT_BASIS_RADIUS_METERS = 25_000;

const A = 6378137.0;
const F = 1 / 298.257223563;
const B = (1 - F) * A;

function radians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

export function vincentyDistanceMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const phi1 = radians(lat1);
  const phi2 = radians(lat2);
  const deltaLambda = radians(lon2 - lon1);
  const u1 = Math.atan((1 - F) * Math.tan(phi1));
  const u2 = Math.atan((1 - F) * Math.tan(phi2));
  const sinU1 = Math.sin(u1);
  const cosU1 = Math.cos(u1);
  const sinU2 = Math.sin(u2);
  const cosU2 = Math.cos(u2);

  let lambda = deltaLambda;
  let lambdaPrev: number;
  let sinSigma = 0;
  let cosSigma = 0;
  let sigma = 0;
  let cosSqAlpha = 0;
  let cos2SigmaM = 0;
  let iterations = 0;
  do {
    const sinLambda = Math.sin(lambda);
    const cosLambda = Math.cos(lambda);
    const sinSqSigma =
      cosU2 * sinLambda * (cosU2 * sinLambda) +
      (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) *
        (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda);
    if (sinSqSigma === 0) {
      return 0;
    }
    sinSigma = Math.sqrt(sinSqSigma);
    cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda;
    sigma = Math.atan2(sinSigma, cosSigma);
    const sinAlpha = (cosU1 * cosU2 * sinLambda) / sinSigma;
    cosSqAlpha = 1 - sinAlpha * sinAlpha;
    cos2SigmaM =
      cosSqAlpha === 0 ? 0 : cosSigma - (2 * sinU1 * sinU2) / cosSqAlpha;
    const c = (F / 16) * cosSqAlpha * (4 + F * (4 - 3 * cosSqAlpha));
    lambdaPrev = lambda;
    lambda =
      deltaLambda +
      (1 - c) *
        F *
        sinAlpha *
        (sigma +
          c *
            sinSigma *
            (cos2SigmaM + c * cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
    iterations += 1;
  } while (Math.abs(lambda - lambdaPrev) > 1e-12 && iterations < 200);

  const uSq = (cosSqAlpha * (A * A - B * B)) / (B * B);
  const a = 1 + (uSq / 16384) * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)));
  const b = (uSq / 1024) * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)));
  const deltaSigma =
    b *
    sinSigma *
    (cos2SigmaM +
      (b / 4) *
        (cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM) -
          (b / 6) *
            cos2SigmaM *
            (-3 + 4 * sinSigma * sinSigma) *
            (-3 + 4 * cos2SigmaM * cos2SigmaM)));
  return B * a * (sigma - deltaSigma);
}

export function withinAoi(latitude: number, longitude: number): boolean {
  return (
    vincentyDistanceMeters(
      latitude,
      longitude,
      AOI_CENTER.latitude,
      AOI_CENTER.longitude,
    ) <= AOI_RADIUS_METERS
  );
}

export function summitBasisRecord<
  T extends { latitude: number; longitude: number; altitude: number },
>(records: T[]): T | null {
  const within = records.filter(
    (record) =>
      vincentyDistanceMeters(
        record.latitude,
        record.longitude,
        AOI_CENTER.latitude,
        AOI_CENTER.longitude,
      ) <= SUMMIT_BASIS_RADIUS_METERS,
  );
  if (within.length === 0) {
    return null;
  }
  const sorted = [...within].sort((a, b) => {
    // Prefer the freshest record for the decision basis; distance is a
    // tie-break only when two records share the same timestamp.
    const timeA = (a as { timestamp?: string }).timestamp;
    const timeB = (b as { timestamp?: string }).timestamp;
    if (timeA !== undefined && timeB !== undefined && timeA !== timeB) {
      return timeA < timeB ? 1 : -1;
    }
    const distanceA = vincentyDistanceMeters(
      a.latitude,
      a.longitude,
      AOI_CENTER.latitude,
      AOI_CENTER.longitude,
    );
    const distanceB = vincentyDistanceMeters(
      b.latitude,
      b.longitude,
      AOI_CENTER.latitude,
      AOI_CENTER.longitude,
    );
    if (distanceA !== distanceB) {
      return distanceA - distanceB;
    }
    return b.altitude - a.altitude;
  });
  return sorted[0];
}

// Oxygen fraction relative to sea level as a standard elevation proxy
// (barometric formula), e.g. ~50% at ~5,500 m and ~33% at ~8,800 m.
// This is an engineering approximation for display ("est."), never a
// provider-reported value.
export function oxygenFractionAtAltitude(altitudeMeters: number): number {
  const seaLevelPressure = 1013.25;
  const scaleHeight = 8434.5;
  const seaLevelOxygen = 0.2095;
  return (
    (seaLevelOxygen *
      seaLevelPressure *
      Math.exp(-altitudeMeters / scaleHeight)) /
    seaLevelOxygen /
    seaLevelPressure
  );
}

// Expresses a meteorological wind direction (0-360 degrees, where 0 = north
// and the value is the direction FROM which the wind blows) as a unit vector
// pointing in the direction the wind travels TOWARD.
export function windVector(directionDegrees: number): { x: number; y: number } {
  const radians = ((directionDegrees + 180) * Math.PI) / 180;
  return { x: Math.sin(radians), y: Math.cos(radians) };
}

const COMPASS_POINTS = [
  "N",
  "NNE",
  "NE",
  "ENE",
  "E",
  "ESE",
  "SE",
  "SSE",
  "S",
  "SSW",
  "SW",
  "WSW",
  "W",
  "WNW",
  "NW",
  "NNW",
] as const;

// Names the bearing a wind blows FROM as one of the sixteen compass points, so a
// text readout can say "SSE" instead of leaving the reader to convert 157
// degrees. Out-of-range and negative bearings are wrapped rather than rejected;
// a provider reporting 360 means north, not an error.
export function compassPoint(directionDegrees: number): string {
  const wrapped = ((directionDegrees % 360) + 360) % 360;
  return COMPASS_POINTS[Math.round(wrapped / 22.5) % 16];
}

// Metres per degree of latitude. A degree of longitude spans this multiplied by
// cos(latitude), which at Everest's 28 degN is about 0.88 of it.
export const METERS_PER_DEGREE_LATITUDE = 111320;

// Converts a local east/north offset in metres into degree offsets at a given
// latitude. Dividing an eastward offset by the latitude figure alone (the
// scene's earlier shortcut) understates it by the cos(latitude) factor, which
// both rotated drawn wind vectors away from their reported bearing and made
// terrain slope probes sample a shorter run than the arctangent assumed.
export function metersToDegrees(
  latitude: number,
  eastMeters: number,
  northMeters: number,
): { deltaLongitude: number; deltaLatitude: number } {
  const scale = Math.cos(radians(latitude));
  return {
    // At a pole a metre east spans no finite number of degrees; report no
    // offset rather than an unbounded one that would propagate into a position.
    // The comparison needs a tolerance because cos(radians(90)) evaluates to
    // ~6e-17 rather than to zero, which would otherwise pass a plain !== 0 test
    // and yield an offset of ~10^14 degrees.
    deltaLongitude:
      Math.abs(scale) < 1e-12
        ? 0
        : eastMeters / (METERS_PER_DEGREE_LATITUDE * scale),
    deltaLatitude: northMeters / METERS_PER_DEGREE_LATITUDE,
  };
}

// Terrain steepness over a horizontal run, as a positive angle in degrees.
// Direction is not preserved: an ascent and a descent of the same gradient are
// equally steep to climb across.
export function slopeDegrees(riseMeters: number, runMeters: number): number {
  return (Math.atan2(Math.abs(riseMeters), runMeters) * 180) / Math.PI;
}
