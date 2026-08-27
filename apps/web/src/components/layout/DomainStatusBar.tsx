"use client";

import React, { useState } from "react";

import { getCommunication } from "@/domains/communication";
import { getDevices } from "@/domains/device";
import { getHazard } from "@/domains/hazard";
import { getMission } from "@/domains/mission";
import { getSensor } from "@/domains/sensor";
import { t, type Locale, type MessageKey } from "@/i18n/t";

export interface DomainStatusBarProps {
  locale: Locale;
  terrainStatus: "ok" | "empty";
  weatherStatus: "ok" | "empty";
  routeStatus: "ok" | "empty";
  routeNodeCount: number;
  riskStatus: "ok" | "empty";
  initialActive?: number | null;
}

export function nextActiveDomainIndex(
  previous: number | null,
  index: number,
): number | null {
  return previous === index ? null : index;
}

const DOMAIN_KEYS = [
  "domains.environment",
  "domains.terrain",
  "domains.weather",
  "domains.sensor",
  "domains.route",
  "domains.hazard",
  "domains.risk",
  "domains.communication",
  "domains.device",
  "domains.mission",
] as const;

type DomainStatus = "ok" | "empty" | "reserved";

export function DomainStatusBar({
  locale,
  terrainStatus,
  weatherStatus,
  routeStatus,
  routeNodeCount,
  riskStatus,
  initialActive = null,
}: DomainStatusBarProps): React.JSX.Element {
  const [active, setActive] = useState<number | null>(initialActive);
  const sensor = getSensor();
  const hazard = getHazard();
  const communication = getCommunication();
  const devices = getDevices();
  const mission = getMission();
  const separator = locale === "zh" ? "：" : ": ";

  const statusFor = (index: number): DomainStatus => {
    if (index === 0) return "ok";
    if (index === 1) return terrainStatus;
    if (index === 2) return weatherStatus;
    if (index === 4) return routeStatus;
    if (index === 6) return riskStatus;
    return "reserved";
  };

  const statusLabel = (status: DomainStatus): string => {
    const keys: Record<DomainStatus, MessageKey> = {
      ok: "domains.statusOk",
      empty: "domains.statusEmpty",
      reserved: "domains.statusReserved",
    };
    return t(keys[status], locale);
  };

  const countLabel = (count: number, key: MessageKey): string =>
    `${count} ${t(key, locale)}`;

  const missionAvailability = statusLabel(
    mission.availability === "available" ? "ok" : mission.availability,
  );

  const detail = (index: number): string => {
    if (index === 0) return statusLabel("ok");
    if (index === 1) return statusLabel(terrainStatus);
    if (index === 2) return statusLabel(weatherStatus);
    if (index === 3) return countLabel(sensor.readings.length, "domains.sensors");
    if (index === 4)
      return `${countLabel(routeNodeCount, "domains.routeNodes")} · ${statusLabel(routeStatus)}`;
    if (index === 5) return countLabel(hazard.points.length, "domains.hazards");
    if (index === 6) return statusLabel(riskStatus);
    if (index === 7)
      return countLabel(communication.links.length, "domains.links");
    if (index === 8) return countLabel(devices.items.length, "domains.devices");
    return t("domains.mission", locale);
  };

  return (
    <div className="domains" aria-label={t("domains.ariaLabel", locale)}>
      {DOMAIN_KEYS.map((key, index) => {
        const status = statusFor(index);
        const name = t(key, locale);
        const isActive = active === index;
        return (
          <button
            key={key}
            type="button"
            aria-pressed={isActive}
            aria-label={`${name}${separator}${statusLabel(status)}`}
            title={`${name}${separator}${detail(index)}`}
            className={`domains__item domains__item--${status}${isActive ? " domains__item--active" : ""}`}
            onClick={() =>
              setActive((previous) => nextActiveDomainIndex(previous, index))
            }
          >
            {name}
          </button>
        );
      })}
      <span className="domains__detail" aria-live="polite">
        {active === null
          ? [
              countLabel(sensor.readings.length, "domains.sensors"),
              countLabel(routeNodeCount, "domains.routeNodes"),
              countLabel(hazard.points.length, "domains.hazards"),
              countLabel(communication.links.length, "domains.links"),
              countLabel(devices.items.length, "domains.devices"),
              `${t("domains.mission", locale)} ${missionAvailability}`,
            ].join(" · ")
          : `${t(DOMAIN_KEYS[active] as MessageKey, locale)}${separator}${detail(active)}`}
      </span>
      <style jsx>{`
        .domains {
          display: flex;
          gap: 6px;
          align-items: center;
          flex-wrap: wrap;
          padding: 4px 0;
          font-size: 11px;
        }
        .domains__item {
          background: transparent;
          border: 1px solid transparent;
          border-radius: 999px;
          padding: 2px 8px;
          cursor: pointer;
          font-size: inherit;
          color: #9aa5b8;
          transition:
            border-color 120ms ease,
            background 120ms ease;
        }
        .domains__item:hover {
          border-color: #2c3a52;
          color: #c7d0e0;
        }
        .domains__item--ok {
          color: #2fbf71;
        }
        .domains__item--empty,
        .domains__item--reserved {
          color: #9aa5b8;
        }
        .domains__item--active {
          border-color: #38bdf8;
          background: rgba(56, 189, 248, 0.12);
          color: #38bdf8;
        }
        .domains__detail {
          color: #5c6678;
        }
      `}</style>
    </div>
  );
}
