# HQMW Cryosphere Windy Plugin

## 目的

`HQMW Cryosphere` 是安装在 Windy 中的 NASA GIBS 卫星影像浏览插件。它用于查看珠峰区域及全球的公开影像、冰冻圈和陆地水圈背景图层。

它不是灾害预测系统，不生成 CAP，不发送通知，不会把任何影像直接判断为冰崩、雪崩、滑坡、洪水或 `RED` 警报。

## 安装

在 Windy Developer Mode 中加载当前发布版本：

```text
https://windy-plugins.com/17744505/windy-plugin-everest-mhews/1.7.0/plugin.min.js
```

Developer Mode：

```text
https://www.windy.com/developer-mode
```

插件显示名称：`HQMW Cryosphere`。

## 当前功能

### NASA GIBS 图层目录

- 加载 NASA GIBS EPSG:3857 WMTS capabilities。
- 搜索可用的 NASA GIBS JPEG/PNG 图层。
- 显示目录总数和当前搜索结果数。
- `TEST ALL` 使用实际低缩放 NASA 瓦片测试图层可加载性。
  - `💚`：测试瓦片可加载。
  - `🔴`：测试瓦片失败。
  - `⚪`：尚未测试。
- `更新图层`：重新读取 NASA 图层目录。
- `刷新影像`：重新请求当前图层、日期和透明度。

测试结果只说明一张 NASA 瓦片是否可加载，不说明产品对珠峰是否有有效观测，也不说明风险等级。

### 影像控制

- `IMAGERY PRODUCT`：选择 NASA 图层。
- `OBSERVATION DATE`：选择影像日期。切换科学图层时，插件自动使用 NASA capabilities 给出的默认可用日期。
- `OPACITY`：调整当前影像透明度。
- `SHOW MAP` / `HIDE MAP`：显示或移除当前 NASA 图层。
- `定位珠峰`：只将 Windy 地图定位到珠峰，用于地图浏览，不表示路线、安全区或人员位置。
- `图例 / 单位`：科学参数图层会显示 NASA 官方图例。真彩色和分类影像通常没有单一数值单位。

### 冰冻圈

插件提供中文快捷筛选：

- 冷冻/解冻
- 冰冻区域
- 冰雪表面温度
- RTC SAR 后向散射
- 积雪覆盖
- 积雪深度
- 积雪范围
- 雪指数
- 雪水当量

`RTC SAR 后向散射` 对应 GIBS 中的 OPERA RTC Sentinel-1 背景产品。积雪、冰温和被动微波产品的空间分辨率与时间延迟各不相同，只能作为背景观察。

### 陆地水圈与 Sentinel-2

- 洪水观测
- 洪水危险度（历史）
- 动态地表水范围
- 土壤湿度
- 水库
- `Sentinel-2 / HLS`：HLS Sentinel-2 MSI 校正反射率与 DSWx-HLS 动态地表水。

`水体参考`、`水体指数`、`湿度指数` 不是 GIBS 的现成图层。它们需要单独的 HLS、DSWx、NDWI/MNDWI 或授权水系数据处理流程。

### 海洋参考

海冰范围、海冰亮温、海表温度和海温异常单独放在海洋参考分类。这些是海洋产品，不能当作珠峰冰川信息。

## Everest Live Monitor

插件内的 `EVEREST LIVE MONITOR` 默认折叠，提供同一图层的两期日期切换：

- 当前影像日期
- 基线影像日期
- 查看当前
- 查看上期

当前状态固定为 `UNKNOWN`，因为插件没有已验证的影像变化指标。风、雨、CAP、自动风险等级、自动灾害识别和自动报警在这一简易比较功能中均已关闭。

未来的变化候选需要独立后端流程：选择经过质量检查的 Sentinel-1 RTC 或 Sentinel-2/HLS 影像对，进行配准、云/阴影/地形处理、变化计算和人工复核。只有经过验证的候选才可以进入 Everest 的风险与决策服务。

## 数据来源与归因

主要数据来源：NASA EOSDIS Global Imagery Browse Services (GIBS)。

```text
https://earthdata.nasa.gov/gibs
```

GIBS 是公开的 WMTS/WMS 可视化服务。其影像用于地图背景和人工观察。产品可用性、默认日期、最大缩放和图例以 NASA WMTS capabilities 为准。

```text
https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml
```

下载原始 HLS、Sentinel、OPERA 或其他科学数据时，可能需要 Earthdata Login、适用数据条款和额外处理。插件不保存 Earthdata 凭据。

## 更新与备份

Windy 发布使用版本化插件 URL。运行中的插件不能自行下载并覆盖自己的代码。

- 图层内容更新：使用插件内 `更新图层` 或 `刷新影像`。
- 插件代码更新：在 Windy Developer Mode 加载新的版本 URL。
- 当前代码备份标签：`hqmw-cryosphere-1.6.0`。

## 故障排查

| 现象 | 检查动作 |
| --- | --- |
| 图层目录数量很少 | 点击 `更新图层`，检查 NASA GIBS catalog 状态或错误信息。 |
| 科学图层不显示 | 重新选择该图层，让插件使用 NASA 默认日期；查看 `图例 / 单位` 与图层状态。 |
| 显示 `🔴` | 该图层测试瓦片不可用、日期无数据或浏览器网络请求失败；不要将其理解为灾害状态。 |
| 想看珠峰 | 点击 `定位珠峰`，再选择图层和日期。 |
| 想比较变化 | 展开 `EVEREST LIVE MONITOR`，选择当前和基线日期后交替查看。 |

## 系统边界

公开卫星影像、USGS 事件、火点和海洋产品都可以提供态势感知，但不能单独确认珠峰灾害或触发撤离。EVEREST-MHEWS 的即时高等级告警必须依赖授权、高频地面证据、质量控制、传播/ETA、暴露度和适当的决策流程。
