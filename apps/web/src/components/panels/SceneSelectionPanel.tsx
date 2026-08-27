"use client";

import React from "react";

import type {
  BackendRiskAssessment,
  CanonicalWeatherRecord,
  EverestCamp,
} from "@/api/types";
import type { SceneSelection } from "@/cesium/selection";
import { t, type Locale } from "@/i18n/t";
import {
  formatTemperature,
  formatVisibility,
  formatWindDirection,
  formatWindSpeed,
} from "@/lib/units";

interface SceneSelectionPanelProps {
  selection: SceneSelection | null;
  records: CanonicalWeatherRecord[];
  camps?: EverestCamp[];
  summit?: EverestCamp | null;
  risk?: BackendRiskAssessment | null;
  onSelectCamp?: (camp: EverestCamp) => void;
  locale?: Locale;
}

export function nearestDisplayedWeatherRecord(
  records: CanonicalWeatherRecord[],
  latitude: number,
  longitude: number,
): CanonicalWeatherRecord | null {
  let nearest: CanonicalWeatherRecord | null = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  for (const record of records) {
    const distance =
      (record.latitude - latitude) ** 2 + (record.longitude - longitude) ** 2;
    if (distance < nearestDistance) {
      nearest = record;
      nearestDistance = distance;
    }
  }
  return nearest;
}

function selectedCoordinate(selection: SceneSelection): {
  latitude: number;
  longitude: number;
} {
  if (selection.kind === "camp") {
    return {
      latitude: selection.camp.latitude,
      longitude: selection.camp.longitude,
    };
  }
  if (selection.kind === "weather") {
    return {
      latitude: selection.record.latitude,
      longitude: selection.record.longitude,
    };
  }
  return {
    latitude: selection.coordinate[0],
    longitude: selection.coordinate[1],
  };
}

function selectionName(selection: SceneSelection): string {
  if (selection.kind === "camp") return selection.camp.name;
  if (selection.kind === "route") return "South Col route";
  return `${selection.record.source} · ${selection.record.spatial_key}`;
}

function supportsBackendRisk(selection: SceneSelection): boolean {
  if (selection.kind !== "camp") return false;
  return (
    selection.camp.name === "Camp 4S South Col" ||
    selection.camp.name === "Summit"
  );
}

export function SceneSelectionPanel({
  selection,
  records,
  camps = [],
  summit = null,
  risk = null,
  onSelectCamp,
  locale = "en",
}: SceneSelectionPanelProps): React.JSX.Element {
  const coordinate = selection ? selectedCoordinate(selection) : null;
  const nearest = coordinate
    ? nearestDisplayedWeatherRecord(
        records,
        coordinate.latitude,
        coordinate.longitude,
      )
    : null;
  const riskAvailable = selection ? supportsBackendRisk(selection) : false;
  const selectableCamps = summit ? [...camps, summit] : camps;

  return (
    <section
      className="selection-panel"
      aria-label={t("selection.title", locale)}
    >
      <h2>{t("selection.title", locale)}</h2>
      <div className="selection-panel__camp-list">
        <p>{t("selection.keyboardCamps", locale)}</p>
        <ul>
          {selectableCamps.map((camp) => (
            <li key={`${camp.osm_ref ?? "summit"}-${camp.name}`}>
              <button type="button" onClick={() => onSelectCamp?.(camp)}>
                {camp.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
      {selection === null || coordinate === null ? (
        <p>{t("selection.none", locale)}</p>
      ) : (
        <>
          <h3>{selectionName(selection)}</h3>
          <dl>
            <div>
              <dt>{t("selection.coordinate", locale)}</dt>
              <dd>
                {coordinate.latitude.toFixed(6)}°,{" "}
                {coordinate.longitude.toFixed(6)}°
              </dd>
            </div>
          </dl>
          <h3>{t("selection.nearestGrid", locale)}</h3>
          {nearest ? (
            <>
              <p>
                {nearest.source} · {nearest.model ?? "—"} · {nearest.timestamp}
              </p>
              <dl>
                <div>
                  <dt>{t("units.temperature", locale)}</dt>
                  <dd>{formatTemperature(nearest.temperature)}</dd>
                </div>
                <div>
                  <dt>{t("units.windSpeed", locale)}</dt>
                  <dd>
                    {formatWindSpeed(nearest.wind_speed)} ·{" "}
                    {formatWindDirection(nearest.wind_direction)}
                  </dd>
                </div>
                <div>
                  <dt>{t("units.visibility", locale)}</dt>
                  <dd>{formatVisibility(nearest.visibility)}</dd>
                </div>
              </dl>
            </>
          ) : (
            <p>{t("selection.noDisplayedWeather", locale)}</p>
          )}
          <h3>{t("selection.backendRisk", locale)}</h3>
          {riskAvailable && risk ? (
            <p>
              <strong>{risk.level.toUpperCase()}</strong> · {risk.basis} ·{" "}
              {risk.profile}
            </p>
          ) : (
            <p>
              {t("selection.riskUnavailable", locale)} ·{" "}
              {t("selection.nonAuthoritative", locale)}
            </p>
          )}
        </>
      )}
      <style>{`
        .selection-panel {
          border: 1px solid #2c3a52;
          border-radius: 8px;
          padding: 12px;
        }
        .selection-panel h2,
        .selection-panel h3 {
          margin: 0 0 8px;
        }
        .selection-panel h3 {
          margin-top: 12px;
          font-size: 13px;
        }
        .selection-panel p,
        .selection-panel dl {
          margin: 6px 0;
          font-size: 12px;
        }
        .selection-panel dl div {
          display: flex;
          justify-content: space-between;
          gap: 12px;
        }
        .selection-panel dt {
          color: #9aa5b8;
        }
        .selection-panel__camp-list ul {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          list-style: none;
          margin: 0;
          padding: 0;
        }
        .selection-panel__camp-list button {
          min-height: 32px;
          border: 1px solid #3b4c6b;
          border-radius: 5px;
          background: #141a24;
          color: #e6eaf2;
          cursor: pointer;
          padding: 4px 8px;
        }
        .selection-panel__camp-list button:focus-visible {
          outline: 2px solid #38bdf8;
          outline-offset: 2px;
        }
      `}</style>
    </section>
  );
}
