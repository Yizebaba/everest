import type { Locale } from "./locale";
import { CATALOGS, type LocaleCatalog } from "./messages";

export type { Locale } from "./locale";

type Section = keyof LocaleCatalog;
export type MessageKey = {
  [S in Section]: `${S & string}.${keyof LocaleCatalog[S] & string}`;
}[Section];

export function t(key: MessageKey, locale: Locale = "en"): string {
  const [section, item] = key.split(".") as [Section, string];
  const group = CATALOGS[locale][section] as Record<string, string>;
  const value = group[item];
  if (value === undefined) {
    throw new Error(`missing i18n key: ${key} (${locale})`);
  }
  return value;
}

export function catalogs(): typeof CATALOGS {
  return CATALOGS;
}

export function applyDocumentLocale(
  root: Pick<HTMLElement, "lang">,
  locale: Locale,
): void {
  root.lang = locale;
}
