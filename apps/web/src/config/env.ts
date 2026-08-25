export interface AppConfig {
  apiBaseUrl: string;
}

function requireHttpOrigin(value: string | undefined): string {
  if (!value) {
    throw new Error(
      "NEXT_PUBLIC_EVEREST_API_BASE_URL is required and must be an http(s) origin",
    );
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("API base URL must use http(s)");
  }
  return value.replace(/\/$/, "");
}

export function loadConfig(env: Record<string, string | undefined>): AppConfig {
  return {
    apiBaseUrl: requireHttpOrigin(env.NEXT_PUBLIC_EVEREST_API_BASE_URL),
  };
}

export const config: AppConfig = loadConfig(
  typeof process !== "undefined" ? process.env : {},
);
