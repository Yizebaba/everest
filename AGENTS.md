# Everest Project Specification

> 中文说明：这是 Everest 项目的协作和工程规范。英文原文是强制规则；以下中文注释仅用于帮助理解，不改变原有含义。

## Purpose

Everest is a 3D digital twin of the full Mount Everest, including the Everest
south-side route from Everest Base Camp (EBC) through C1, C2, C3, C4, and the
summit. It combines terrain, weather, and mountaineering data to support Summit
Window decisions.

> 中文说明：项目是珠峰全貌 3D 数字孪生，包括珠峰南坡登山路线，从大本营（EBC）经 C1、C2、C3、C4 到顶峰；它结合地形、天气和登山数据来辅助判断冲顶天气窗口。

## Governance

The Everest Manager is the project controller. Every request is classified as
product, architecture, GIS/3D, meteorology, backend, frontend, QA, or release
before it is assigned.

> 中文说明：每项需求都必须先分类，再交给相应领域的负责人。领域包含产品、架构、GIS/三维、气象、后端、前端、QA 和发布。

1. Specialist work is delegated to its owning agent; the manager does not
   implement specialist code directly.
2. Cross-domain work is first decomposed by the architect.
3. Each assignment includes an ID, objective, acceptance criteria, dependencies,
   and the handoff document to update.
4. Each completed task updates its domain handoff document before downstream
   work begins. Downstream agents use those documents rather than assumptions.
5. Every code change must pass QA before release.
6. The manager maintains `docs/management/board.md` and
   `docs/management/decisions.md`.
7. Delivery stages are: PRD, `/plan-ceo-review`, architecture,
   `/plan-eng-review`, UI, `/plan-design-review`, implementation, `/review`,
   QA, and release.

### Repeated Failure Escalation

When the same identifiable problem or failure event occurs three times, the
current task MUST pause before a fourth attempt. The owning Agent and Everest
Manager MUST then:

1. Consult the relevant current official documentation first.
2. Inspect the complete available logs, stack traces, provider responses,
   migration output, and test evidence for all three occurrences.
3. Identify and record the root cause, not only the symptom.
4. Record the correct next-run procedure, command/configuration, prerequisites,
   expected evidence, and rollback or cleanup steps.
5. Record the event count, timestamps, task ID, affected component, official
   documentation URLs, log locations, root cause, and next-run procedure in the
   relevant domain handoff and `docs/management/decisions.md`.
6. Resume only after the manager accepts the recorded corrective procedure.

The count applies across retries, agents, and sessions when the failure has the
same root-cause signature. A changed error is a new event only when the owner
documents why its root-cause signature differs. A successful retry does not
erase the incident history.

> 中文说明：同一个可识别问题或失败事件累计出现三次后，第四次尝试前必须暂停。负责人和总控必须先查阅当前官方文档，检查三次完整日志、堆栈、供应商响应、迁移输出和测试证据，记录根因、正确的下次运行方案、命令/配置、前置条件、预期证据及清理/回滚步骤，并写入领域交接文档和 `docs/management/decisions.md`。总控接受方案后才能继续。成功重试不能清除事件历史。

> 中文说明：负责人只处理自己领域的任务；跨领域工作先由架构负责人拆分。每个任务要写清 ID、目标、验收标准、依赖和要更新的交接文档。代码修改必须先通过 QA 才能发布。交付流程依次为：PRD、CEO 评审、架构、工程评审、UI、设计评审、实现、代码评审、QA、发布。

| Agent | Responsibility |
| --- | --- |
| product | PRD, user stories, priorities |
| architect | Modules, contracts, technical choices |
| gis-3d | Cesium, terrain, 3D Tiles, PostGIS, coordinates |
| meteorology | ECMWF, GFS, ICON, observations, atmospheric layers |
| backend | FastAPI, PostgreSQL, WebSocket, service APIs |
| frontend | Next.js and non-Cesium web UI |
| qa | Tests, regression, acceptance; never business-code changes |
| release | Build, deployment, release |

