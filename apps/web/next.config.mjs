/** @type {import('next').NextConfig} */
// 'unsafe-eval' is required by Cesium (WebGL shader compilation). 'unsafe-inline'
// is required by Next.js dev-mode inline scripts; production builds use external
// scripts and should tighten this before shared deployment. img-src https:
// permits OSM raster tiles from tile.openstreetmap.org (interactive
// viewport-only use per the OSMF Tile Usage Policy).
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "connect-src 'self' http://localhost:50149 http://192.168.1.11:50149",
  "img-src 'self' data: https:",
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
