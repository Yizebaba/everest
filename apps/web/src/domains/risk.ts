import type { RiskResponse } from "@/api/types";
import type { Risk } from "@/types/schema";

/**
 * Presentation adapter for the backend risk engine response. This module does
 * not score weather and is not an independent risk authority.
 */
export function riskFromApi(response: RiskResponse): Risk {
  const assessment = response.risk;
  return {
    summitWindow: {
      level: assessment.level,
      confidence: assessment.confidence,
      validTime: assessment.valid_time,
      profile: assessment.profile,
      altitudeMetres: assessment.altitude_metres,
      factors: assessment.factors,
      inputs: assessment.inputs,
      basis: assessment.basis,
      authority: "backend-risk-engine",
    },
    hazards: { availability: "reserved", points: [] },
  };
}