> 中文说明：表格列出了各角色的职责。`qa` 只做测试、回归和验收，不能改业务代码；`release` 负责构建、部署和发布。

## Ownership

| Path | Owner |
| --- | --- |
| `apps/web/src/cesium*`, `apps/web/src/map*`, `services/terrain/` | gis-3d |
| `services/weather/`, `services/forecast/` | meteorology |
| `services/risk/` | architect and meteorology jointly |
| `apps/api/` | backend |
| `apps/web/src/` excluding Cesium/map paths | frontend |
| `docs/*` | Relevant domain owner |
| `AGENTS.md`, `.opencode/` | Everest Manager |

> 中文说明：表格定义每个目录/文件的负责人。改动某路径下的内容应由其负责人处理；`AGENTS.md` 与 `.opencode/` 仅由项目经理负责。

## Required Handoff Documents

| Domain | Document |
| --- | --- |
| Product | `docs/product/PRD.md` |
| Architecture | `docs/architecture/architecture.md` |
| GIS | `docs/gis/terrain-spec.md` |
| Meteorology | `docs/meteorology/weather-spec.md` |
| API | `docs/api/API.md` |
| QA | `docs/qa/test-plan.md` |

## Mandatory Official Documentation & Verification Rule

This rule is mandatory for every Agent and every task.

Before every task, and whenever a technical issue arises, the Agent MUST
consult the relevant official technical documentation first.

This includes, but is not limited to:

- installation
- data retrieval
- APIs
- authentication
- SDKs
- code standards
- dependencies
- versions
- configuration
- protocols
- data formats
- technical limitations
- licensing
- commercial-use restrictions

### External Integration Verification

Before implementing any external integration, the Agent MUST identify and
consult the official documentation for that specific service, API, or data
source.

For data integrations, the Agent MUST verify:

1. Official provider
2. Official endpoint/access method
3. Authentication requirements
4. Data format
5. Variables
6. Units
7. Update frequency
8. Spatial coverage
9. Temporal coverage
10. License
11. Commercial-use restrictions
12. Rate limits
13. Current API/version status

If any of the above cannot be verified, the Agent MUST NOT claim the
integration is verified.

The Agent MUST NOT:

- invent API endpoints
- invent credentials or API keys
- assume undocumented API behavior
- assume data availability
- assume licensing or commercial-use permission
- use an unofficial substitute without explicit approval
- claim a data source is `verified` without real-data verification
- rely on outdated documentation when current official documentation is available

For external data sources, the Agent MUST record the verified information in
the relevant data-source or domain documentation before downstream work begins.

Each domain must maintain its corresponding handoff document. Downstream
Agents MUST use those documents rather than assumptions.

### Verification Status

An external integration MUST NOT be considered complete merely because a
connector, SDK, configuration, or API client has been implemented.

The minimum verification flow is:

`official documentation`
→ `connector`
→ `real data`
→ `parser`
→ `normalizer`
→ `quality control`
→ `database/object storage`
→ `service/API`
→ `tests`
→ `documentation`
→ `review`

Only after successful real-data verification may an integration be marked
`verified`.

If only the connector or configuration has been completed, the status MUST
remain `configured` or `connected`, as appropriate.

### Chinese Explanation

以上规则为所有 Agent 和所有任务的强制工程规则。

每项任务开始前，以及出现任何技术问题时，Agent 必须优先查阅对应的
官方技术文档。

对于任何外部服务、API 或数据源，在开始接入之前，必须确认并查阅该
服务、API 或数据源的官方文档。

对于数据接入，必须确认：

1. 官方提供方
2. 官方接口或官方数据获取方式
3. 身份认证要求
4. 数据格式
5. 数据变量
6. 数据单位
7. 更新频率
8. 空间覆盖范围
9. 时间覆盖范围
10. 许可证
11. 商业使用限制
12. 速率限制
13. 当前 API/版本状态

如果上述任何一项无法确认，Agent 都不得声称该数据源或集成已经
`verified`。

Agent 不得：

