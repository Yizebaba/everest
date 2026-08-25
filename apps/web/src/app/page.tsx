"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import { getCurrent, getSatellite, getTerrainTile } from "@/api/client";
import { CampLadder } from "@/components/panels/CampLadder";
import { ForecastPanel } from "@/components/panels/ForecastPanel";
import { ModelDisagreement } from "@/components/panels/ModelDisagreement";
import { ProvenancePopover } from "@/components/panels/ProvenancePopover";
import { SourcesPanel } from "@/components/panels/SourcesPanel";
import { SummitWindowPanel } from "@/components/panels/SummitWindowPanel";
import { TimeNav } from "@/components/panels/TimeNav";
import type { CanonicalWeatherRecord } from "@/api/types";
import { AOI_CENTER, withinAoi } from "@/lib/geo";
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
  const terrain = useApiFetch(() =>
    getTerrainTile(AOI_CENTER.latitude, AOI_CENTER.longitude),
  );
  const satellite = useApiFetch(() => getSatellite());

  const records = (current.data?.records ?? [])
    .filter((record) => activeTime === null || record.timestamp === activeTime)
    .filter((record) => withinAoi(record.latitude, record.longitude));

  return (
    <main className="dashboard">
      <div className="dashboard__scene">
        <EverestScene
          records={records}
          terrainTile={terrain.data ?? null}
          satelliteSegments={satellite.data?.segments ?? []}
          onSelectRecord={setProvenance}
        />
      </div>
      <aside className="dashboard__rail" aria-label="Data panels">
        <SummitWindowPanel />
        <ForecastPanel
          onActiveTimeChange={setActiveTime}
          activeTime={activeTime}
        />
        <TimeNav activeTime={activeTime} onActiveTimeChange={setActiveTime} />
        <CampLadder />
        <ModelDisagreement />
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
          height: 100vh;
          background: #0b0e14;
          color: #e6eaf2;
          font-family: Inter, system-ui, sans-serif;
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
