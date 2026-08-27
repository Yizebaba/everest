"use client";

import { getProfile } from "@/api/client";
import type { ProfileResponse } from "@/api/types";
import type { ProfileLabel } from "@/api/types";
import { PROFILE_LABELS } from "@/api/validate";
import { useApiFetch, type FetchState } from "@/state/useApiFetch";
import { t, type Locale } from "@/i18n/t";

export function CampLadder({
  locale = "en",
}: {
  locale?: Locale;
}): React.JSX.Element {
  const ebc = useApiFetch(() => getProfile("EBC"));
  const c1 = useApiFetch(() => getProfile("C1"));
  const c2 = useApiFetch(() => getProfile("C2"));
  const c3 = useApiFetch(() => getProfile("C3"));
  const c4 = useApiFetch(() => getProfile("C4"));
  const summit = useApiFetch(() => getProfile("SUMMIT"));

  const states: Record<ProfileLabel, FetchState<ProfileResponse>> = {
    EBC: ebc,
    C1: c1,
    C2: c2,
    C3: c3,
    C4: c4,
    SUMMIT: summit,
  };

  return (
    <section aria-label={t("panels.altitudeLadder", locale)} className="ladder">
      <h2>{t("panels.altitudeLadder", locale)}</h2>
      <ol className="ladder__rungs">
        {PROFILE_LABELS.map((label) => {
          const state = states[label];
          const records = state?.data?.records ?? [];
          const latest = records[0];
          return (
            <li key={label} className="ladder__rung">
              <span className="ladder__label">{label}</span>
              {state?.status === "loading" ? (
                <span>…</span>
              ) : latest ? (
                <span>
                  {latest.altitude.toFixed(0)} m ·{" "}
                  {latest.temperature === null ||
                  latest.temperature === undefined
                    ? "–"
                    : `${latest.temperature.toFixed(1)}°C`}{" "}
                  ·{" "}
                  {latest.wind_speed === null || latest.wind_speed === undefined
                    ? "–"
                    : `${latest.wind_speed.toFixed(1)} m/s`}
                </span>
              ) : (
                <span>no data</span>
              )}
            </li>
          );
        })}
      </ol>
      <style jsx>{`
        .ladder__rungs {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .ladder__rung {
          display: flex;
          gap: 12px;
          font-size: 12px;
          align-items: baseline;
        }
        .ladder__label {
          font-weight: 700;
          min-width: 56px;
          color: #9aa5b8;
        }
      `}</style>
    </section>
  );
}
