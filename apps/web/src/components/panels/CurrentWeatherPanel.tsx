"use client";

import type { CurrentResponse } from "@/api/types";
import type { FetchState } from "@/state/useApiFetch";

export interface CurrentWeatherPanelProps {
  state: FetchState<CurrentResponse>;
}

export function CurrentWeatherPanel({
  state,
}: CurrentWeatherPanelProps): React.JSX.Element {
  if (state.status === "idle" || state.status === "loading") {
    return (
      <section aria-label="Current weather" aria-busy="true">
        <h2>Current Weather</h2>
        <p>Loading…</p>
      </section>
    );
  }
  if (state.status === "error") {
    const correlationId =
      state.error && "correlationId" in state.error
        ? String(state.error.correlationId)
        : null;
    return (
      <section aria-label="Current weather" role="alert">
        <h2>Current Weather</h2>
        <p>{state.error?.message ?? "Request failed"}</p>
        {correlationId && <p>Correlation ID: {correlationId}</p>}
        <button type="button" onClick={state.refetch}>
          Retry
        </button>
      </section>
    );
  }

  const records = state.data?.records ?? [];
  return (
    <section aria-label="Current weather" className="current-weather">
      <h2>Current Weather</h2>
      {(state.data?.warningCount ?? 0) > 0 && (
        <p role="status">
          {state.data?.warningCount} invalid record(s) isolated
        </p>
      )}
      {records.length === 0 ? (
        <p>No current weather records available</p>
      ) : (
        <ul>
          {records.map((record) => (
            <li
              key={`${record.source}-${record.spatial_key}-${record.timestamp}-${record.forecast_cycle}`}
            >
              <strong>{record.record_type}</strong> · valid {record.timestamp}
              <br />
              {record.source} / {record.model ?? "no model"}
              {record.record_type === "forecast" && (
                <small> · forecast, not an observation</small>
              )}
            </li>
          ))}
        </ul>
      )}
      <style jsx>{`
        .current-weather {
          border: 1px solid #232c40;
          border-radius: 8px;
          padding: 12px;
        }
        ul {
          list-style: none;
          margin: 0;
          padding: 0;
        }
        li {
          margin-top: 8px;
          font-size: 12px;
        }
        small {
          color: #d8b36a;
        }
      `}</style>
    </section>
  );
}