- 编造 API 地址
- 编造 API Key 或凭据
- 猜测未公开的 API 行为
- 猜测数据是否存在
- 猜测许可证或商业使用权限
- 未经批准使用非官方替代数据源
- 没有真实数据验证就声称接入完成
- 在存在最新官方文档时依赖过时信息

对于外部数据源，经过确认的信息必须记录到对应的数据源文档或领域
交接文档中，然后下游 Agent 才能继续工作。

领域交接文档必须持续维护。下游 Agent 必须以交接文档中已经确认的
事实为依据，不得自行猜测。

外部集成不能因为“Connector 已经写好”、“SDK 已安装”或“配置已经
完成”就被视为完成。

必须经过：

`官方文档`
→ `Connector`
→ `真实数据`
→ `解析`
→ `标准化`
→ `质量检查`
→ `数据库/对象存储`
→ `服务/API`
→ `测试`
→ `文档`
→ `评审`

只有完成真实数据验证后，才能将状态标记为 `verified`。

如果仅完成 Connector 或配置，则只能保持为 `configured` 或
`connected`，不能标记为 `verified`。

If any of the above cannot be verified, the Agent MUST NOT claim the
integration is verified.

## Technology Baseline

- Web: Next.js, React, CesiumJS.
- Terrain: CesiumJS, 3D Tiles, DEM.
- Storage: PostgreSQL, PostGIS, object storage.
- Services: FastAPI, Python, WebSocket.
- Data tooling: xarray, netCDF, GDAL.

> 中文说明：固定技术栈为 Next.js/React/CesiumJS（网页和三维地图）、PostgreSQL/PostGIS（存储）、FastAPI/Python/WebSocket（服务）及 xarray、netCDF、GDAL（气象和地理数据处理）。

## Engineering Standards

All Python and TypeScript code follows the Google Python and TypeScript style
guides. The following requirements are mandatory:

- Python: 80-column limit, 4 spaces, absolute imports grouped standard library,
  third party, and local; public APIs fully typed; module/class/function/method
  docstrings; no bare `except`, mutable default arguments, relative imports, or
  assertion-based production validation; use context managers for resources.
- TypeScript: ES modules, named exports only, `const` by default, no `var`, no
  default exports, single quotes, `interface` preferred for component props,
  `import type` for type-only imports, and `??` for nullish fallback.
- Before delivery: run `black --line-length 80` and `pylint` for Python; run
  `prettier --write`, `eslint`, and `tsc --noEmit` for TypeScript.
- Tests may use assertions. Necessary framework exceptions require a concise
  explanatory comment.
- Ports must be unallocated, non-standard, randomly selected, and documented.

> 中文说明：代码必须遵循 Google Python/TypeScript 风格。Python 每行最多 80 字符；TypeScript 使用具名导出、单引号和 `const`。交付前必须运行格式化、静态检查和类型检查。端口必须随机、非标准、未被占用，并记录在文档中。

## EV-DATA-001: Approved Data Infrastructure

> 中文说明：以下内容是数据基础设施任务 `EV-DATA-001` 的强制范围和验收条件。

### Scope and Prohibitions

Use only approved free/public sources. Do not procure or integrate commercial
APIs, Meteomatics, Pleiades Neo, SkySat, WorldView, WorldDEM, commercial weather
services, or unapproved substitutes.

Do not invent endpoints, credentials, licenses, data, or successful status.

### Geographic Data Scope

Data acquisition MUST be limited to the Everest project Area of Interest (AOI)
defined in `docs/everest-aoi.md`.

The default operational AOI is:

- Everest and the South Col climbing route
- EBC, C1, C2, C3, C4, and Summit
- Khumbu Icefall
- Western Cwm
- Lhotse Face
- surrounding area within a 100 km radius of Mount Everest

Data outside the approved AOI MUST NOT be downloaded unless the task explicitly
requires an expanded AOI and the expansion is documented and approved.

Do not download global datasets when an AOI-limited dataset or subset is
sufficient for the task.

### Raw Data and Repository Storage

Large raw datasets MAY be downloaded and processed locally or stored in approved
external/object storage when required by the project.

