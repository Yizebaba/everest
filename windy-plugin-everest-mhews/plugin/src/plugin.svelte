<div class="plugin__mobile-header">{title}</div>
<section class="plugin__content">
    <div class="plugin__title plugin__title--chevron-back" on:click={() => bcast.emit('rqstOpen', 'menu')}>{title}</div>

    <div class="intro">
        NASA GIBS daily satellite imagery for map context. This is imagery, not a hazard decision layer.
    </div>

    <label class="field-label" for="gibs-layer">IMAGERY PRODUCT</label>
    <select id="gibs-layer" bind:value={selectedLayerId} on:change={replaceLayer}>
        {#each layers as layer}<option value={layer.id}>{layer.label}</option>{/each}
    </select>

    <label class="field-label" for="gibs-date">OBSERVATION DATE</label>
    <input id="gibs-date" type="date" bind:value={selectedDate} max={today} on:change={replaceLayer} />

    <div class="control-row">
        <label class="field-label" for="gibs-opacity">OPACITY {Math.round(opacity * 100)}%</label>
        <input id="gibs-opacity" type="range" min="0" max="1" step="0.05" bind:value={opacity} on:input={updateOpacity} />
    </div>

    <div class="control-row action-row">
        <span class:ready={status === 'ready'} class="status"><i></i>{status.toUpperCase()}</span>
        <button on:click={toggleLayer}>{visible ? 'HIDE MAP' : 'SHOW MAP'}</button>
    </div>

    {#if errorMessage}<div class="error-message">{errorMessage}</div>{/if}

    <div class="details">
        <span>WMTS / EPSG:3857</span>
        <span>{selectedLayer.label}</span>
        <span>{selectedDate}</span>
    </div>

    <footer>
        Imagery provided by <a href="https://earthdata.nasa.gov/gibs" target="_blank">NASA EOSDIS GIBS</a>.
    </footer>
</section>

<script lang="ts">
    import bcast from '@windy/broadcast';
    import { layerOrder, map } from '@windy/map';
    import { onDestroy, onMount } from 'svelte';
    import config from './pluginConfig';

    type GIBSLayer = { id: string; label: string };

    const { title } = config;
    const layers: GIBSLayer[] = [
        { id: 'MODIS_Terra_CorrectedReflectance_TrueColor', label: 'MODIS Terra True Color' },
        { id: 'MODIS_Aqua_CorrectedReflectance_TrueColor', label: 'MODIS Aqua True Color' },
        { id: 'VIIRS_NOAA20_CorrectedReflectance_TrueColor', label: 'VIIRS NOAA-20 True Color' },
    ];
    const today = new Date().toISOString().slice(0, 10);
    const initialDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    let selectedLayerId = layers[0].id;
    let selectedDate = initialDate;
    let opacity = 0.75;
    let visible = true;
    let status: 'loading' | 'ready' | 'hidden' | 'error' = 'loading';
    let errorMessage = '';
    let imageryLayer: L.TileLayer | null = null;

    $: selectedLayer = layers.find(layer => layer.id === selectedLayerId) || layers[0];

    const tileUrl = () => `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${selectedLayer.id}/default/${selectedDate}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`;

    const removeLayer = () => {
        imageryLayer?.remove();
        imageryLayer = null;
    };

    const replaceLayer = () => {
        removeLayer();
        errorMessage = '';
        if (!visible) {
            status = 'hidden';
            return;
        }
        status = 'loading';
        imageryLayer = new L.TileLayer(tileUrl(), {
            minZoom: 0,
            maxNativeZoom: 9,
            maxZoom: 19,
            opacity: Number(opacity),
            tileSize: 256,
            layerBucketId: layerOrder.MAIN,
        });
        imageryLayer.on('load', () => { status = 'ready'; });
        imageryLayer.on('tileerror', () => {
            status = 'error';
            errorMessage = 'NASA GIBS imagery is unavailable for this product or date.';
        });
        imageryLayer.addTo(map);
    };

    const updateOpacity = () => { imageryLayer?.setOpacity(Number(opacity)); };
    const toggleLayer = () => {
        visible = !visible;
        replaceLayer();
    };

    export const onopen = () => { if (!imageryLayer && visible) replaceLayer(); };
    onMount(replaceLayer);
    onDestroy(removeLayer);
</script>

<style lang="less">
    .plugin__content { padding: 12px 14px 24px; color: #e8edf0; background: #11191e; min-height: 100%; }
    .intro { color: #a8babf; font-size: 12px; line-height: 1.5; margin: 12px 0 18px; }
    .field-label { display: block; color: #91a5aa; font-size: 10px; letter-spacing: 1px; margin: 15px 0 6px; }
    select, input[type='date'] { box-sizing: border-box; width: 100%; background: #172126; border: 1px solid #33464d; color: #e8edf0; padding: 8px; }
    input[type='range'] { width: 100%; accent-color: #52b6c7; }
    .control-row { margin-top: 16px; } .action-row { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #304047; padding-top: 14px; }
    button { background: #172126; border: 1px solid #33464d; color: #d7e1e3; padding: 8px 10px; font-size: 10px; cursor: pointer; }
    .status { color: #f2ad42; font-size: 10px; letter-spacing: 1px; } .status.ready { color: #51c7a3; } .status i { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: currentColor; margin-right: 5px; }
    .error-message { color: #f2ad42; font-size: 11px; border: 1px solid #7b5c2c; padding: 8px; margin-top: 14px; }
    .details { display: grid; gap: 4px; margin-top: 18px; color: #71858a; font-size: 10px; } footer { color: #869ba0; font-size: 10px; border-top: 1px solid #304047; margin-top: 18px; padding-top: 12px; } a { color: #52b6c7; }
</style>
