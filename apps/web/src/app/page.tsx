"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import { getCurrent, getForecast } from "@/api/client";
import { CampLadder } from "@/components/panels/CampLadder";
import { CurrentWeatherPanel } from "@/components/panels/CurrentWeatherPanel";
import { ForecastPanel } from "@/components/panels/ForecastPanel";
import { ModelDisagreement } from "@/components/panels/ModelDisagreement";
import { ProvenancePopover } from "@/components/panels/ProvenancePopover";
import { SourcesPanel } from "@/components/panels/SourcesPanel";
import { SummitWindowPanel } from "@/components/panels/SummitWindowPanel";
import { VerticalProfilePanel } from "@/components/panels/VerticalProfilePanel";
import type { CanonicalWeatherRecord } from "@/api/types";
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

  const current = useApiFetch(() => getCurrent());
  const forecast = useApiFetch(() => getForecast());

  const records = selectMapRecords(
    current.data?.records ?? [],
    forecast.data?.records ?? [],
    activeTime,
  );

  return (
    <main className="dashboard">
      <div className="dashboard__scene">
        <EverestScene records={records} onSelectRecord={setProvenance} />
      </div>
      <aside className="dashboard__rail" aria-label="Data panels">
        <SummitWindowPanel current={current} forecast={forecast} />
        <CurrentWeatherPanel state={current} />
        <ForecastPanel
          state={forecast}
          onActiveTimeChange={setActiveTime}
          activeTime={activeTime}
        />
        <VerticalProfilePanel records={forecast.data?.records ?? []} />
        <CampLadder />
        <ModelDisagreement
          records={forecast.data?.records ?? []}
          loading={forecast.status === "loading"}
          activeTime={activeTime}
        />
        <SourcesPanel />
      </aside>
      <ProvenancePopover
        record={provenance}
        onClose={() => setProvenance(null)}
      />
      <style jsx>{`
        .dashboard {
          display: grid;
          grid-template-columns: 1fr 400px;
          grid-template-rows: 100vh;
          height: 100vh;
          overflow: hidden;
          background: #0b0e14;
          color: #e6eaf2;
          font-family: Inter, system-ui, sans-serif;
        }
        .dashboard__scene {
          position: relative;
          min-width: 0;
          min-height: 0;
          overflow: hidden;
        }
        .dashboard__rail {
          border-left: 1px solid #232c40;
          padding: 16px;
          overflow-y: auto;
          overflow-x: hidden;
          display: flex;
          flex-direction: column;
          gap: 16px;
          background: #0d1117;
          min-height: 0;
        }
        .dashboard__rail > :global(section),
        .dashboard__rail > :global(div) {
          background: #141a24;
          border: 1px solid #232c40;
          border-radius: 8px;
        }
      `}</style>
    </main>
  );
}