Raw datasets MUST NOT be committed to Git.

The default repository limit for individual data files is:

- <= 10 MB: may be committed only when required as a test fixture, sample,
  metadata example, or small development asset.
- > 10 MB: MUST NOT be committed to Git.
- Raw GRIB, GRIB2, NetCDF, GeoTIFF, satellite products, DEM tiles, point clouds,
  and similar source datasets MUST be treated as external/raw data regardless
  of file size unless explicitly approved as a small test fixture.

Large raw data MUST be stored outside the Git repository, for example in:

- local `data/raw/`
- local cache/storage
- object storage
- approved data volume

Repository code MUST reference the data location or retrieval mechanism rather
than committing the raw dataset itself.

Do not download global datasets, commit large raw files, remove V2 features,
modify a tested Risk Engine, change the meaning of weather core fields, build
AI, or build new UI.

Approved sources are ECMWF IFS, ECMWF AIFS, NOAA GFS, DWD ICON, Everest AWS,
Pyramid Meteorological Network, Himawari-8/9, Sentinel-1, Sentinel-2, Landsat
8/9, Copernicus DEM GLO-30, NASA ICESat-2, ICIMOD RDS, NASA Earthdata/Harmony,
Copernicus EMS, and OpenStreetMap.

> 中文说明：只能使用上面列出的免费/公开批准数据源。禁止接入商业或未批准的数据源；
> 不能编造接口、凭据、许可证、数据或成功状态。
>
> 数据获取范围必须遵守 `docs/everest-aoi.md` 中定义的 Everest 项目 AOI。
> 默认允许的数据范围包括珠峰及南坡登山路线，以及珠峰周边 100 公里范围。
> 如果任务需要超出该范围的数据，必须明确说明原因并获得批准后才能扩大 AOI。
> 在已有 AOI 数据足以完成任务时，不得下载全球数据。
>
> 大型原始数据允许为了项目处理而下载到本地或存储到批准的对象存储中，
> 但不得提交到 Git 仓库。
>
> 单个数据文件：
>
> - <= 10 MB：只有在确实作为测试样本、fixture、示例或开发资源时才允许提交。
> - > 10 MB：不得提交到 Git。
> - GRIB、GRIB2、NetCDF、GeoTIFF、卫星产品、DEM、点云等原始数据，
>   无论文件大小，原则上都属于外部原始数据，不应提交到 Git；只有明确
>   作为小型测试样本并符合大小限制时才允许提交。
>
> 大型原始数据应放在 `data/raw/`、本地缓存、对象存储或其他批准的数据存储中。
> Git 仓库只保存代码、配置、Schema、元数据、测试以及数据获取和处理逻辑，
> 不保存大型原始数据本体。
>
> 同时禁止删除 V2 功能、修改已经测试通过的 Risk Engine、改变核心天气字段
> 的含义、开发 AI 或开发新的 UI。

External sources must never be called by the frontend. The only permitted flow is:

`external source -> connector -> raw data -> parser -> normalizer -> QC ->`
`canonical model -> PostgreSQL/PostGIS or object storage -> service -> REST/WS`
`-> frontend`.

> 中文说明：前端不能直接访问外部数据源。必须严格遵循：外部来源 -> 连接器 -> 原始数据 -> 解析 -> 标准化 -> 质量检查（QC）-> 统一模型 -> 数据库/对象存储 -> 后端服务 -> REST/WebSocket -> 前端。

### Current Delivery Boundary

Execute only the following phases, in order, then stop pending further
instruction:

1. A: Data Registry.
2. B: Weather Schema.
3. C: ECMWF IFS.
4. D: NOAA GFS.
5. E: DWD ICON.
6. F: ECMWF AIFS.

> 中文说明：当前只能依次执行 A 到 F：数据源登记、天气数据结构、ECMWF IFS、NOAA GFS、DWD ICON、ECMWF AIFS。完成前，不能开始 AWS 站、Pyramid、卫星、地形、环境、OSM、AI 或风险相关工作。

