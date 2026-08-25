"use client";

import { useEffect, useRef } from "react";

import type { CanonicalWeatherRecord } from "@/api/types";

export interface ProvenancePopoverProps {
  record: CanonicalWeatherRecord | null;
  onClose: () => void;
}

export function ProvenancePopover({
  record,
  onClose,
}: ProvenancePopoverProps): React.JSX.Element | null {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (record) {
      ref.current?.focus();
    }
  }, [record]);

  if (!record) {
    return null;
  }

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="Record provenance"
      tabIndex={-1}
      className="provenance"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          onClose();
        }
      }}
    >
      <button type="button" onClick={onClose} aria-label="Close">
        ×
      </button>
      <dl>
        <div>
          <dt>source</dt>
          <dd>{record.source}</dd>
        </div>
        <div>
          <dt>model</dt>
          <dd>{record.model ?? "–"}</dd>
        </div>
        <div>
          <dt>record_type</dt>
          <dd>{record.record_type}</dd>
        </div>
        <div>
          <dt>timestamp</dt>
          <dd>{record.timestamp}</dd>
        </div>
        <div>
          <dt>cycle</dt>
          <dd>{record.forecast_cycle ?? "–"}</dd>
        </div>
        <div>
          <dt>lead (s)</dt>
          <dd>{record.forecast_lead_time ?? "–"}</dd>
        </div>
        <div>
          <dt>spatial_key</dt>
          <dd>{record.spatial_key}</dd>
        </div>
        <div>
          <dt>flags</dt>
          <dd>{record.quality_flags.join(", ") || "clean"}</dd>
        </div>
      </dl>
      <style jsx>{`
        .provenance {
          position: fixed;
          right: 416px;
          top: 16px;
          width: 300px;
          background: #161d2e;
          border: 1px solid #232c40;
          border-radius: 8px;
          padding: 12px;
        }
        dl {
          margin: 0;
          display: grid;
          grid-template-columns: 90px 1fr;
          gap: 4px;
          font-size: 12px;
        }
        dt {
          color: #9aa5b8;
        }
      `}</style>
    </div>
  );
}
