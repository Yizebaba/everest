"use client";

import { useMemo } from "react";

import type { CanonicalWeatherRecord } from "@/api/types";
import { compassPoint } from "@/lib/geo";

export interface VerticalProfilePanelProps {
  records: CanonicalWeatherRecord[];
  // The forecast hour the rest of the dashboard is showing. Without it the panel
  // stacked every lead's levels into one list, so a 13-lead cycle produced ~150
  // unordered rows and no readable vertical column.
  activeTime?: string | null;
}

/** Round a value to one decimal for compact display. */
function fmt(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return value.toFixed(1);
}

/** Filter canonical records to pressure-level entries, sorted by altitude. */
export function pressureLevels(
  records: CanonicalWeatherRecord[],
): CanonicalWeatherRecord[] {
  return records
    .filter((r) => /(hpa)$/.test(r.spatial_key ?? ""))
    .sort((a, b) => a.altitude - b.altitude);
}

export interface ProfileRow {
  record: CanonicalWeatherRecord;
  /** Where this row is: a named camp, or the model level it came from. */
  label: string;
  /** True when the values were interpolated between two model levels. */
  interpolated: boolean;
}

/** The single time column nearest ``activeTime``, or the earliest available. */
function nearestColumn(
  records: CanonicalWeatherRecord[],
  activeTime: string | null | undefined,
): string | null {
  if (records.length === 0) {
    return null;
  }
  const times = [...new Set(records.map((r) => r.timestamp))].sort();
  if (!activeTime) {
    return times[0];
  }
  const target = Date.parse(activeTime);
  if (Number.isNaN(target)) {
    return times[0];
  }
  return times.reduce((best, time) =>
    Math.abs(Date.parse(time) - target) < Math.abs(Date.parse(best) - target)
      ? time
      : best,
  );
}

/**
 * Build one labelled vertical column: named camps and raw model levels for a
 * single forecast hour, lowest first.
 *
 * The panel previously rendered only an altitude per row, so a camp's forecast
 * was indistinguishable from the model level beside it and the climber could
 * not tell which row was the South Col.
 */
export function profileRows(
  records: CanonicalWeatherRecord[],
  activeTime?: string | null,
): ProfileRow[] {
  const levels = pressureLevels(records);
  const column = nearestColumn(levels, activeTime);
  return levels
    .filter((record) => record.timestamp === column)
    .map((record) => {
      const interpolated = /:interp[\d-]+hpa$/.test(record.spatial_key ?? "");
      const level = /:(\d+)hpa$/.exec(record.spatial_key ?? "")?.[1];
      return {
        record,
        label: record.route_profile ?? (level ? `${level} hPa` : "model level"),
        interpolated,
      };
    });
}

