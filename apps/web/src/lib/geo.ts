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
