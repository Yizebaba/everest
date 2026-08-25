"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { ForecastResponse } from "@/api/types";
import type { FetchState } from "@/state/useApiFetch";

const SOURCE_COLORS: Record<string, string> = {
  "ecmwf-ifs": "#38BDF8",
  "ecmwf-aifs": "#818CF8",
  "noaa-gfs": "#C084FC",
  "dwd-icon": "#2DD4BF",
};

const STEP_MS = 750;

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
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const currentIndex =
    activeTime == null ? -1 : distinctTimes.indexOf(activeTime);

  useEffect(() => {
    if (!playing) {
      return undefined;
    }
    if (distinctTimes.length === 0) {
      setPlaying(false);
      return undefined;
    }
    timerRef.current = setInterval(() => {
      const index =
        activeTime == null ? 0 : Math.max(0, distinctTimes.indexOf(activeTime));
      const next = (index + 1) % distinctTimes.length;
      onActiveTimeChange?.(distinctTimes[next]);
    }, STEP_MS);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, distinctTimes, activeTime]);

  const step = (direction: 1 | -1): void => {
    if (distinctTimes.length === 0) {
      return;
    }
    const index = activeTime == null ? -1 : distinctTimes.indexOf(activeTime);
    const nextIndex =
      direction === 1
        ? (index + 1) % distinctTimes.length
        : (index - 1 + distinctTimes.length) % distinctTimes.length;
    onActiveTimeChange?.(distinctTimes[nextIndex]);
  };

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
      <div
        className="forecast__time-nav"
        role="group"
        aria-label="Time navigation"
      >
        <button
          type="button"
          onClick={() => step(-1)}
          disabled={distinctTimes.length === 0}
          aria-label="Previous valid time"
        >
          ‹
        </button>
        <button
          type="button"
          onClick={() => setPlaying((value) => !value)}
          disabled={distinctTimes.length === 0}
          aria-pressed={playing}
        >
          {playing ? "⏸" : "▶"}
        </button>
        <button
          type="button"
          onClick={() => step(1)}
          disabled={distinctTimes.length === 0}
          aria-label="Next valid time"
        >
          ›
        </button>
        <input
          type="range"
          min={0}
          max={Math.max(0, distinctTimes.length - 1)}
          value={currentIndex < 0 ? 0 : currentIndex}
          aria-label="Forecast valid time"
          onChange={(event) =>
            onActiveTimeChange?.(
              distinctTimes[Number(event.target.value)] ?? null,
            )
          }
        />
        <span className="forecast__time-value">{activeTime ?? "—"}</span>
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
        .forecast__time-nav {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 8px;
        }
        .forecast__time-nav button {
          font-size: 12px;
          background: #161d2e;
          border: 1px solid #232c40;
          color: #e6eaf2;
          padding: 2px 8px;
          cursor: pointer;
        }
        .forecast__time-nav button[aria-pressed="true"] {
          border-color: #7fb4ff;
          color: #7fb4ff;
        }
        .forecast__time-nav input {
          flex: 1;
          min-width: 0;
        }
        .forecast__time-value {
          font-size: 11px;
          color: #9aa5b8;
          min-width: 130px;
          white-space: nowrap;
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
