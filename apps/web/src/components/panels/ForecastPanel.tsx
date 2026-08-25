"use client";

import { useMemo, useState } from "react";

import type { ForecastResponse } from "@/api/types";
import type { FetchState } from "@/state/useApiFetch";

const SOURCE_COLORS: Record<string, string> = {
  "ecmwf-ifs": "#38BDF8",
  "ecmwf-aifs": "#818CF8",
  "noaa-gfs": "#C084FC",
  "dwd-icon": "#2DD4BF",
};

export interface ForecastPanelProps {
  state: FetchState<ForecastResponse>;
  activeTime?: string | null;
  onActiveTimeChange?: (time: string | null) => void;
}

export function ForecastPanel({
  state,
  activeTime,
  onActiveTimeChange,
}: ForecastPanelProps): React.JSX.Element {
  const { status, data, error, refetch } = state;
  const [activeSource, setActiveSource] = useState<string>("all");

  const records = useMemo(() => data?.records ?? [], [data]);

  const distinctTimes = useMemo(() => {
    const times = new Set<string>();
    for (const record of records) {
      times.add(record.timestamp);
    }
    return [...times].sort();
  }, [records]);

  const sources = useMemo(() => {
    const set = new Set<string>();
    for (const record of records) {
      set.add(record.source);
    }
    return [...set].sort();
  }, [records]);

  const visible =
    activeSource === "all"
      ? records
      : records.filter((r) => r.source === activeSource);

  if (status === "idle" || status === "loading") {
    return (
      <section aria-label="Forecast" aria-busy="true">
        Loading…
      </section>
    );
  }
  if (status === "error") {
    return (
      <section aria-label="Forecast">
        {error?.message ?? "Request failed"}{" "}
        {error && "correlationId" in error && (
          <span>Correlation ID: {String(error.correlationId)} </span>
        )}
        <button type="button" onClick={refetch}>
          Retry
        </button>
      </section>
    );
  }

  return (
    <section aria-label="Forecast" className="forecast">
      <h2>Forecast</h2>
      {(data?.warningCount ?? 0) > 0 && (
        <p role="status">{data?.warningCount} invalid record(s) isolated</p>
      )}
      <div
        className="forecast__filters"
        role="group"
        aria-label="Source filter"
      >
        <button
          type="button"
          onClick={() => setActiveSource("all")}
          aria-pressed={activeSource === "all"}
        >
          All
        </button>
        {sources.map((source) => (
          <button
            key={source}
            type="button"
            onClick={() => setActiveSource(source)}
            aria-pressed={activeSource === source}
          >
            {source}
          </button>
        ))}
      </div>
      {distinctTimes.length === 0 ? (
        <p>No data for this selection</p>
      ) : (
        <>
          <div
            className="forecast__timeline"
            role="group"
            aria-label="Valid times"
          >
            {distinctTimes.map((time) => (
              <button
                key={time}
                type="button"
                aria-pressed={activeTime === time}
                onClick={() => onActiveTimeChange?.(time)}
              >
                {time.slice(11, 16)}Z
              </button>
            ))}
          </div>
          <ul className="forecast__times">
            {distinctTimes.map((time) => (
              <li key={time}>
                <time dateTime={time}>{time}</time>
                {visible
                  .filter((record) => record.timestamp === time)
                  .map((record) => (
                    <span
                      key={`${record.source}-${record.spatial_key}-${record.timestamp}-${record.forecast_cycle}`}
                      style={{
                        color: SOURCE_COLORS[record.source] ?? "#9AA5B8",
                      }}
                    >
                      {record.source} ·{" "}
                      {record.temperature === null ||
                      record.temperature === undefined
                        ? "–"
                        : `${record.temperature.toFixed(1)}°C`}
                      {record.wind_speed !== null &&
                        record.wind_speed !== undefined &&
                        ` · ${record.wind_speed.toFixed(1)} m/s`}
                      {record.precipitation !== null &&
                        record.precipitation !== undefined &&
                        ` · ${record.precipitation.toFixed(1)} mm`}
                      {record.visibility !== null &&
                        record.visibility !== undefined &&
                        ` · ${Math.round(record.visibility)} m vis`}
                    </span>
                  ))}
              </li>
            ))}
          </ul>
        </>
      )}
      <style jsx>{`
        .forecast__filters {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }
        .forecast__timeline {
          display: flex;
          gap: 4px;
          margin-bottom: 8px;
          flex-wrap: wrap;
        }
        .forecast__timeline button {
          font-size: 11px;
          background: #161d2e;
          border: 1px solid #232c40;
          color: #e6eaf2;
        }
        .forecast__timeline button[aria-pressed="true"] {
          border-color: #7fb4ff;
        }
        .forecast__times {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
          max-height: 260px;
          overflow-y: auto;
        }
        .forecast__times li {
          display: flex;
          gap: 8px;
          font-size: 12px;
        }
        .forecast__times time {
          color: #9aa5b8;
          min-width: 150px;
        }
      `}</style>
    </section>
  );
}
