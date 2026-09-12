# Everest Multi-Hazard Early Warning System

**[English](#english) | [中文](#中文) | [नेपाली](#नेपाली) | [Русский](#русский) | [Қазақша](#қазақша)**

<a id="english"></a>
## English

EVEREST-MHEWS is a high-altitude multi-hazard early warning system for the Everest region. It connects environmental observations, weather, satellite products, terrain and authorized exposure data into a life-safety decision chain.

`data intake -> quality -> features -> hazard -> propagation -> ETA -> risk -> decision -> CAP alert -> action`

### What This Repository Contains

- Weather ingestion and normalized forecast records for ECMWF, GFS, ICON, AIFS and GEFS workflows.
- Spatial and terrain foundations using PostGIS, natural geography, DEM and public baseline geometry.
- Satellite, telemetry, seismic, alert, detection, propagation and decision service foundations.
- A private Windy plugin that renders read-only MHEWS telemetry, CAP areas, public baseline geometry and persisted weather records.

### Operational Boundary

This repository is not an operational life-safety service by default. Missing, stale or unverified evidence is `UNKNOWN`, never safe. Current work does not claim completed multi-hazard classification, propagation/ETA, exposure fusion, five-level decisions or real CAP dissemination.

### Windy Plugin

Installation URL:

`https://windy-plugins.com/17744505/windy-plugin-everest-mhews/0.1.1/plugin.min.js`

The plugin needs a deployed HTTPS Everest API. Enter that URL in its panel. The API must explicitly allow `https://www.windy.com` through `EVEREST_CORS_ALLOWED_ORIGINS` and expose the documented read-only endpoints. Do not expose raw data paths, credentials or operational control endpoints to Windy.

### Repository Layout

| Path | Purpose |
| --- | --- |
| `apps/api/` | FastAPI service and API contracts |
| `services/` | Weather, telemetry, detection, risk, decision, alert and geospatial modules |
| `infra/docker/` | Local Docker composition and deployment material |
| `docs/` | Product, architecture, data source and operational documentation |
| `windy-plugin-everest-mhews/plugin/` | Published private Windy integration |

<a id="中文"></a>
## 中文

EVEREST-MHEWS 是面向珠峰区域的高海拔多灾种生命安全预警系统。系统将天气、卫星、地形、现场观测和已授权的暴露度数据接入统一风险与告警链路。

系统边界：数据缺失、过期或未经验证时必须显示 `UNKNOWN`，不能推断为安全。当前仓库不宣称已经完成多灾种识别、传播与 ETA、暴露度融合、五级决策或真实 CAP 多渠道发布。

Windy 插件仅显示项目 API 的只读数据。必须部署 HTTPS API，并在 `EVEREST_CORS_ALLOWED_ORIGINS` 中显式允许 `https://www.windy.com`。

<a id="नेपाली"></a>
## नेपाली

EVEREST-MHEWS एभरेस्ट क्षेत्रका लागि उच्च हिमाली बहु-विपद् जीवन-सुरक्षा पूर्वचेतावनी प्रणाली हो। यसले मौसम, उपग्रह, भू-भाग, स्थलगत अवलोकन र अधिकारप्राप्त जोखिम-सम्बन्धी डेटालाई एउटै निर्णय शृङ्खलामा जोड्छ।

डेटा हराएको, पुरानो वा प्रमाणीकरण नभएको अवस्थामा स्थिति `UNKNOWN` रहन्छ; त्यसलाई सुरक्षित मानिँदैन। Windy प्लगइनले HTTPS मा तैनाथ गरिएको Everest API बाट पढ्न-मात्र मिल्ने डेटा देखाउँछ।

<a id="русский"></a>
## Русский

EVEREST-MHEWS — система раннего предупреждения о множественных опасностях в высокогорье для района Эвереста. Она объединяет погоду, спутниковые данные, рельеф, полевые наблюдения и разрешенные данные об уязвимости в единую цепочку решений.

При отсутствии, устаревании или непроверенности данных статус остаётся `UNKNOWN`; это не означает безопасность. Плагин Windy отображает только данные чтения из развернутого HTTPS API Everest.

<a id="қазақша"></a>
## Қазақша

EVEREST-MHEWS — Эверест өңіріне арналған биік таулы аймақтағы көп қауіп-қатерді ерте ескерту жүйесі. Ол ауа райын, спутниктік деректерді, жер бедерін, далалық бақылауларды және рұқсат етілген осалдық деректерін бір шешім тізбегіне біріктіреді.

Дерек жоқ, ескірген немесе тексерілмеген жағдайда күй `UNKNOWN` болып қалады; бұл қауіпсіз дегенді білдірмейді. Windy плагині орналастырылған HTTPS Everest API-ден тек оқуға арналған деректерді көрсетеді.

## Documentation

- [API contract](docs/api/API.md)
- [Windy official plugin notes](docs/operations/WINDY_PLUGIN_OFFICIAL_DOCS.md)
