# Windy 官方会员与插件能力调查

调查日期：2026-09-12

范围：仅使用 Windy 官方插件文档、`windycom/windy-plugin-template` 官方仓库、Windy 官方 LeafletGL 文档及 Windy 官方社区发布说明。以下“日期”均为本次核验日期；仓库版本/提交信息另行注明。

## 关键结论

1. **会员能否安装私有插件：可以使用，但官方没有把它定义为 Premium 专属能力。** 官方插件指南明确支持“private plugin just for your own use”，并说明私有插件可供本人、朋友或机构内部使用；发布文档没有声明必须是 Premium 会员，也没有声明 Premium 会员获得额外的私有插件安装权限。因此不能据官方资料得出“只有会员能装”或“会员一定能装”的更强结论。
   - 来源：https://docs.windy-plugins.com/
   - 来源：https://docs.windy-plugins.com/getting-started/publishing-plugin.html
   - 日期：2026-09-12

2. **私有插件的含义是隐藏于插件 Gallery，不是访问控制系统。** `private: true` 表示插件不向其他用户展示在 Gallery；官方发布文档建议通过已发布的安装 URL 分享给朋友或机构。若要面向所有用户，移除该字段或设为 `false`，再请 Windy 审核后进入 Gallery。
   - 来源：https://docs.windy-plugins.com/api/interfaces/ExternalPluginConfig.html#private
   - 来源：https://docs.windy-plugins.com/getting-started/publishing-plugin.html#my-plugin-is-published-whats-next
   - 日期：2026-09-12

3. **Developer Mode 是开发期加载方式。** 运行模板的本地 HTTPS 服务后，打开 `https://www.windy.com/developer-mode`，在 Windy Developer Mode 中加载插件 URL，例如 `https://localhost:9999/plugin.js`；本地自签名证书必须先在浏览器中接受，否则插件不能工作。模板也支持加载 `example01/plugin.js` 等示例。
   - 来源：https://docs.windy-plugins.com/getting-started/debugging.html
   - 来源：https://github.com/windycom/windy-plugin-template/blob/main/README.md
   - 日期：2026-09-12

4. **正式插件必须由 `windy-plugins.com` 提供。** 官方要求所有已发布插件从该域名服务，以保证来源安全、可靠且审核后内容不被修改。官方给出的 URL 形态为 `https://windy-plugins.com/<Windy用户ID>/<插件名>/<版本>/plugin.min.js`。
   - 来源：https://docs.windy-plugins.com/getting-started/publishing-plugin.html
   - 日期：2026-09-12

5. **正式发布需要 Windy Plugins API key。** 官方流程是在 `https://api.windy.com/keys` 创建 Windy Plugins API key，将其作为 GitHub Actions secret `WINDY_API_KEY`，运行模板提供的 `publish-plugin` workflow；也可按官方脚本向 `https://node.windy.com/plugins/v1.0/upload` 上传归档。发布新版本必须提高 semver 版本号。
   - 来源：https://docs.windy-plugins.com/getting-started/publishing-plugin.html
   - 来源：https://github.com/windycom/windy-plugin-template/blob/main/.github/workflows/publish-plugin.yml
   - 日期：2026-09-12

## `pluginConfig` 字段

配置文件名必须是 `pluginConfig.ts`，对象符合 `ExternalPluginConfig`。外部插件名称必须以 `windy-plugin-` 开头；模板当前示例默认包含 `private: true`。字段如下：

- 必填：`name`（`windy-plugin-${string}`）、`version`（semver）、`title`、`icon`、`author`、`desktopUI`（`rhpane` 或 `embedded`）、`mobileUI`（`fullscreen` 或 `small`）。
- 可选：`description`、`repository`、`homepage`、`private`、`internal`、`desktopWidth`、`routerPath`、`addToContextmenu`、`listenToSingleclick`。
- `private`：不放入插件 Gallery。
- `internal`：不出现在主菜单，只能程序化打开，且安装不持久化；这与 `private` 是不同语义。
- `desktopUI`：`rhpane` 独占右侧面板；`embedded` 嵌入页面并保持打开。`desktopWidth` 默认 400 像素，仅用于 `rhpane`。
- `mobileUI`：`fullscreen` 全屏；`small` 占底部最小空间。
- `routerPath`：为已安装插件提供 `/plugin/...` URL 路由，可含参数。
- `addToContextmenu`：允许从地图右键上下文菜单打开，并向 `onopen` 传递经纬度。
- `listenToSingleclick`：插件打开时接收地图单击事件。

来源：https://docs.windy-plugins.com/api/interfaces/ExternalPluginConfig.html
来源：https://github.com/windycom/windy-plugin-template/blob/main/src/pluginConfig.ts
日期：2026-09-12

## 官方插件 API

### `map`

从 `@windy/map` 导入已初始化的 Windy LeafletGL Map 实例：

```ts
import { map } from '@windy/map';
map.on('zoomend', handler);
```

