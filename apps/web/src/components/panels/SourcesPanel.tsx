"use client";

import { getDataHealth, getSources } from "@/api/client";
import { t, type Locale } from "@/i18n/t";
import { useApiFetch } from "@/state/useApiFetch";

export interface SourcesPanelProps {
  locale?: Locale;
}

export function SourcesPanel({
  locale = "en",
}: SourcesPanelProps): React.JSX.Element {
  const sources = useApiFetch(() => getSources());
  const health = useApiFetch(() => getDataHealth());

  if (sources.status === "loading" || health.status === "loading") {
    return (
      <section aria-label="Sources" aria-busy="true">
        Loading…
      </section>
    );
  }
  if (sources.status === "error" || health.status === "error") {
    const error = sources.error ?? health.error;
    return (
      <section aria-label="Sources">
        {t("app.apiError", locale)}: {error?.message ?? "Request failed"}{" "}
        {error && "correlationId" in error && (
          <span>Correlation ID: {String(error.correlationId)} </span>
        )}
        <button type="button" onClick={sources.refetch}>
          {t("app.retry", locale)}
        </button>
      </section>
    );
  }
  const healthBySource = new Map(
    (health.data?.sources ?? []).map((source) => [source.source_id, source]),
  );
  return (
    <section aria-label="Sources" className="sources">
      <h2>{t("sources.title", locale)}</h2>
      <table>
        <thead>
          <tr>
            <th scope="col">{t("sources.source", locale)}</th>
            <th scope="col">{t("sources.lifecycle", locale)}</th>
            <th scope="col">{t("sources.health", locale)}</th>
            <th scope="col">{t("sources.lastSuccess", locale)}</th>
          </tr>
        </thead>
        <tbody>
          {(sources.data?.sources ?? []).map((source) => {
            const healthRow = healthBySource.get(source.source_id);
            return (
              <tr key={source.source_id}>
                <td>{source.source_id}</td>
                <td>{source.status}</td>
                <td>{healthRow?.health_status ?? source.health_status}</td>
                <td>
                  {healthRow?.last_success_at ?? source.last_success_at ?? "–"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <style jsx>{`
        .sources table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        .sources th,
        .sources td {
          text-align: left;
          padding: 4px;
          border-bottom: 1px solid #1a2132;
        }
      `}</style>
    </section>
  );
}
