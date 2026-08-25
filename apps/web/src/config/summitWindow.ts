export interface SummitThresholds {
  goMaxWind: number;
  cautionMaxWind: number;
}

export const SUMMIT_THRESHOLDS: SummitThresholds = {
  goMaxWind: 15,
  cautionMaxWind: 25,
};

export const STALE_AFTER_HOURS = 6;
