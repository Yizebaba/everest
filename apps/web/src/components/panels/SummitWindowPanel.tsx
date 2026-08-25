"use client";

import { useMemo } from "react";

import { getProfile } from "@/api/client";
import type {
  CanonicalWeatherRecord,
  CurrentResponse,
  ForecastResponse,
} from "@/api/types";
import { SUMMIT_THRESHOLDS, STALE_AFTER_HOURS } from "@/config/summitWindow";
import { summitBasisRecord } from "@/lib/geo";
import {
  formatPrecipitation,
  formatTemperature,
  formatVisibility,
  formatWindDirection,
  formatWindSpeed,
} from "@/lib/units";
import { useApiFetch, type FetchState } from "@/state/useApiFetch";

export type SummitScore = "GO" | "CAUTION" | "STOP";

export function scoreSummitRecord(
  record: CanonicalWeatherRecord,
): SummitScore | null {
  if (!isClean(record) || record.wind_speed === null) {
    return null;
  }
  const windSpeed = record.wind_speed;
  if (windSpeed <= SUMMIT_THRESHOLDS.goMaxWind) {
    return "GO";
  }
  if (windSpeed <= SUMMIT_THRESHOLDS.cautionMaxWind) {
    return "CAUTION";
  }
  return "STOP";
}

function isClean(record: CanonicalWeatherRecord): boolean {
  return (
    record.quality_flags.length > 0 &&
    record.quality_flags.every((flag) => flag === "clean")
  );
}

export interface SummitWindowPanelProps {
  current: FetchState<CurrentResponse>;
  forecast: FetchState<ForecastResponse>;
}

export function SummitWindowPanel({
  current,
  forecast,
}: SummitWindowPanelProps): React.JSX.Element {
  const profile = useApiFetch(() => getProfile("SUMMIT"));

  const pool: CanonicalWeatherRecord[] = useMemo(
    () => [
      ...(profile.data?.records ?? []),
      ...(current.data?.records ?? []),
      ...(forecast.data?.records ?? []),
    ],
    [current.data, forecast.data, profile.data],
  );

  const basis = useMemo(() => summitBasisRecord(pool), [pool]);

  const agreement = useMemo(() => {
    if (!basis) {
      return null;
    }
    const bySource = new Map<string, CanonicalWeatherRecord>();
    for (const record of pool) {
      if (!bySource.has(record.source)) {
        bySource.set(record.source, record);
      }
    }
    const counts = { GO: 0, CAUTION: 0, STOP: 0 };
    let cleanSources = 0;
    let staleSources = 0;
    for (const [source, record] of bySource) {
      if (!isClean(record)) {
        continue;
      }
      cleanSources += 1;
      if (record.wind_speed !== null && record.wind_speed !== undefined) {
        const score = scoreSummitRecord(record);
        if (score) {
          counts[score] += 1;
        }
      }
      const hoursOld =
        (Date.now() - new Date(record.timestamp).getTime()) / 3_600_000;
      if (hoursOld > STALE_AFTER_HOURS) {
        staleSources += 1;
      }
      void source;
    }
    return { counts, cleanSources, staleSources };
  }, [basis, pool]);

  const basisTime = basis ? new Date(basis.timestamp).getTime() : null;
  const staleness =
    basisTime === null ? null : (Date.now() - basisTime) / 3_600_000;

  return (
    <section aria-label="Summit Window" className="summit-window">
      <h2>Summit Window</h2>
      {basis === null ? (
        <p>No data for this selection</p>
      ) : (
        <>
          {scoreSummitRecord(basis) ? (
            <p
              className="summit-window__state"
              data-state={scoreSummitRecord(basis)?.toLowerCase()}
            >
              {scoreSummitRecord(basis)}
            </p>
          ) : (
            <p className="summit-window__state" data-state="unavailable">
              unavailable
            </p>
          )}
          {!isClean(basis) && (
            <p className="summit-window__flag">
              {basis.quality_flags.join(", ")}
            </p>
          )}
          <dl className="summit-window__values">
            <div>
              <dt>Temperature</dt>
              <dd>{formatTemperature(basis.temperature ?? null)}</dd>
            </div>
            <div>
              <dt>Wind</dt>
              <dd>
                {`${formatWindSpeed(basis.wind_speed ?? null)} · ${formatWindDirection(basis.wind_direction ?? null)}`}
              </dd>
            </div>
            <div>
              <dt>Visibility</dt>
              <dd>{formatVisibility(basis.visibility ?? null)}</dd>
            </div>
            <div>
              <dt>Precipitation</dt>
              <dd>{formatPrecipitation(basis.precipitation ?? null)}</dd>
            </div>
          </dl>
          <p className="summit-window__basis">
            basis: {basis.source} · {basis.model ?? "–"} · {basis.timestamp} ·{" "}
            {basis.spatial_key}
            {basis.forecast_cycle && ` · cycle ${basis.forecast_cycle}`}
            {basis.forecast_lead_time !== null &&
              basis.forecast_lead_time !== undefined &&
              ` · lead ${basis.forecast_lead_time}s`}
          </p>
          {agreement && (
            <p className="summit-window__agreement">
              agreement (clean sources): GO {agreement.counts.GO} · CAUTION{" "}
              {agreement.counts.CAUTION} · STOP {agreement.counts.STOP} ·
              sources {agreement.cleanSources} · stale {agreement.staleSources}
            </p>
          )}
          {staleness !== null && staleness > STALE_AFTER_HOURS && (
            <p className="summit-window__staleness">
              stale basis ({Math.round(staleness)} h)
            </p>
          )}
          <p className="summit-window__note">
            non-authoritative presentation layer · thresholds wind ≤ 15 / ≤ 25
            m/s
          </p>
        </>
      )}
      <style jsx>{`
        .summit-window {
          border: 1px solid #232c40;
          border-radius: 8px;
          padding: 16px;
          background: #111623;
        }
        .summit-window__state {
          font-weight: 700;
          font-size: 24px;
        }
        .summit-window__state[data-state="go"] {
          color: #2fbf71;
        }
        .summit-window__state[data-state="caution"] {
          color: #e8a33d;
        }
        .summit-window__state[data-state="stop"] {
          color: #ef5350;
        }
        .summit-window__state[data-state="unavailable"] {
          color: #9aa5b8;
        }
        .summit-window__values {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .summit-window__values dt {
          font-size: 11px;
          color: #9aa5b8;
        }
        .summit-window__basis,
        .summit-window__note,
        .summit-window__agreement,
        .summit-window__staleness {
          font-size: 11px;
          color: #9aa5b8;
        }
        .summit-window__flag,
        .summit-window__staleness {
          color: #d8b36a;
        }
      `}</style>
    </section>
  );
}
