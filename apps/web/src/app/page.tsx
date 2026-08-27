"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import {
  getCurrent,
  getEverestRoute,
  getForecast,
  getSummitWindowRisk,
  getTerrainTile,
} from "@/api/client";
import { DomainStatusBar } from "@/components/layout/DomainStatusBar";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { CampLadder } from "@/components/panels/CampLadder";
import { CurrentWeatherPanel } from "@/components/panels/CurrentWeatherPanel";
import { ForecastPanel } from "@/components/panels/ForecastPanel";
import { ModelDisagreement } from "@/components/panels/ModelDisagreement";
import { ProvenancePopover } from "@/components/panels/ProvenancePopover";
import { SceneSelectionPanel } from "@/components/panels/SceneSelectionPanel";
import { SourcesPanel } from "@/components/panels/SourcesPanel";
import { SummitWindowPanel } from "@/components/panels/SummitWindowPanel";
import { VerticalProfilePanel } from "@/components/panels/VerticalProfilePanel";
import type { CanonicalWeatherRecord } from "@/api/types";
import type { SceneSelection } from "@/cesium/selection";
import { t, type Locale } from "@/i18n/t";
import { AOI_CENTER } from "@/lib/geo";
import { selectMapRecords } from "@/lib/weatherFlow";
import { useApiFetch } from "@/state/useApiFetch";

const EverestScene = dynamic(
  () => import("@/cesium/EverestScene").then((m) => m.EverestScene),
  { ssr: false },
);

export default function Page(): React.JSX.Element {
  const [provenance, setProvenance] = useState<CanonicalWeatherRecord | null>(
    null,
  );
  const [activeTime, setActiveTime] = useState<string | null>(null);
  const [selection, setSelection] = useState<SceneSelection | null>(null);
  const [locale, setLocale] = useState<Locale>("en");

  const current = useApiFetch(() => getCurrent());
  const forecast = useApiFetch(() => getForecast());
  const terrain = useApiFetch(() =>
    getTerrainTile(AOI_CENTER.latitude, AOI_CENTER.longitude),
  );
  const everestRoute = useApiFetch(() => getEverestRoute());
  const risk = useApiFetch(() => getSummitWindowRisk());

  const records = selectMapRecords(
    current.data?.records ?? [],
    forecast.data?.records ?? [],
    activeTime,
  );

  const terrainStatus = terrain.data?.tile ? "ok" : "empty";
  const weatherStatus =
    (current.data?.records ?? []).length > 0 ? "ok" : "empty";
  const routeStatus =
    (everestRoute.data?.route.length ?? 0) > 0 ? "ok" : "empty";
  const riskStatus =
    risk.data?.risk.basis === "persisted_canonical_weather" ? "ok" : "empty";

  return (
    <main className="dashboard">
      <header className="dashboard__header">
        <h1>{t("app.title", locale)}</h1>
        <DomainStatusBar
          locale={locale}
          terrainStatus={terrainStatus}
          weatherStatus={weatherStatus}
          routeStatus={routeStatus}
          routeNodeCount={everestRoute.data?.route.length ?? 0}
          riskStatus={riskStatus}
        />
        <LanguageSwitcher locale={locale} onLocaleChange={setLocale} />
      </header>
      <div className="dashboard__body">
        <div className="dashboard__scene">
          <EverestScene
            records={records}
            camps={everestRoute.data?.camps ?? []}
            route={everestRoute.data?.route ?? []}
            summit={everestRoute.data?.summit ?? null}
            locale={locale}
            onSelectRecord={setProvenance}
            onSelect={setSelection}
          />
        </div>
        <aside
          className="dashboard__rail"
          aria-label={t("panels.dataPanels", locale)}
        >
          <SceneSelectionPanel
            selection={selection}
            records={records}
            camps={everestRoute.data?.camps ?? []}
            summit={everestRoute.data?.summit ?? null}
            route={everestRoute.data?.route ?? []}
            risk={risk.data?.risk ?? null}
            onSelectCamp={(camp) => {
              setSelection({ kind: "camp", camp });
              setProvenance(null);
            }}
            onSelectRoute={(route) => {
              const coordinate = route[0];
              if (coordinate) {
                setSelection({ kind: "route", route, coordinate });
                setProvenance(null);
              }
            }}
            locale={locale}
          />
          <SummitWindowPanel
            current={current}
            forecast={forecast}
            locale={locale}
          />
          <CurrentWeatherPanel state={current} locale={locale} />
          <ForecastPanel
            state={forecast}
            activeTime={activeTime}
            onActiveTimeChange={setActiveTime}
            locale={locale}
          />
          <VerticalProfilePanel
            records={forecast.data?.records ?? []}
            activeTime={activeTime}
            locale={locale}
          />
          <CampLadder locale={locale} />
          <ModelDisagreement
            records={forecast.data?.records ?? []}
            loading={forecast.status === "loading"}
            activeTime={activeTime}
            locale={locale}
          />
          <SourcesPanel locale={locale} />
        </aside>
      </div>
      <ProvenancePopover
        record={provenance}
        onClose={() => setProvenance(null)}
      />
      <style jsx>{`
        .dashboard {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: #0b0e14;
          color: #e6eaf2;
          font-family: Inter, system-ui, sans-serif;
        }
        .dashboard__header {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 8px 16px;
          border-bottom: 1px solid #232c40;
        }
        .dashboard__header h1 {
          font-size: 16px;
          margin: 0;
          white-space: nowrap;
        }
        .dashboard__body {
          display: grid;
          grid-template-columns: 1fr 400px;
          flex: 1;
          min-height: 0;
        }
        .dashboard__scene {
          position: relative;
          min-width: 0;
        }
        .dashboard__rail {
          border-left: 1px solid #232c40;
          padding: 16px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
      `}</style>
    </main>
  );
}