文档列出 `map`、复用 markers、`whenMapInitialized`、图层顺序及地图掩膜相关函数。当前官方 LeafletGL 文档说明它是结合 Leaflet API 与裁剪后的 MapLibre 能力的 Windy 定制库；不要假定完整 Leaflet 或完整 MapLibre API 都可用。

来源：https://docs.windy-plugins.com/api/modules/map.html
来源：https://windycom.github.io/LeafletGL/docs/
日期：2026-09-12

### `broadcast` 与事件生命周期

`@windy/broadcast` 是 Windy 的主要事件发射器，支持 `on`、`off`、`once`、`emit`；官方示例特别要求注销监听器。已文档化事件包括 `dependenciesResolved`、`paramsChanged`、`redrawFinished`、`metricChanged`、`pluginOpened`、`pluginClosed`、`rqstOpen`、`rqstClose`、`externalPluginChanged` 等。

插件生命周期为：Svelte `onMount` 在挂载时调用一次；导出的 `onopen` 在每次打开时调用，可能多次；Svelte `onDestroy` 销毁时调用一次。监听器应在 `onMount` 注册、在 `onDestroy` 移除，不应放进可能重复调用的 `onopen`。

来源：https://docs.windy-plugins.com/api/interfaces/broadcast.BasicBcastTypes.html
来源：https://docs.windy-plugins.com/api/classes/Evented.Evented.html
来源：https://docs.windy-plugins.com/getting-started/
日期：2026-09-12

### `fetch`

`@windy/fetch` 是 Windy 对 HTTP 请求的标准化封装，官方文档列出获取点预报、详细预报、雷达/卫星信息、CAP 告警摘要、实时告警、海拔、时区、静态地图 URL 等函数。插件也可按模板示例使用浏览器原生 `fetch` 请求自己的数据服务；官方模板的空域示例就是用原生 `fetch` 读取 GeoJSON。

来源：https://docs.windy-plugins.com/api/modules/fetch.html
来源：https://github.com/windycom/windy-plugin-template/blob/main/examples/05-airspace-map/plugin.svelte
日期：2026-09-12

### GeoJSON、Leaflet 与地图图层

Windy 文档说明 `L`（LeafletGL 的 Leaflet-like 全局对象）已在 TypeScript 类型中提供，无需导入。官方模板示例使用 `new L.GeoJSON(geoJsonData, options)`，再通过 `map.addLayer(layer)` 加入地图；销毁时调用 `layer.remove()`。LeafletGL 官方 API 还定义 `GeoJSON` 图层的 `addData`、`setStyle`、`toGeoJSON`、`bindPopup`、`getBounds` 等能力。

注意：LeafletGL 文档标记部分旧式工厂函数（包括 `geoJSON()`）为 deprecated，优先按当前类/API 及模板示例使用。

来源：https://docs.windy-plugins.com/getting-started/examples.html
来源：https://github.com/windycom/windy-plugin-template/blob/main/examples/05-airspace-map/plugin.svelte
来源：https://windycom.github.io/LeafletGL/docs/API/LeafletGL/classes/GeoJSON/
来源：https://windycom.github.io/LeafletGL/docs/API/LeafletGL/functions/geoJSON/
日期：2026-09-12

## 发布、托管与限制清单

- 开发加载：Developer Mode 可加载本地 HTTPS URL；自签名证书需先接受。
- 正式托管：必须使用 `windy-plugins.com`；不能把任意第三方生产域名作为正式插件托管地址。
- 发布凭证：需要 Windy Plugins API key；模板 workflow 要求 GitHub secret 名为 `WINDY_API_KEY`。
- 发布内容：上传归档中包含构建后的插件及插件配置；官方脚本还合并 repository、commit SHA、repository owner 元数据。
- 版本：新版本必须使用更高的 semver；已安装用户会收到更新通知，发布超过 7 天的更新会自动更新。
- Gallery：新插件默认私有；公开发布需取消 `private` 并请求 Windy 审核批准。
- 访问范围：官方资料描述的是 Gallery 可见性与 URL 分享，没有承诺 `private` 对 URL 使用者提供账号、会员、组织或令牌级访问控制。敏感数据保护仍应由插件自己的后端认证/授权负责。
- 运行模型：插件是运行在 Windy.com 环境中的小型 Web 应用；Svelte/TypeScript 可选，原生 JavaScript 也可用。Windy API 模块以 `@windy/` 前缀导入，类型导入必须使用 `import type`。

来源：https://docs.windy-plugins.com/getting-started/publishing-plugin.html
来源：https://docs.windy-plugins.com/getting-started/updating-plugin.html
来源：https://docs.windy-plugins.com/getting-started/
来源：https://github.com/windycom/windy-plugin-template/blob/main/.github/workflows/publish-plugin.yml
日期：2026-09-12

## 官方资料边界

截至 2026-09-12，核验到的 Windy 官方插件资料没有给出“Premium 会员专属插件安装权限”、私有插件的用户白名单机制、组织租户权限模型或 Windy 侧访问令牌机制。工程上应把 `private: true` 理解为“不进 Gallery”，不要把它当作完整的私有访问控制。