Do not begin Everest AWS, Pyramid, satellite, terrain, environmental, OSM, AI,
or Risk work in this delivery. A source is not complete until it has passed:

`connector -> real data -> parser -> normalizer -> DB -> API -> test -> docs -> review`.

The delivery stops only after all four forecast sources have real retrieval,
parsing, normalization, QC, persistence, queryable API results, tests, docs,
and health status. A connector without real-data verification is `configured`,
never `verified`.

#### A-F Display Acceptance (方案 A / ADR-015)

Everest Manager ruling, 2026-08-22: in EV-DATA-001 phases A-F, "frontend
display" means the backend REST surface is queryable and has returned real
canonical data. It does not mean a Next.js, Cesium, browser, or other UI.

The A-F display/stop-gate APIs are exactly:

- `GET /api/weather/current`
- `GET /api/weather/forecast`
- `GET /api/weather/profile`
- `GET /api/weather/sources`
- `GET /api/data-health`

A-F does not require `apps/web`, TypeScript, Cesium, or any new UI. The
prohibition on building new UI remains in force. Frontend display of pages is
deferred to a separately authorized delivery. No frontend may call ECMWF, NOAA,
DWD, or any other external source.

Historical disposable evidence that these five APIs returned real records is
sufficient for the A-F display criterion. Current runtime/API availability
after teardown remains `unknown` and is not a live-service claim.

#### Lifecycle And Health Semantics

Keep two tracks. Do not mix them:

- Historical disposable `verified`/`healthy` is an in-run database fact after
  a canonical commit. It is not current operational health.
- After teardown, current health and API availability are `unknown`. AIFS may
  remain documented `connected` as the current registry interpretation.
- Source presence does not imply `verified`. Do not write historical health as
  current production health.

#### Non-Blocking Follow-Ups

These items MUST NOT block A-F source/core close:

- Gate C-Operational (IAM/ACL, legal/WORM, Git exclusion): production-only.
- Project-root `tmp-gfs*` / `tmp-icon*` disposition: separate authorization;
  do not hash, move, or delete those artifacts until authorized.
- EBC/C1/C2/C3/C4 camp-labeled profile records: the profile API may filter
  those labels; connectors MUST NOT invent camp coordinates. Summit-only or
  null `route_profile` is accepted for A-F.
- Measured current latency and a continuously running service.
- `docs/product/PRD.md`, `docs/gis/terrain-spec.md`, and `GET /api/data-sources`.
- GFS/ICON commercial-use confirmation: keep pending/unknown.

#### Close-Out Prohibitions

Do not, in order to close EV-DATA-001:

- write Next.js, Cesium, or any new UI;
- rerun external retrieval or a database solely to close documentation;
- operate on `tmp-gfs*` / `tmp-icon*`;
- invent camp coordinates or EBC-C4 labeled data;
- claim current health as `verified`.

> 中文说明：一个来源必须完整通过“连接器 -> 真实数据 -> 解析 -> 标准化 -> 数据库 -> API -> 测试 -> 文档 -> 评审”才算完成。经理裁决（方案 A / ADR-015）：A-F 的「前端能显示」= 上述五个后端 API 已用真实数据可查询，不要求新建任何 UI。禁止新 UI 的规则继续有效。历史一次性 `verified`/`healthy` 不得写成现网健康；拆库后当前健康为 `unknown`。生产加固、仓库内 tmp 原始数据、营地廓线、现网延迟、PRD/地形、`/api/data-sources`、GFS/ICON 商用许可均不阻断 A-F 关闭。只有连接器配置好但未用真实数据验证时，只能是 `configured`，不能称为 `verified`。

### Registry and Scheduling

Create `docs/data-sources.md` and a `data_source_registry` configuration/database
layer. Each source records `source_id`, `name`, `provider`, `category`, `status`,
`access_method`, `endpoint`, `format`, `update_frequency`, `spatial_resolution`,
`temporal_resolution`, `coverage`, `license`, `commercial_allowed`,
`credentials_required`, `last_success_at`, `last_failure_at`, and `health_status`.

