import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  DomainStatusBar,
  nextActiveDomainIndex,
} from "./DomainStatusBar";

const renderStatusBar = (
  locale: "en" | "zh",
  initialActive?: number | null,
) =>
  renderToStaticMarkup(
    <DomainStatusBar
      locale={locale}
      terrainStatus="ok"
      weatherStatus="ok"
      routeStatus="ok"
      routeNodeCount={17}
      riskStatus="ok"
      initialActive={initialActive}
    />,
  );

describe("nextActiveDomainIndex", () => {
  it("selects a chip and deselects the same chip", () => {
    expect(nextActiveDomainIndex(null, 4)).toBe(4);
    expect(nextActiveDomainIndex(4, 4)).toBeNull();
    expect(nextActiveDomainIndex(4, 2)).toBe(2);
  });
});

describe("DomainStatusBar", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
      const message = args[0];
      if (
        typeof message !== "string" ||
        !message.includes("non-boolean attribute") ||
        !args.includes("jsx")
      ) {
        throw new Error(`unexpected console error: ${String(message)}`);
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uses the live route node count and translated English detail labels", () => {
    const html = renderStatusBar("en");

    expect(html).toContain('aria-label="Everest OS domains"');
    expect(html).toContain("17 route nodes");
    expect(html).toContain("Mission reserved");
    expect(html).toContain('aria-label="Sensor: reserved"');
  });

  it("translates its aria, count, detail, and reserved labels into Chinese", () => {
    const html = renderStatusBar("zh");

    expect(html).toContain('aria-label="珠峰 OS 领域状态"');
    expect(html).toContain("17 个路线节点");
    expect(html).toContain("任务 预留");
    expect(html).toContain('aria-label="传感器：预留"');
    expect(html).not.toContain("route nodes");
    expect(html).not.toContain("mission reserved");
  });

  it("renders chips as unpressed buttons with a live detail pane", () => {
    const html = renderStatusBar("en");

    expect(html).toContain('type="button"');
    expect(html).toContain('aria-pressed="false"');
    expect(html).not.toContain('aria-pressed="true"');
    expect(html).toContain('aria-live="polite"');
    expect(html).toContain('title="Route: 17 route nodes · available"');
    expect(html).toContain('title="Sensor: 0 sensors"');
    expect(html).toContain('title="Weather: available"');
    expect(html).toContain('title="Mission: Mission"');
  });

  it("shows the selected chip detail when a domain is active", () => {
    const html = renderStatusBar("en", 4);

    expect(html).toContain('aria-pressed="true"');
    expect(html).toContain("Route: 17 route nodes · available");
    expect(html).not.toContain("Mission reserved");
  });

  it("translates selected-chip titles and the active detail pane into Chinese", () => {
    const html = renderStatusBar("zh", 2);

    expect(html).toContain('title="路线：17 个路线节点 · 可用"');
    expect(html).toContain('title="传感器：0 个传感器"');
    expect(html).toContain('title="气象：可用"');
    expect(html).toContain("气象：可用");
    expect(html).not.toContain("任务 预留");
  });
});
