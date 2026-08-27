import type { WindFieldFrame, WindFieldResponse } from "@/api/types";

import { buildRegionalSeeds } from "./regional";

/** Fail closed if the backend cannot provide the exact requested frame. */
export function selectRenderableWindFrame(
  response: WindFieldResponse,
  requestedValidTime?: string,
): WindFieldFrame | null {
  if (response.status !== "available") return null;
  if (
    requestedValidTime !== undefined &&
    response.frame.valid_time !== requestedValidTime
  ) {
    return null;
  }
  return buildRegionalSeeds(response.frame, { maxSeeds: 1 }).length > 0
    ? response.frame
    : null;
}