export function VerticalProfilePanel({
  records,
  activeTime,
}: VerticalProfilePanelProps): React.JSX.Element {
  const rows = useMemo(
    () => profileRows(records, activeTime),
    [records, activeTime],
  );

  if (rows.length === 0) {
    return (
      <section className="profile-panel" aria-label="Vertical profile">
        <h2 className="profile-panel__title">Vertical profile</h2>
        <p className="profile-panel__empty">
          No pressure-level data yet. Pressure levels show wind/temperature at
          altitude (300 hPa ≈ summit).
        </p>
        <style jsx>{`
          .profile-panel {
            border: 1px solid #232c40;
            border-radius: 8px;
            padding: 12px;
            background: #10141d;
          }
          .profile-panel__title {
            font-size: 0.85rem;
            color: #9aa5b8;
            margin: 0 0 8px;
          }
          .profile-panel__empty {
            font-size: 0.75rem;
            color: #5c6f82;
            margin: 0;
          }
        `}</style>
      </section>
    );
  }

  const levels = rows.map((row) => row.record);
  const maxTemp = Math.max(...levels.map((l) => l.temperature ?? -273), -273);
  const minTemp = Math.min(...levels.map((l) => l.temperature ?? 273), 273);
  const maxWind = Math.max(...levels.map((l) => l.wind_speed ?? 0), 0.01);
  // Every row in ``rows`` shares one forecast hour, so the column can be stated
  // once in the header instead of being invisible per row.
  const column = levels[0]?.timestamp ?? null;

  return (
    <section className="profile-panel" aria-label="Vertical profile">
      <h2 className="profile-panel__title">
        Vertical profile
        {column ? (
          <span className="profile-panel__column"> · {column}</span>
        ) : null}
      </h2>
      <div className="profile-panel__legend">
        <span className="legend-dot legend-dot--temp">Temp °C</span>
        <span className="legend-dot legend-dot--wind">Wind m/s</span>
      </div>
      <div className="profile-panel__rows">
        {rows.map(({ record: level, label, interpolated }) => {
          const temp = level.temperature ?? null;
          const wind = level.wind_speed ?? null;
          const tempPct =
            temp === null || maxTemp === minTemp
              ? 0
              : ((temp - minTemp) / (maxTemp - minTemp)) * 100;
          const windPct = wind === null ? 0 : (wind / maxWind) * 100;
          return (
            <div
              className="profile-row"
              key={`${level.spatial_key}-${level.timestamp}`}
            >
              <span className="profile-row__label">
                <span className="profile-row__place">
                  {label}
                  {/* An interpolated camp value is not a model output; saying so
                      keeps the climber from reading it as directly forecast. */}
                  {interpolated ? (
                    <abbr
                      className="profile-row__interp"
                      title="Interpolated between the bracketing model levels"
                    >
                      ~
                    </abbr>
                  ) : null}
                </span>
                <span className="profile-row__altitude">
                  {level.altitude.toFixed(0)} m
                </span>
              </span>
              <div className="profile-row__bars">
                <div className="profile-row__bar profile-row__bar--temp">
                  <div
                    className="profile-row__fill profile-row__fill--temp"
                    style={{ width: `${Math.max(2, tempPct)}%` }}
                    title={`${level.spatial_key}: ${fmt(temp)}°C`}
                  />
                </div>
                <div className="profile-row__bar profile-row__bar--wind">
                  <div
                    className="profile-row__fill profile-row__fill--wind"
                    style={{ width: `${Math.max(2, windPct)}%` }}
                    title={`${level.spatial_key}: ${fmt(wind)} m/s`}
                  />
                </div>
              </div>
              <span className="profile-row__values">
                {fmt(temp)}°C · {fmt(wind)} m/s
                {/* Wind direction was persisted and drawn as a 3D barb but never
                    stated in text, so the panel could not answer which way the
                    wind crosses a camp. It is the bearing the wind blows from. */}
                {level.wind_direction === null ||
                level.wind_direction === undefined ? null : (
                  <span
                    className="profile-row__from"
                    title={`From ${level.wind_direction.toFixed(0)}°`}
                  >
                    {" "}
                    ← {compassPoint(level.wind_direction)}
                  </span>
                )}
              </span>
            </div>
          );
        })}
      </div>
      <style jsx>{`
        .profile-panel {
          background: transparent;
        }
        .profile-panel__title {
          font-size: 0.85rem;
          color: #9aa5b8;
          margin: 0 0 8px;
        }
        .profile-panel__legend {
          display: flex;
          gap: 12px;
          font-size: 0.7rem;
          color: #5c6f82;
          margin-bottom: 6px;
        }
        .legend-dot::before {
          content: "";
          display: inline-block;
          width: 8px;
          height: 8px;
          margin-right: 4px;
          border-radius: 2px;
        }
        .legend-dot--temp::before {
          background: #38bdf8;
        }
        .legend-dot--wind::before {
          background: #2dd4bf;
        }
        .profile-panel__rows {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .profile-row {
          display: grid;
          grid-template-columns: 104px 1fr 150px;
          align-items: center;
          gap: 8px;
          font-size: 0.72rem;
        }
        .profile-row__from {
          color: #9aa5b8;
        }
        .profile-panel__column {
          color: #5c6f82;
          font-weight: 400;
        }
        .profile-row__label {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          line-height: 1.25;
        }
        .profile-row__place {
          color: #c6cfdd;
        }
        .profile-row__interp {
          color: #5c6f82;
          border: none;
          text-decoration: none;
          margin-left: 2px;
        }
        .profile-row__altitude {
          color: #5c6f82;
          font-size: 0.66rem;
        }
        .profile-row__bars {
          display: flex;
          gap: 4px;
          align-items: center;
        }
        .profile-row__bar {
          flex: 1;
          height: 6px;
          background: #1a2230;
          border-radius: 3px;
          overflow: hidden;
        }
        .profile-row__fill {
          height: 100%;
          border-radius: 3px;
        }
        .profile-row__fill--temp {
          background: #38bdf8;
        }
        .profile-row__fill--wind {
          background: #2dd4bf;
        }
        .profile-row__values {
          color: #c6cfdd;
          white-space: nowrap;
        }
        .profile-panel__empty {
          font-size: 0.75rem;
          color: #5c6f82;
          margin: 0;
        }
      `}</style>
    </section>
  );
}
