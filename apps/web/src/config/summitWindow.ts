export interface SummitThresholds {
  goMaxWind: number;
  cautionMaxWind: number;
  precipitationCaution: number;
  visibilityCaution: number;
  temperatureCaution: number;
}

export const SUMMIT_THRESHOLDS: SummitThresholds = {
  goMaxWind: 15,
  cautionMaxWind: 25,
  precipitationCaution: 0.1,
  visibilityCaution: 200,
  temperatureCaution: -25,
};

export const STALE_AFTER_HOURS = 6;
