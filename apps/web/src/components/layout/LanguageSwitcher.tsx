"use client";

import { useEffect } from "react";

import { applyDocumentLocale, type Locale } from "@/i18n/t";

export interface LanguageSwitcherProps {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
}

export function LanguageSwitcher({
  locale,
  onLocaleChange,
}: LanguageSwitcherProps): React.JSX.Element {
  useEffect(() => {
    applyDocumentLocale(document.documentElement, locale);
  }, [locale]);

  return (
    <div className="language" role="group" aria-label="Language">
      <button
        type="button"
        aria-pressed={locale === "en"}
        onClick={() => onLocaleChange("en")}
      >
        EN
      </button>
      <button
        type="button"
        aria-pressed={locale === "zh"}
        onClick={() => onLocaleChange("zh")}
      >
        中文
      </button>
      <style jsx>{`
        .language {
          display: flex;
          gap: 4px;
        }
        .language button {
          font-size: 12px;
          background: #161d2e;
          border: 1px solid #232c40;
          color: #e6eaf2;
        }
        .language button[aria-pressed="true"] {
          border-color: #7fb4ff;
        }
      `}</style>
    </div>
  );
}
