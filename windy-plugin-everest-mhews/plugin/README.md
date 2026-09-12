# Everest MHEWS Windy plugin

Standalone Windy plugin for the Everest multi-hazard monitoring view.

## Included

- Read-only telemetry markers from `/api/telemetry/geojson`.
- Validated CAP areas from `/api/alerts/geojson` and alert headlines from `/api/alerts`.
- Public baseline geometry from `/api/osm/public-baseline/geojson`, shown only as map geometry.
- Persisted weather pressure records from `/api/weather/forecast`.
- `UNKNOWN` when the API or evidence is unavailable; this UI never derives a decision level.

## Development

```sh
npm install
npm run build
```

For local Windy developer mode, run `npm start` and load `https://localhost:9999/plugin.js`.

The panel intentionally has no default API URL. Enter the HTTPS URL of the deployed
Everest API. The API must allow `https://www.windy.com` in its explicit CORS allow-list.
The plugin remembers this URL in browser local storage. The endpoints are read-only and
the plugin does not send credentials or ingest telemetry.
