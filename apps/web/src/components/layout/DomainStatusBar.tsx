"use client";

import React from "react";

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

export function DomainStatusBar({
  locale,
  terrainStatus,
  weatherStatus,
  routeStatus,
  routeNodeCount,
  riskStatus,
}: DomainStatusBarProps): React.JSX.Element {
  const sensor = getSensor();
  const hazard = getHazard();
  const communication = getCommunication();
  const devices = getDevices();
  const mission = getMission();

  const statusFor = (index: number): "ok" | "empty" | "reserved" => {
    if (index === 0) return "ok";
    if (index === 1) return terrainStatus;
    if (index === 2) return weatherStatus;
    if (index === 4) return routeStatus;
    if (index === 6) return riskStatus;
    return "reserved";
  };

  const statusLabel = (status: "ok" | "empty" | "reserved"): string => {
    const keys: Record<typeof status, MessageKey> = {
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

  return (
    <div className="domains" aria-label={t("domains.ariaLabel", locale)}>
      {DOMAIN_KEYS.map((key, index) => {
        const status = statusFor(index);
        const name = t(key, locale);
        const separator = locale === "zh" ? "：" : ": ";
        return (
          <span
            key={key}
            className={`domains__item domains__item--${status}`}
            aria-label={`${name}${separator}${statusLabel(status)}`}
          >
            {name}
          </span>
        );
      })}
      <span className="domains__detail">
        {countLabel(sensor.readings.length, "domains.sensors")} ·{" "}
        {countLabel(routeNodeCount, "domains.routeNodes")} ·{" "}
        {countLabel(hazard.points.length, "domains.hazards")} ·{" "}
        {countLabel(communication.links.length, "domains.links")} ·{" "}
        {countLabel(devices.items.length, "domains.devices")} ·{" "}
        {t("domains.mission", locale)} {missionAvailability}
      </span>
      <style jsx>{`
        .domains {
          display: flex;
          gap: 8px;
          align-items: center;
          flex-wrap: wrap;
          padding: 4px 0;
          font-size: 11px;
          color: #9aa5b8;
        }
        .domains__item--ok {
          color: #2fbf71;
        }
        .domains__item--empty,
        .domains__item--reserved {
          color: #9aa5b8;
        }
        .domains__detail {
          color: #5c6678;
        }
      `}</style>
    </div>
  );
}
