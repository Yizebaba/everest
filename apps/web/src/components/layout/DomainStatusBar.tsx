"use client";

import { getCommunication } from "@/domains/communication";
import { getDevices } from "@/domains/device";
import { getHazard } from "@/domains/hazard";
import { getMission } from "@/domains/mission";
import { getRoute } from "@/domains/route";
import { getSensor } from "@/domains/sensor";
import { t, type Locale } from "@/i18n/t";

export interface DomainStatusBarProps {
  locale: Locale;
  terrainStatus: "ok" | "empty";
  weatherStatus: "ok" | "empty";
  routeStatus: "ok" | "empty";
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
  riskStatus,
}: DomainStatusBarProps): React.JSX.Element {
  const sensor = getSensor();
  const route = getRoute();
  const hazard = getHazard();
  const communication = getCommunication();
  const devices = getDevices();
  const mission = getMission();

  const statusFor = (index: number): string => {
    if (index === 0) return "ok";
    if (index === 1) return terrainStatus;
    if (index === 2) return weatherStatus;
    if (index === 4) return routeStatus;
    if (index === 6) return riskStatus;
    return "reserved";
  };

  return (
    <div className="domains" aria-label="Everest OS domains">
      {DOMAIN_KEYS.map((key, index) => (
        <span
          key={key}
          className={`domains__item domains__item--${statusFor(index)}`}
        >
          {t(key, locale)}
        </span>
      ))}
      <span className="domains__detail">
        {sensor.readings.length} sensors · {route.nodes.length} route nodes ·{" "}
        {hazard.points.length} hazards · {communication.links.length} links ·{" "}
        {devices.items.length} devices · mission {mission.availability}
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
