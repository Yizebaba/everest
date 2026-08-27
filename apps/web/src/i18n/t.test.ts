import { describe, expect, it } from "vitest";

import { applyDocumentLocale, t } from "./t";

describe("i18n", () => {
  it("provides translated touched Phase 1 labels", () => {
    expect(t("panels.currentWeather", "zh")).toBe("当前天气");
    expect(t("scene.satellite", "zh")).toBe("卫星");
  });

  it("applies the active locale to the document root", () => {
    const root = { lang: "en" };
    applyDocumentLocale(root, "zh");
    expect(root.lang).toBe("zh");
  });
});
