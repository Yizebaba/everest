<div class="plugin__mobile-header">{title}</div>
<section class="plugin__content">
    <header class="topbar">
        <div>
            <button class="back" aria-label="Back to menu" on:click={() => bcast.emit('rqstOpen', 'menu')}>‹</button>
            <span class="eyebrow">EVEREST MHEWS</span>
            <h1>{title}</h1>
        </div>
        <div class:connected={apiState === 'available'} class="status"><span class="status-dot"></span> {apiState.toUpperCase()}</div>
    </header>

    <form class="connection" on:submit|preventDefault={refresh}>
        <label for="api-base">MHEWS API</label>
        <input id="api-base" bind:value={apiBase} on:change={persistApiBase} aria-label="MHEWS API base URL" placeholder="https://your-everest-api.example" />
        <button type="submit">REFRESH</button>
    </form>
    {#if errorMessage}<div class="api-error">{errorMessage}</div>{/if}

    <div class="summary-grid">
        <div class="metric"><span>DECISION</span><strong class="unknown">{decision}</strong><small>Windy is display-only</small></div>
        <div class="metric"><span>CAP MESSAGES</span><strong>{alertCount}</strong><small>validated active areas</small></div>
        <div class="metric"><span>TELEMETRY</span><strong>{sensors.length}</strong><small>{sensors.length ? 'positioned observations' : 'no usable positions'}</small></div>
    </div>

    <div class="external-layer">
        <div class="section-heading"><span>USGS EARTHQUAKES</span><span class="muted">PAST HOUR</span></div>
        <div class="external-layer__row">
            <span>{earthquakeStatus === 'available' ? `${earthquakeFeatures.length} events` : earthquakeStatus}</span>
            <button on:click={toggleEarthquakes}>{showEarthquakes ? 'HIDE MAP' : 'SHOW MAP'}</button>
        </div>
        <small>U.S. Geological Survey · background awareness only</small>
    </div>

    <div class="section-heading"><span>LIVE EVIDENCE</span><span class="muted">read-only adapter</span></div>
    {#if sensors.length}
        <div class="sensor-list">
            {#each sensors as sensor}
                <div class="sensor">
                    <span class="sensor-signal" class:warning={sensor.quality !== 'clean'}></span>
                    <span class="sensor-copy"><b>{sensor.device}</b><small>{sensor.quantity} · {sensor.observedAt}</small></span>
                    <span class="sensor-value">{sensor.value}<small>{sensor.unit}</small></span>
                </div>
            {/each}
        </div>
    {:else}
        <div class="empty">No positioned telemetry is available from the configured API.</div>
    {/if}

    <div class="section-heading"><span>CAP AREAS</span><span class="muted">source polygons only</span></div>
    {#if alertCount}
        <div class="alert-list">
            {#each alertHeadlines as headline}<div class="alert"><span class="alert-dot"></span>{headline}</div>{/each}
        </div>
    {:else}
        <div class="empty">No active CAP area returned.</div>
    {/if}

    <div class="chart-panel">
        <div class="section-heading"><span>WEATHER RECORDS</span><span class="muted">persisted project data</span></div>
        {#if chartStatus === 'loading'}
            <div class="chart-message">Loading project forecast records…</div>
        {:else if chartStatus === 'error'}
            <div class="chart-message">Forecast records unavailable.</div>
        {:else if chartValues.length > 1}
            <svg class="chart" viewBox="0 0 360 118" role="img" aria-label="Project weather record trend">
                <line x1="8" y1="92" x2="352" y2="92" class="gridline" /><line x1="8" y1="58" x2="352" y2="58" class="gridline" /><line x1="8" y1="24" x2="352" y2="24" class="gridline" />
                <polyline points={chartPoints} class="trend" /><text x="8" y="112">EARLIEST</text><text x="308" y="112">LATEST</text>
            </svg>
        {:else}
            <div class="chart-message">No numeric weather records available.</div>
        {/if}
    </div>

    <footer class="legend"><span><i class="legend-dot red"></i> CAP area</span><span><i class="legend-dot cyan"></i> public geometry</span><span><i class="legend-dot amber"></i> telemetry</span></footer>
</section>

<script lang="ts">
    import bcast from '@windy/broadcast';
    import { map } from '@windy/map';
    import { onDestroy, onMount } from 'svelte';
    import config from './pluginConfig';

    type Sensor = { device: string; quantity: string; value: string; unit: string; observedAt: string; quality: string; position: [number, number] };
    type ApiState = 'loading' | 'available' | 'unavailable';

    const { title } = config;
    const apiBaseStorageKey = 'everest-mhews-api-base';
    let apiBase = '';
    let apiState: ApiState = 'loading';
    let decision = 'UNKNOWN';
    let sensors: Sensor[] = [];
    let alertCount = 0;
    let alertHeadlines: string[] = [];
    let chartStatus: 'loading' | 'ready' | 'error' = 'loading';
    let chartValues: number[] = [];
    let chartPoints = '';
    let errorMessage = '';
    let layers: L.Layer[] = [];
    let earthquakeLayers: L.Layer[] = [];
    let earthquakeFeatures: any[] = [];
    let earthquakeStatus: 'loading' | 'available' | 'unavailable' = 'loading';
    let showEarthquakes = true;
    let refreshController: AbortController | null = null;
    let mapController: AbortController | null = null;
    let earthquakeController: AbortController | null = null;
    let earthquakeTimer: ReturnType<typeof setInterval> | null = null;
    let refreshEpoch = 0;

    const endpoint = (path: string) => `${apiBase.replace(/\/$/, '')}${path}`;
    const usgsAllHourUrl = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson';
    const isTestTelemetry = (properties: Record<string, unknown>) => {
        const deviceId = String(properties.device_id || '');
        const sourceReference = String(properties.source_reference || '');
        return /^test-/i.test(deviceId) || /test/i.test(sourceReference);
    };
    const persistApiBase = () => {
        const value = apiBase.trim();
        try {
            if (value) localStorage.setItem(apiBaseStorageKey, value);
            else localStorage.removeItem(apiBaseStorageKey);
        } catch {
            // Storage is optional; the current session remains usable when it is blocked.
        }
    };
    const readJson = async (path: string, signal: AbortSignal) => {
        const response = await fetch(endpoint(path), { signal });
        if (!response.ok) throw new Error(`${path}: ${response.status}`);
        return response.json();
    };

    const refresh = async () => {
        refreshController?.abort();
        mapController?.abort();
        const controller = new AbortController();
        refreshController = controller;
        const epoch = ++refreshEpoch;
        const timeout = setTimeout(() => controller.abort(), 15000);
        apiState = 'loading'; chartStatus = 'loading'; errorMessage = '';
        if (!apiBase.trim()) {
            sensors = []; alertCount = 0; alertHeadlines = []; decision = 'UNKNOWN';
            removeLayers(); chartStatus = 'error'; apiState = 'unavailable';
            errorMessage = 'Enter an HTTPS MHEWS API URL.';
            clearTimeout(timeout);
            if (refreshController === controller) refreshController = null;
            return;
        }
        try {
            const [telemetry, alerts, alertGeoJson, weather] = await Promise.all([
                readJson('/api/telemetry/geojson', controller.signal),
                readJson('/api/alerts', controller.signal),
                readJson('/api/alerts/geojson', controller.signal),
                readJson('/api/weather/forecast', controller.signal),
            ]);
            if (epoch !== refreshEpoch) return;
            sensors = (telemetry.features || []).filter((feature: any) => !isTestTelemetry(feature.properties || {})).map((feature: any) => {
                const p = feature.properties || {}; const c = feature.geometry?.coordinates;
                return { device: p.device_id || 'unknown device', quantity: p.quantity || 'unknown quantity', value: p.value == null ? 'UNKNOWN' : String(p.value), unit: p.unit || '', observedAt: p.observed_at || 'unknown time', quality: p.quality_flags ? 'flagged' : 'clean', position: [c[1], c[0]] };
            }).filter((sensor: Sensor) => Number.isFinite(sensor.position[0]) && Number.isFinite(sensor.position[1]));
            const actualAlerts = (alerts.alerts || []).filter((alert: any) => alert.status === 'Actual');
            alertCount = actualAlerts.length;
            alertHeadlines = actualAlerts.flatMap((alert: any) => (alert.info || []).map((item: any) => item.headline || item.event || alert.identifier)).slice(0, 4);
            const actualAlertIds = new Set(actualAlerts.map((alert: any) => alert.identifier));
            const actualAlertGeoJson = { ...alertGeoJson, features: (alertGeoJson.features || []).filter((feature: any) => actualAlertIds.has(feature.id)) };
            const records = weather.records || [];
            chartValues = records.map((record: any) => Number(record.pressure)).filter(Number.isFinite).slice(-8);
            updateChart(); chartStatus = 'ready'; apiState = 'available';
            drawLayers(actualAlertGeoJson, { type: 'FeatureCollection', features: [] });
            void loadPublicGeometry(actualAlertGeoJson, epoch);
        } catch (error) {
            if (epoch !== refreshEpoch) return;
            sensors = []; alertCount = 0; alertHeadlines = []; decision = 'UNKNOWN';
            removeLayers(); chartStatus = 'error'; apiState = 'unavailable';
            errorMessage = controller.signal.aborted ? 'MHEWS API request timed out after 15 seconds.' : error instanceof Error ? error.message : 'MHEWS API request failed.';
        } finally {
            clearTimeout(timeout);
            if (refreshController === controller) refreshController = null;
        }
    };

    const loadPublicGeometry = async (alertGeoJson: any, epoch: number) => {
        const controller = new AbortController();
        mapController = controller;
        try {
            const publicGeoJson = await readJson('/api/osm/public-baseline/geojson', controller.signal);
            if (epoch === refreshEpoch) drawLayers(alertGeoJson, publicGeoJson);
        } catch (error) {
            if (!controller.signal.aborted) console.warn('MHEWS public geometry unavailable', error);
        } finally {
            if (mapController === controller) mapController = null;
        }
    };

    const updateChart = () => {
        if (chartValues.length < 2) { chartPoints = ''; return; }
        const min = Math.min(...chartValues); const max = Math.max(...chartValues); const span = max - min || 1;
        chartPoints = chartValues.map((value, index) => `${8 + index * (344 / (chartValues.length - 1))},${92 - ((value - min) / span) * 70}`).join(' ');
    };

    const clearEarthquakes = () => {
        earthquakeLayers.forEach(layer => map.removeLayer(layer));
        earthquakeLayers = [];
    };
    const drawEarthquakes = () => {
        clearEarthquakes();
        if (!showEarthquakes) return;
        earthquakeFeatures.forEach(feature => {
            const coordinates = feature.geometry?.coordinates;
            if (!Array.isArray(coordinates) || coordinates.length < 2) return;
            const [lon, lat, depth] = coordinates;
            const magnitude = Number(feature.properties?.mag);
            if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(magnitude)) return;
            const marker = new L.CircleMarker([lat, lon], {
                radius: Math.max(4, Math.min(12, 3 + magnitude * 2)),
                color: magnitude >= 5 ? '#e56b55' : magnitude >= 3 ? '#f2ad42' : '#52b6c7',
                fillOpacity: 0.8,
                weight: 1,
            });
            marker.bindTooltip(`M ${magnitude.toFixed(1)} · ${feature.properties?.place || 'USGS event'} · ${depth ?? '?'} km`);
            marker.addTo(map);
            earthquakeLayers.push(marker);
        });
    };
    const loadEarthquakes = async () => {
        earthquakeController?.abort();
        const controller = new AbortController();
        earthquakeController = controller;
        earthquakeStatus = 'loading';
        try {
            const response = await fetch(usgsAllHourUrl, { signal: controller.signal });
            if (!response.ok) throw new Error(`USGS: ${response.status}`);
            const payload = await response.json();
            if (earthquakeController !== controller) return;
            earthquakeFeatures = Array.isArray(payload.features) ? payload.features : [];
            earthquakeStatus = 'available';
            drawEarthquakes();
        } catch {
            if (earthquakeController === controller && !controller.signal.aborted) earthquakeStatus = 'unavailable';
        } finally {
            if (earthquakeController === controller) earthquakeController = null;
        }
    };
    const toggleEarthquakes = () => {
        showEarthquakes = !showEarthquakes;
        drawEarthquakes();
    };

    const removeLayers = () => { layers.forEach(layer => map.removeLayer(layer)); layers = []; };
    const drawLayers = (alertsGeoJson: any, publicGeoJson: any) => {
        removeLayers();
        if (alertsGeoJson?.features?.length) {
            const alertsLayer = new L.GeoJSON(alertsGeoJson, { style: { color: '#e56b55', weight: 2, fillColor: '#e56b55', fillOpacity: 0.18 } });
            alertsLayer.addTo(map); layers.push(alertsLayer);
        }
        if (publicGeoJson?.features?.length) {
            const publicLayer = new L.GeoJSON(publicGeoJson, { style: { color: '#52b6c7', weight: 2, opacity: 0.7 } });
            publicLayer.addTo(map); layers.push(publicLayer);
        }
        sensors.forEach(sensor => { const marker = new L.CircleMarker(sensor.position, { radius: 6, color: '#f2ad42', fillColor: '#f2ad42', fillOpacity: 1 }); marker.bindTooltip(sensor.device); marker.addTo(map); layers.push(marker); });
    };

    export const onopen = () => { refresh(); };
    onMount(() => {
        try { apiBase = localStorage.getItem(apiBaseStorageKey) || ''; }
        catch { apiBase = ''; }
        loadEarthquakes();
        earthquakeTimer = setInterval(loadEarthquakes, 60000);
    });
    onDestroy(() => {
        refreshController?.abort();
        mapController?.abort();
        earthquakeController?.abort();
        if (earthquakeTimer) clearInterval(earthquakeTimer);
        clearEarthquakes();
        removeLayers();
    });
</script>

<style lang="less">
    .plugin__content { padding:14px 14px 24px; color:#e8edf0; background:#11191e; min-height:100%; }
    .topbar { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid #304047; padding-bottom:14px; }
    .back { border:0; background:none; color:#9fb2b7; font-size:28px; padding:0 8px 0 0; vertical-align:middle; cursor:pointer; } h1 { display:inline; font-size:17px; letter-spacing:1px; font-weight:600; } .eyebrow,.section-heading,.metric span { font-size:10px; letter-spacing:1.2px; color:#91a5aa; } .eyebrow { margin-right:8px; }
    .status { font-size:10px; color:#e56b55; padding-top:5px; white-space:nowrap; } .status.connected { color:#51c7a3; } .status-dot,.sensor-signal,.alert-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#e56b55; margin-right:5px; } .connected .status-dot { background:#51c7a3; } .sensor-signal { background:#51c7a3; } .sensor-signal.warning { background:#f2ad42; }
    .connection { display:flex; align-items:center; gap:6px; margin:12px 0; } .connection label { color:#91a5aa; font-size:10px; } input { min-width:0; flex:1; background:#172126; border:1px solid #33464d; color:#cbd6d8; padding:7px; font-size:10px; } .connection button,.filter { background:#f2ad42; border:1px solid #f2ad42; color:#151b1d; padding:7px 9px; font-size:10px; cursor:pointer; }
    .summary-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#304047; margin:14px 0 20px; } .metric { background:#172126; padding:11px 8px; } .metric strong { display:block; font-size:18px; margin:8px 0 3px; } .metric small,.sensor small { color:#869ba0; font-size:10px; } .unknown { color:#e56b55; }
    .external-layer { border-top:1px solid #304047; border-bottom:1px solid #304047; padding:1px 0 11px; } .external-layer__row { display:flex; align-items:center; justify-content:space-between; font-size:12px; color:#d7e1e3; } .external-layer__row button { background:#172126; border:1px solid #33464d; color:#b4c2c5; padding:6px 8px; font-size:10px; cursor:pointer; } .external-layer small { display:block; color:#869ba0; font-size:10px; margin-top:6px; }
    .section-heading { display:flex; justify-content:space-between; margin:16px 0 8px; } .muted { color:#657a80; } .sensor-list,.alert-list { display:grid; gap:5px; } .sensor,.alert { display:flex; align-items:center; background:#172126; border:1px solid #263940; padding:9px; } .sensor-copy { flex:1; } .sensor-copy b { display:block; font-size:12px; font-weight:500; margin-bottom:3px; } .sensor-value { font-size:15px; color:#f2ad42; text-align:right; } .sensor-value small { display:block; } .alert { color:#d7e1e3; font-size:11px; } .alert-dot { background:#e56b55; }
    .api-error { color:#f2ad42; font-size:10px; border:1px solid #7b5c2c; padding:7px; margin:-4px 0 8px; overflow-wrap:anywhere; } .empty,.chart-message { color:#91a5aa; font-size:11px; padding:12px 4px; border:1px dashed #33464d; } .chart-panel { border-top:1px solid #304047; margin-top:20px; padding-top:1px; } .chart { width:100%; height:130px; overflow:visible; } .gridline { stroke:#2e4147; stroke-width:1; } .trend { fill:none; stroke:#52b6c7; stroke-width:2.5; } text { fill:#71858a; font-size:8px; }
    .legend { display:flex; gap:12px; color:#8fa3a8; font-size:10px; border-top:1px solid #304047; padding-top:12px; } .legend-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:4px; } .red { background:#e56b55; } .cyan { background:#52b6c7; } .amber { background:#f2ad42; }
</style>
