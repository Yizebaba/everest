"use client";

import { useMemo } from "react";

import type { CanonicalWeatherRecord } from "@/api/types";

export interface VerticalProfilePanelProps {
  records: CanonicalWeatherRecord[];
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

export function VerticalProfilePanel({
  records,
}: VerticalProfilePanelProps): React.JSX.Element {
  const levels = useMemo(() => pressureLevels(records), [records]);

  if (levels.length === 0) {
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

  const maxTemp = Math.max(...levels.map((l) => l.temperature ?? -273), -273);
  const minTemp = Math.min(...levels.map((l) => l.temperature ?? 273), 273);
  const maxWind = Math.max(...levels.map((l) => l.wind_speed ?? 0), 0.01);

  return (
    <section className="profile-panel" aria-label="Vertical profile">
      <h2 className="profile-panel__title">Vertical profile</h2>
      <div className="profile-panel__legend">
        <span className="legend-dot legend-dot--temp">Temp °C</span>
        <span className="legend-dot legend-dot--wind">Wind m/s</span>
      </div>
      <div className="profile-panel__rows">
        {levels.map((level) => {
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
              <span className="profile-row__level">
                {level.altitude.toFixed(0)}m
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
              </span>
            </div>
          );
        })}
      </div>
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
          grid-template-columns: 56px 1fr 110px;
          align-items: center;
          gap: 8px;
          font-size: 0.72rem;
        }
        .profile-row__level {
          color: #9aa5b8;
          text-align: right;
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
