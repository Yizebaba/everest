import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DomainStatusBar } from "./DomainStatusBar";

const renderStatusBar = (locale: "en" | "zh") =>
  renderToStaticMarkup(
    <DomainStatusBar
      locale={locale}
      terrainStatus="ok"
      weatherStatus="ok"
      routeStatus="ok"
      routeNodeCount={17}
      riskStatus="ok"
    />,
  );

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
});
