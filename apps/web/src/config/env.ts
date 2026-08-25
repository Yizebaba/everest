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

// Direct member access on process.env.NEXT_PUBLIC_* is required so webpack
// DefinePlugin inlines the value into the client bundle.
export const config: AppConfig = {
  apiBaseUrl: requireHttpOrigin(process.env.NEXT_PUBLIC_EVEREST_API_BASE_URL),
};