Allowed status values are `planned`, `configured`, `connected`, `verified`,
`degraded`, and `disabled`. Scheduling is configuration-driven and supports
interval, retry, timeout, backoff, last success/failure, next run, and source
health. Do not hard-code cron behavior in business code.

> 中文说明：需创建 `docs/data-sources.md` 和 `data_source_registry` 数据源登记层。每个来源必须保存身份、访问方式、格式、更新频率、覆盖范围、许可证、凭据、最近成功/失败时间和健康状态等列出的字段。调度由配置驱动，不可在业务代码写死 cron。

### Canonical Weather Contract

Create `docs/weather-spec.md`. Core fields retain these meanings:

`timestamp`, `latitude`, `longitude`, `altitude`, `wind_speed`,
`wind_direction`, `temperature`, `precipitation`, `visibility`.

Recommended fields: `pressure`, `relative_humidity`, `dew_point`, `cloud_cover`,
`cloud_base`, `cloud_top`, `snowfall`, `gust_speed`, `source`, `model`,
`forecast_cycle`, `forecast_lead_time`, and `quality_flag`.

Units: UTC ISO-8601 timestamps; temperature Celsius; wind speed m/s; wind
direction 0-360 degrees; precipitation mm; visibility and altitude meters.
Forecast, observation, satellite, and derived records are distinct record types.

> 中文说明：需创建 `docs/weather-spec.md`。核心天气字段的含义不能改变：时间、纬度、经度、海拔、风速、风向、温度、降水、能见度。单位固定为 UTC ISO-8601、摄氏度、m/s、0-360 度、毫米和米。预报、观测、卫星和推导数据必须是不同记录类型。

Use independent connectors under `services/weather/` for `ecmwf`, `aifs`, `gfs`,
and `icon`; do not create a monolithic weather module. Retain immutable raw
source payloads and raw metadata. Deduplicate using source, dataset, timestamp,
spatial key, forecast cycle, lead time, and when necessary a content hash.

> 中文说明：`ecmwf`、`aifs`、`gfs`、`icon` 要在 `services/weather/` 中分别使用独立连接器，不能合成一个巨型天气模块。原始数据和元数据必须不可变地保留；去重使用来源、数据集、时间、空间位置、预报周期、预报时效，必要时使用内容哈希。

### Forecast Source Acceptance

- ECMWF IFS: use an official public channel, support actual GRIB/NetCDF input,
  retain raw metadata, track model/run/cycle/lead/valid time, retry failures,
  deduplicate downloads, and retrieve an Everest, South Col, or summit sample.
- NOAA GFS: use the official source, parse GRIB2, retain cycle, lead, location,
  altitude layer, time, and source metadata, and complete a real retrieval test.
- DWD ICON: use DWD Open Data, parse GRIB2, retain ICON metadata, normalize to
  the canonical schema, and complete an Everest-area real-read test.
- ECMWF AIFS: use a separate connector, always record `model = AIFS`, and make
  IFS comparison possible.

Each source must have connector, parser, normalization, schema, real-data smoke,
and failure/retry tests. QC checks timestamps, coordinates, altitude, units,
missing values, ranges, duplicates, stale data, source identity, and checksums.
QC flags anomalies rather than deleting raw data.

> 中文说明：每个预报来源都必须包含连接器、解析器、标准化、数据结构、真实数据冒烟测试和失败/重试测试。QC 要检查时间、坐标、海拔、单位、缺失值、范围、重复、过期、来源身份和校验和；异常只能打标，不能删除原始数据。

### API and Health

The backend service layer owns `GET /api/weather/current`,
`GET /api/weather/forecast`, `GET /api/weather/profile`,
`GET /api/weather/sources`, and `GET /api/data-health`. A future unified API
also reserves observations, satellite, terrain, route, and data-source endpoints.

Weather profiles must support EBC, C1, C2, C3, C4, and Summit as filter labels
and distinguish forecasts from observations. Connectors MUST NOT invent camp
or route geometry. For A-F, a working profile filter with Summit-only or null
`route_profile` satisfies the API requirement. `/api/data-health` reports real
health only; source presence does not imply `verified`. Under ADR-015, these
five APIs are the A-F display acceptance surface.

