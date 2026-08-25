"use client";

import { useMemo, useState } from "react";

import type { CanonicalWeatherRecord } from "@/api/types";

type Variable = "temperature" | "wind_speed" | "visibility";

const VARIABLES: Variable[] = ["temperature", "wind_speed", "visibility"];

function valueOf(
  record: CanonicalWeatherRecord,
  variable: Variable,
): number | null {
  switch (variable) {
    case "temperature":
      return record.temperature ?? null;
    case "wind_speed":
      return record.wind_speed ?? null;
    case "visibility":
      return record.visibility ?? null;
  }
}

export interface ModelDisagreementProps {
  records: CanonicalWeatherRecord[];
  loading: boolean;
  activeTime: string | null;
}

export function ModelDisagreement({
  records,
  loading,
  activeTime,
}: ModelDisagreementProps): React.JSX.Element {
  const [variable, setVariable] = useState<Variable>("wind_speed");

  const times = useMemo(
    () => [...new Set(records.map((r) => r.timestamp))].sort(),
    [records],
  );
  const selectedTime = activeTime ?? (times.length > 0 ? times[0] : null);

  const atTime = records.filter((record) => record.timestamp === selectedTime);

  const stats = useMemo(() => {
    const values = atTime
      .map((record) => valueOf(record, variable))
      .filter((value): value is number => value !== null)
      .sort((a, b) => a - b);
    if (values.length === 0) {
      return null;
    }
    const min = values[0];
    const max = values[values.length - 1];
    const mid =
      values.length % 2 === 1
        ? values[(values.length - 1) / 2]
        : (values[values.length / 2 - 1] + values[values.length / 2]) / 2;
    return { min, max, median: mid, count: values.length };
  }, [atTime, variable]);

  return (
    <section aria-label="Model disagreement" className="disagreement">
      <h2>Model disagreement</h2>
      <div role="group" aria-label="Variable">
        {VARIABLES.map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setVariable(v)}
            aria-pressed={variable === v}
          >
            {v}
          </button>
        ))}
      </div>
      {loading && <p>…</p>}
      {!loading && selectedTime === null && <p>No data for this selection</p>}
      {stats && (
        <dl>
          <div>
            <dt>time</dt>
            <dd>{selectedTime}</dd>
          </div>
          <div>
            <dt>min</dt>
            <dd>{stats.min.toFixed(1)}</dd>
          </div>
          <div>
            <dt>median</dt>
            <dd>{stats.median.toFixed(1)}</dd>
          </div>
          <div>
            <dt>max</dt>
            <dd>{stats.max.toFixed(1)}</dd>
          </div>
          <div>
            <dt>sources</dt>
            <dd>{stats.count}</dd>
          </div>
        </dl>
      )}
      {selectedTime && atTime.length > 0 && (
        <ul>
          {atTime.map((record) => (
            <li
              key={`${record.source}-${record.spatial_key}-${record.timestamp}-${record.forecast_cycle}`}
            >
              {record.source}:{" "}
              {valueOf(record, variable) === null
                ? "–"
                : valueOf(record, variable)?.toFixed(1)}
            </li>
          ))}
        </ul>
      )}
      <style jsx>{`
        dl {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px;
          font-size: 12px;
        }
        ul {
          list-style: none;
          margin: 8px 0 0;
          padding: 0;
          font-size: 12px;
        }
      `}</style>
    </section>
  );
}
