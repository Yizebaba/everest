<div class="plugin__mobile-header">{title}</div>
<section class="plugin__content">
    <div class="plugin__title plugin__title--chevron-back" on:click={() => bcast.emit('rqstOpen', 'menu')}>{title}</div>
    <p class="intro">NASA GIBS imagery for map context. Imagery is not a hazard decision layer.</p>

    <div class="catalog-status" class:ready={catalogStatus === 'ready'}>
        <i></i>{catalogStatus === 'ready' ? `${catalogLayers.length} NASA GIBS layers ready` : catalogStatus.toUpperCase()}
        <button on:click={loadCatalog}>RELOAD</button>
    </div>
    {#if catalogError}<div class="error-message">{catalogError}</div>{/if}

    <label class="field-label" for="gibs-search">SEARCH NASA GIBS</label>
    <input id="gibs-search" bind:value={query} placeholder="MODIS, VIIRS, snow, aerosol..." />
    <div class="quick-filters">
        <span>冰冻圈推荐</span>
        <button on:click={() => query = 'NDSI Snow Cover'}>冰雪覆盖</button>
        <button on:click={() => query = 'Ice Surface Temp'}>冰面温度</button>
        <button on:click={() => query = 'Snow Depth Over Glaciated Surface'}>冰川积雪深度</button>
        <button on:click={() => query = ''}>全部</button>
    </div>

    <label class="field-label" for="gibs-layer">IMAGERY PRODUCT · {catalogLayers.length}</label>
    <select id="gibs-layer" size="7" bind:value={selectedLayerId} on:change={replaceLayer}>
        {#each matchingLayers as layer}<option value={layer.id}>{layer.title} {layerHealth[layer.id] === 'available' ? '💚' : layerHealth[layer.id] === 'unavailable' ? '🔴' : '⚪'}</option>{/each}
    </select>
    <div class="catalog-actions"><small class="result-count">{matchingLayers.length} matching layers · {testCompleted}/{catalogLayers.length} tested</small><button on:click={testAllLayers} disabled={catalogStatus !== 'ready' || testStatus === 'running'}>{testStatus === 'running' ? 'TESTING...' : 'TEST ALL'}</button></div>

    <label class="field-label" for="gibs-date">OBSERVATION DATE</label>
    <input id="gibs-date" type="date" bind:value={selectedDate} max={today} disabled={!selectedLayer.timeEnabled} on:change={replaceLayer} />

    <div class="control-row">
        <label class="field-label" for="gibs-opacity">OPACITY {Math.round(opacity * 100)}%</label>
        <input id="gibs-opacity" type="range" min="0" max="1" step="0.05" bind:value={opacity} on:input={updateOpacity} />
    </div>

    <div class="control-row action-row">
        <span class:ready={tileStatus === 'ready'} class="tile-status"><i></i>{tileStatus.toUpperCase()}</span>
        <button on:click={toggleLayer}>{visible ? 'HIDE MAP' : 'SHOW MAP'}</button>
    </div>
    {#if tileError}<div class="error-message">{tileError}</div>{/if}

    <div class="details"><span>{selectedLayer.title}</span><span>{selectedLayer.tileMatrixSet}</span><span>{selectedDate}</span></div>
    <footer>Imagery provided by <a href="https://earthdata.nasa.gov/gibs" target="_blank">NASA EOSDIS GIBS</a>.</footer>
</section>

<script lang="ts">
    import bcast from '@windy/broadcast';
    import { layerOrder, map } from '@windy/map';
    import { onDestroy, onMount } from 'svelte';
    import config from './pluginConfig';

    type GIBSLayer = { id: string; title: string; template: string; tileMatrixSet: string; maxZoom: number; timeEnabled: boolean; defaultTime: string };

    const { title } = config;
    const capabilitiesUrl = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml';
    const today = new Date().toISOString().slice(0, 10);
    const initialDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const initialLayers: GIBSLayer[] = [
        { id: 'MODIS_Terra_CorrectedReflectance_TrueColor', title: 'MODIS Terra True Color', template: 'https://gibs-{s}.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{Time}/GoogleMapsCompatible_Level9/{TileMatrix}/{TileRow}/{TileCol}.jpg', tileMatrixSet: 'GoogleMapsCompatible_Level9', maxZoom: 9, timeEnabled: true, defaultTime: initialDate },
        { id: 'MODIS_Aqua_CorrectedReflectance_TrueColor', title: 'MODIS Aqua True Color', template: 'https://gibs-{s}.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Aqua_CorrectedReflectance_TrueColor/default/{Time}/GoogleMapsCompatible_Level9/{TileMatrix}/{TileRow}/{TileCol}.jpg', tileMatrixSet: 'GoogleMapsCompatible_Level9', maxZoom: 9, timeEnabled: true, defaultTime: initialDate },
        { id: 'VIIRS_NOAA20_CorrectedReflectance_TrueColor', title: 'VIIRS NOAA-20 True Color', template: 'https://gibs-{s}.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_NOAA20_CorrectedReflectance_TrueColor/default/{Time}/GoogleMapsCompatible_Level9/{TileMatrix}/{TileRow}/{TileCol}.jpg', tileMatrixSet: 'GoogleMapsCompatible_Level9', maxZoom: 9, timeEnabled: true, defaultTime: initialDate },
    ];

    let catalogLayers = initialLayers;
    let catalogStatus: 'loading' | 'ready' | 'error' = 'loading';
    let catalogError = '';
    let query = '';
    let selectedLayerId = initialLayers[0].id;
    let selectedDate = initialDate;
    let opacity = 0.75;
    let visible = true;
    let tileStatus: 'loading' | 'ready' | 'hidden' | 'error' = 'loading';
    let tileError = '';
    let imageryLayer: L.TileLayer | null = null;
    let catalogController: AbortController | null = null;
    let testController: AbortController | null = null;
    let layerHealth: Record<string, 'available' | 'unavailable'> = {};
    let testStatus: 'idle' | 'running' | 'done' = 'idle';
    let testCompleted = 0;

    $: selectedLayer = catalogLayers.find(layer => layer.id === selectedLayerId) || initialLayers[0];
    $: matchingLayers = catalogLayers.filter(layer => `${layer.title} ${layer.id}`.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 100);

    const directChildText = (element: Element, name: string) => Array.from(element.children).find(child => child.localName === name)?.textContent?.trim() || '';
    const buildTileUrl = (layer: GIBSLayer, time = selectedDate) => layer.template
        .replace('https://gibs.earthdata.nasa.gov/', 'https://gibs-{s}.earthdata.nasa.gov/')
        .replace(/\{Time\}/g, time)
        .replace(/\{TileMatrixSet\}/g, layer.tileMatrixSet)
        .replace(/\{TileMatrix\}/g, '{z}')
        .replace(/\{TileRow\}/g, '{y}')
        .replace(/\{TileCol\}/g, '{x}');

    const parseCapabilities = (xml: string): GIBSLayer[] => {
        const document = new DOMParser().parseFromString(xml, 'application/xml');
        if (document.getElementsByTagName('parsererror').length) throw new Error('NASA GIBS capabilities could not be parsed.');
        const parsed: GIBSLayer[] = [];
        for (const layerElement of Array.from(document.getElementsByTagNameNS('*', 'Layer'))) {
            const id = directChildText(layerElement, 'Identifier');
            const title = directChildText(layerElement, 'Title') || id;
            const formats = Array.from(layerElement.getElementsByTagNameNS('*', 'Format')).map(element => element.textContent?.trim());
            const extension = formats.includes('image/png') ? 'png' : formats.includes('image/jpeg') ? 'jpg' : '';
            const matrix = Array.from(layerElement.getElementsByTagNameNS('*', 'TileMatrixSet')).map(element => element.textContent?.trim()).find(value => value?.startsWith('GoogleMapsCompatible'));
            const timeDimension = Array.from(layerElement.getElementsByTagNameNS('*', 'Dimension')).find(element => directChildText(element, 'Identifier') === 'Time');
            const defaultTime = timeDimension ? directChildText(timeDimension, 'Default') : '';
            const resource = Array.from(layerElement.getElementsByTagNameNS('*', 'ResourceURL')).find(element => element.getAttribute('resourceType') === 'tile' && (element.getAttribute('format') === `image/${extension === 'jpg' ? 'jpeg' : extension}` || !element.getAttribute('format')))?.getAttribute('template');
            if (!id || !matrix || !resource || !extension) continue;
            const level = /Level(\d+)$/.exec(matrix);
            parsed.push({ id, title, template: resource, tileMatrixSet: matrix, maxZoom: level ? Number(level[1]) : 9, timeEnabled: resource.includes('{Time}'), defaultTime });
        }
        return parsed.sort((left, right) => left.title.localeCompare(right.title));
    };

    const removeLayer = () => { imageryLayer?.remove(); imageryLayer = null; };
    const replaceLayer = () => {
        removeLayer();
        tileError = '';
        if (!visible) { tileStatus = 'hidden'; return; }
        tileStatus = 'loading';
        imageryLayer = new L.TileLayer(buildTileUrl(selectedLayer), {
            minZoom: 0, maxNativeZoom: selectedLayer.maxZoom, maxZoom: 19,
            opacity: Number(opacity), tileSize: 256, layerBucketId: layerOrder.MAIN,
            subdomains: 'abc', noWrap: true, continuousWorld: true,
            bounds: [[-85.0511287776, -179.999999975], [85.0511287776, 179.999999975]],
        });
        imageryLayer.on('load', () => { tileStatus = 'ready'; });
        imageryLayer.on('tileerror', () => { tileStatus = 'error'; tileError = 'NASA GIBS imagery is unavailable for this product or date.'; });
        imageryLayer.addTo(map);
    };
    const updateOpacity = () => { imageryLayer?.setOpacity(Number(opacity)); };
    const toggleLayer = () => { visible = !visible; replaceLayer(); };

    const loadCatalog = async () => {
        catalogController?.abort();
        const controller = new AbortController();
        catalogController = controller;
        catalogStatus = 'loading'; catalogError = '';
        try {
            const response = await fetch(capabilitiesUrl, { signal: controller.signal });
            if (!response.ok) throw new Error(`NASA GIBS: ${response.status}`);
            const parsed = parseCapabilities(await response.text());
            if (catalogController !== controller || !parsed.length) return;
            catalogLayers = parsed;
            layerHealth = {};
            testCompleted = 0;
            testStatus = 'idle';
            if (!catalogLayers.some(layer => layer.id === selectedLayerId)) selectedLayerId = catalogLayers[0].id;
            catalogStatus = 'ready';
            replaceLayer();
        } catch (error) {
            if (catalogController !== controller || controller.signal.aborted) return;
            catalogStatus = 'error';
            catalogError = error instanceof Error ? error.message : 'NASA GIBS catalog is unavailable.';
        } finally {
            if (catalogController === controller) catalogController = null;
        }
    };

    const testLayer = (layer: GIBSLayer, signal: AbortSignal) => new Promise<boolean>(resolve => {
        const image = new Image();
        const timeout = setTimeout(() => { image.src = ''; resolve(false); }, 10000);
        const finish = (result: boolean) => { clearTimeout(timeout); resolve(result); };
        signal.addEventListener('abort', () => finish(false), { once: true });
        image.onload = () => finish(true);
        image.onerror = () => finish(false);
        const zoom = Math.min(1, layer.maxZoom);
        image.src = buildTileUrl(layer, layer.defaultTime || selectedDate).replace('{z}', String(zoom)).replace('{y}', '0').replace('{x}', '0').replace('{s}', 'a');
    });

    const testAllLayers = async () => {
        testController?.abort();
        const controller = new AbortController();
        testController = controller;
        layerHealth = {}; testCompleted = 0; testStatus = 'running';
        let next = 0;
        const worker = async () => {
            while (!controller.signal.aborted) {
                const layer = catalogLayers[next++];
                if (!layer) return;
                const result = await testLayer(layer, controller.signal);
                if (controller.signal.aborted) return;
                layerHealth = { ...layerHealth, [layer.id]: result ? 'available' : 'unavailable' };
                testCompleted += 1;
            }
        };
        await Promise.all(Array.from({ length: 4 }, worker));
        if (testController === controller) { testController = null; testStatus = 'done'; }
    };

    export const onopen = () => { if (!imageryLayer && visible) replaceLayer(); };
    onMount(() => { replaceLayer(); loadCatalog(); });
    onDestroy(() => { catalogController?.abort(); testController?.abort(); removeLayer(); });
</script>

<style lang="less">
    .plugin__content { padding: 12px 14px 24px; color: #e8edf0; background: #11191e; min-height: 100%; } .intro { color: #a8babf; font-size: 12px; line-height: 1.5; margin: 12px 0 18px; }
    .field-label { display: block; color: #91a5aa; font-size: 10px; letter-spacing: 1px; margin: 15px 0 6px; } input, select { box-sizing: border-box; width: 100%; background: #172126; border: 1px solid #33464d; color: #e8edf0; padding: 8px; } input[type='range'] { accent-color: #52b6c7; padding: 0; } select { font-size: 11px; } .quick-filters { display:flex; flex-wrap:wrap; align-items:center; gap:5px; margin-top:8px; color:#91a5aa; font-size:10px; } .quick-filters button { padding:5px 6px; } .catalog-actions { display:flex; align-items:center; justify-content:space-between; margin-top:6px; } .result-count { color: #71858a; font-size: 10px; } button:disabled { cursor: wait; opacity: 0.55; }
    .catalog-status, .tile-status { color: #f2ad42; font-size: 10px; letter-spacing: 1px; } .catalog-status { display: flex; align-items: center; justify-content: space-between; border: 1px solid #33464d; padding: 7px; } .catalog-status.ready, .tile-status.ready { color: #51c7a3; } .catalog-status i, .tile-status i { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: currentColor; margin-right: 5px; } button { background: #172126; border: 1px solid #33464d; color: #d7e1e3; padding: 7px 9px; font-size: 10px; cursor: pointer; }
    .control-row { margin-top: 16px; } .action-row { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #304047; padding-top: 14px; } .error-message { color: #f2ad42; font-size: 11px; border: 1px solid #7b5c2c; padding: 8px; margin-top: 10px; overflow-wrap: anywhere; } .details { display: grid; gap: 4px; margin-top: 18px; color: #71858a; font-size: 10px; } footer { color: #869ba0; font-size: 10px; border-top: 1px solid #304047; margin-top: 18px; padding-top: 12px; } a { color: #52b6c7; }
</style>