> 中文说明：后端负责当前天气、预报、垂直廓线、来源和数据健康度这五个 API。廓线 API 必须能按 EBC、C1、C2、C3、C4、Summit 标签过滤并区分预报与观测；连接器不得编造营地坐标。A-F 阶段 Summit-only 或空 `route_profile` 即可满足 API 要求。`/api/data-health` 必须反映真实健康状态，来源存在不代表已验证。按 ADR-015，这五个 API 就是 A-F 的 display 验收面。

### Phase-F Report

After the four forecast sources are complete, report the actual successful and
failed sources, exact official data URLs, formats, update frequencies, download
sizes, database tables, APIs, test count and failures, licensing findings,
current latency, Everest coverage, and next-stage recommendation. A successful
claim must identify the real UTC data time and parsed variable count, including
an Everest-area coordinate such as `27.9881, 86.9250`.

> 中文说明：四个预报源完成后，必须提交 Phase-F 报告，列出真实成功/失败来源、官方 URL、格式、更新频率、下载大小、数据库表、API、测试结果、许可证、延迟、珠峰覆盖范围和下一阶段建议。任何成功结论都必须带实际 UTC 数据时间、解析变量数和珠峰区域坐标，例如 `27.9881, 86.9250`。


## Everest OS - 10-Dimension Domain Architecture (Phase 1)

**Approved:** 2026-08-27 (Everest Manager). Phase 1 defines presentation/domain
views over the existing canonical API contracts and reserves interfaces;
existing 3D rendering and API request logic must remain fully operational.

### Domains (TypeScript presentation contracts in `apps/web/src/types/schema.ts`)

1. Environment - running context (Everest / cave / mine / wilderness); Everest only now.
2. Terrain - DEM / elevation / slope / terrain profile (GLO-30 API + Cesium terrain).
3. Weather - multi-source canonical API records plus bounded derived U/V wind frames.
4. Sensor - hardware/station data (AWS / Pyramid / custom nodes); reserved/empty.
5. Route - real OSM South Col route and camp nodes from the Everest API.
6. Hazard - crevasses, avalanche zones; reserved/empty.
7. Risk - existing deterministic Python Risk Engine exposed through the Everest API; no AI.
8. Communication - link states (satellite / mesh / 4g / offline); reserved/empty.
9. Device - bound terminal devices; reserved/empty.
10. Mission - task context; reserved/empty.

### Module mapping

- `apps/web/src/domains/terrain.ts` wraps the existing GLO-30 terrain API.
- `apps/web/src/domains/weather.ts` wraps validated canonical weather responses.
- `apps/web/src/domains/risk.ts` adapts the backend Risk Engine response; it
  must not duplicate the scoring algorithm in TypeScript.
- Reserved domains return explicit `reserved`/empty states, never fabricated
  operational readings, devices, links, hazards, or missions.

### Internationalization

- locale: 'en' | 'zh' reserved in the Environment domain.
- Bilingual catalog for core terms (temperature, wind speed, visibility,
  precipitation, Summit Window, GO/STOP) in `apps/web/src/i18n/messages.ts`.
- Language switch exposed in the top navigation bar.

### Constraints (unchanged)

The Everest OS abstraction must not: call external providers from the
frontend, invent geometry or data, remove V2 features, modify a tested Risk
Engine beyond presentation-layer semantics, build AI, or change canonical
weather field meanings.

Weather retrieval and decoding use reviewed open-source adapters. Existing
direct ecCodes parsers remain canonical-ingestion fallbacks. The MIT
`RaymanNg/3D-Wind-Field` project is pinned as a reference at commit
`ddbbca160c14b5fe081fdd5c2e3dcd05718dba66`; its demo application, provider
calls, NetCDF browser loader, and GUI are not copied. GPU rendering may only be
enabled through verified Cesium public APIs. If that boundary is unavailable,
the product must report fallback status and retain the existing lightweight
particle renderer rather than use undocumented renderer internals.
