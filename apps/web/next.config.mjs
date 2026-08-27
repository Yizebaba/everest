/** @type {import('next').NextConfig} */
// 'unsafe-eval' is required by Cesium (WebGL shader compilation). 'unsafe-inline'
// is required by Next.js dev-mode inline scripts; production builds use external
// scripts and should tighten this before shared deployment. img-src https:
// and connect-src https://tile.openstreetmap.org permit the OSM base layer
// (interactive viewport-only use per the OSMF Tile Usage Policy; Cesium loads
// imagery tiles over XHR, which connect-src governs). api.cesium.com and
// assets.cesium.com are permitted for Cesium ion assets (World Terrain / 3D
// Tiles) when NEXT_PUBLIC_CESIUM_ION_TOKEN is set in .env.local. ion streams
// terrain/tile payloads from assets.ion.cesium.com (CDN), which the API
// endpoint returns as the asset URL. Cesium World Imagery (ion Bing global
// imagery) resolves to dev.virtualearth.net and t*.ssl.ak.dynamic / ecn.t*.
// tiles.virtualearth.net, so those are permitted for the imagery base map.
// Bing tile endpoints are served over http (ecn.tN.tiles.virtualearth.net),
// so both schemes must be allowed for World Imagery to load.
const configuredApiUrl =
  process.env.NEXT_PUBLIC_EVEREST_API_BASE_URL ?? "http://localhost:52147";
let configuredApiOrigin;
try {
  const parsed = new URL(configuredApiUrl);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("API URL must use http or https");
  }
  configuredApiOrigin = parsed.origin;
} catch (error) {
  throw new Error(
    `NEXT_PUBLIC_EVEREST_API_BASE_URL must be an http(s) origin: ${error instanceof Error ? error.message : "invalid URL"}`,
  );
}

const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  `connect-src 'self' ${configuredApiOrigin} http://127.0.0.1:52147 http://localhost:52147 http://192.168.1.11:52147 https://tile.openstreetmap.org https://api.cesium.com https://assets.cesium.com https://assets.ion.cesium.com http://*.virtualearth.net https://*.virtualearth.net`,
  "img-src 'self' data: http: https:",
  "font-src 'self'",
  "worker-src 'self' blob:",
].join("; ");

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [{ key: "Content-Security-Policy", value: csp }],
      },
    ];
  },
};

export default nextConfig;
