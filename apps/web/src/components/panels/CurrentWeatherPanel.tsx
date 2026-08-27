"use client";

import type { CurrentResponse } from "@/api/types";
import type { FetchState } from "@/state/useApiFetch";
import { t, type Locale } from "@/i18n/t";
import { formatHumidity } from "@/lib/units";

export interface CurrentWeatherPanelProps {
  state: FetchState<CurrentResponse>;
  locale?: Locale;
}

export function CurrentWeatherPanel({
  state,
  locale = "en",
}: CurrentWeatherPanelProps): React.JSX.Element {
  if (state.status === "idle" || state.status === "loading") {
    return (
      <section aria-label={t("panels.currentWeather", locale)} aria-busy="true">
        <h2>{t("panels.currentWeather", locale)}</h2>
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
      <section aria-label={t("panels.currentWeather", locale)} role="alert">
        <h2>{t("panels.currentWeather", locale)}</h2>
        <p>{state.error?.message ?? "Request failed"}</p>
        {correlationId && <p>Correlation ID: {correlationId}</p>}
        <button type="button" onClick={state.refetch}>
          {t("app.retry", locale)}
        </button>
      </section>
    );
  }

  const records = state.data?.records ?? [];
  const visibleRecords = records.slice(0, 6);
  return (
    <section
      aria-label={t("panels.currentWeather", locale)}
      className="current-weather"
    >
      <h2>{t("panels.currentWeather", locale)}</h2>
      {(state.data?.warningCount ?? 0) > 0 && (
        <p role="status">
          {state.data?.warningCount} invalid record(s) isolated
        </p>
      )}
      {records.length === 0 ? (
        <p>No current weather records available</p>
      ) : (
        <>
          <p className="current-weather__count">
            latest {visibleRecords.length} of {records.length} records
          </p>
          <ul>
            {visibleRecords.map((record) => (
              <li
                key={`${record.source}-${record.spatial_key}-${record.timestamp}-${record.forecast_cycle}`}
              >
                <strong>{record.record_type}</strong> · valid {record.timestamp}
                <br />
                {record.source} / {record.model ?? "no model"}
                {record.record_type === "forecast" && (
                  <small> · forecast, not an observation</small>
                )}
                <dl className="current-weather__values">
                  {record.temperature !== null &&
                    record.temperature !== undefined && (
                      <div>
                        <dt>Temp</dt>
                        <dd>{record.temperature.toFixed(1)}°C</dd>
                      </div>
                    )}
                  {record.wind_speed !== null &&
                    record.wind_speed !== undefined && (
                      <div>
                        <dt>Wind</dt>
                        <dd>
                          {record.wind_speed.toFixed(1)} m/s
                          {record.wind_direction !== null &&
                            record.wind_direction !== undefined &&
                            ` · ${Math.round(record.wind_direction)}°`}
                        </dd>
                      </div>
                    )}
                  {record.relative_humidity !== null &&
                    record.relative_humidity !== undefined && (
                      <div>
                        <dt>{t("units.humidity", locale)}</dt>
                        <dd>{formatHumidity(record.relative_humidity)}</dd>
                      </div>
                    )}
                  {record.precipitation !== null &&
                    record.precipitation !== undefined && (
                      <div>
                        <dt>Precip</dt>
                        <dd>{record.precipitation.toFixed(1)} mm</dd>
                      </div>
                    )}
                  {record.visibility !== null &&
                    record.visibility !== undefined && (
                      <div>
                        <dt>Vis</dt>
                        <dd>{Math.round(record.visibility)} m</dd>
                      </div>
                    )}
                  {record.altitude !== null &&
                    record.altitude !== undefined && (
                      <div>
                        <dt>Alt</dt>
                        <dd>{Math.round(record.altitude)} m</dd>
                      </div>
                    )}
                </dl>
              </li>
            ))}
          </ul>
        </>
      )}
      <style jsx>{`
        .current-weather {
          border: 1px solid #232c40;
          border-radius: 8px;
          padding: 12px;
        }
        .current-weather__count {
          font-size: 11px;
          color: #9aa5b8;
          margin: 4px 0 0;
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
        .current-weather__values {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px 12px;
          margin: 6px 0 0;
        }
        .current-weather__values div {
          display: flex;
          gap: 6px;
        }
        .current-weather__values dt {
          color: #9aa5b8;
          min-width: 42px;
        }
        .current-weather__values dd {
          margin: 0;
          color: #e6eaf2;
        }
        small {
          color: #d8b36a;
        }
      `}</style>
    </section>
  );
}
