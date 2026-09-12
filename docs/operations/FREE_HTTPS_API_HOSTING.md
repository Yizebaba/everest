# FastAPI/Docker 公开 HTTPS 免费托管调研

调查日期：2026-09-12

范围：截至本日期，只核验各厂商的官方定价、部署、域名/TLS、运行时和数据库文档，以及 FastAPI 官方 CORS 文档。不创建账号、不部署资源、不以社区帖或第三方价格汇总作为依据。

适用对象：`infra/docker/api.Dockerfile` 中的 Everest FastAPI 容器（服务端口 `52147`），以及当前 Docker Compose 中依赖的 PostgreSQL、迁移和批处理服务。Windy 插件需要稳定、公开可访问的 HTTPS API 端点；浏览器跨域访问仍由 FastAPI 的 CORS 响应头决定，不由托管商自动解决。

## 结论

1. **严格意义的“持续免费、可运行现有 Docker API、可与自管 PostgreSQL/TimescaleDB 一起长期运行”的首选是 OCI Always Free VM，但不等于无条件永久在线。** OCI 允许在生命周期内使用 Always Free VM：Arm A1 合计 2 OCPU/12 GB RAM，或最多两台 AMD Micro；可在 VM 上自行运行 Docker Compose、FastAPI、PostgreSQL/TimescaleDB 和反向代理。它要求信用卡进行注册验证，Always Free 容量可能不足，且连续 7 天 CPU、网络、内存均低使用率的实例可能被回收。HTTPS 不是 VM 的自动托管功能，必须自行运行反向代理和证书续期，或配置 OCI 负载均衡与证书服务。它适合非关键的长期开发/演示端点，不适合未配置监控、备份、恢复演练和冗余的生命安全生产告警服务。

2. **最省运维的 API 演示候选是 Cloud Run，但不是“无需付款方式的永久免费主机”。** Cloud Run 官方 FastAPI quickstart 明确要求项目启用 Billing；请求计费有每月免费额度（200 万请求、180,000 vCPU-seconds、360,000 GiB-seconds，按 `us-central1` 基准）。它原生接收 Docker/OCI 镜像、生成 `https://*.run.app` HTTPS URL，并在无流量时缩至零，因而存在冷启动。保留最小实例或持续后台任务会消耗额度并可能收费；自定义域名的推荐方案是外部应用负载均衡，Cloud Run Domain Mapping 仍是 Preview 且官方不建议生产使用。Cloud Run 不提供免费的 PostgreSQL/TimescaleDB 配套服务。

3. **Render 免费层只适合联调和临时演示。** 它支持 Python/FastAPI、Docker、`onrender.com` HTTPS、免费自定义域名 TLS；但空闲 15 分钟后休眠，首次请求约需一分钟恢复，免费 Web 服务每工作区每月总计 750 实例小时且可能随时重启。免费 PostgreSQL 仅 1 GB，并在创建 30 天后到期，不能支撑 Everest 的持久时序数据。其官方文档表明没有支付方式时达到带宽/构建额度会暂停服务，而非要求免费 Web 服务预先绑定卡。

4. **Railway Free 可提供短小容器 API，但仅有每月 1 美元资源额度，不能视为持续免费。** 它支持 FastAPI、Docker、自动 HTTPS 的 `*.railway.app` 域名；Free 计划不能使用自定义域名。官方免费 Trial 明确无需信用卡，但已核验的公开文档没有明确承诺 Free 计划在任何情况下都无需卡，且 Railway 已说明订阅的付款方式使用后付费卡。PostgreSQL 与 TimescaleDB 模板可部署，但都是资源计费的容器/模板，`$1` 很快耗尽，故不适合长期端点或数据库。

5. **Koyeb 的部署能力完整，但当前公开定价没有可作为长期方案的免费应用计算承诺。** 它的 FastAPI、Docker、`*.koyeb.app` HTTPS 和自定义域名 TLS 都受支持；文档仍描述 Free Instance 会在一小时无流量后缩至零，公开价格页却只列出了从 Pro 开始的组织计划及按量计算。因此不把它列为截至本日期可依赖的“持续免费”应用托管。其免费 PostgreSQL 仅 5 计算小时/月、1 GB，5 分钟不活跃即休眠；虽列出 TimescaleDB 扩展，但仅 Apache-2 许可功能且不支持压缩。付款方式要求未在本次官方公开页面中明确为免费应用注册前置条件，应在实际注册流程再次核验。

6. **Fly.io 已无持续免费计算。** 它有 FastAPI、Docker、`*.fly.dev` HTTPS、可配置自定义域名和自动证书，但所有组织（非 Linked Organization）均须留存信用卡；当前资源按量收费，最小的 256 MB shared CPU Machine 约 2 美元/月，停止的 Machine 仍有 rootfs 费用。可关闭自动停机以保持运行，但这会持续收费。其托管 PostgreSQL Basic 从 38 美元/月开始，只声明 `pgvector` 与可选 PostGIS，不适合 TimescaleDB 免费部署。

7. **Cloudflare Workers Free 不是现有 Docker/FastAPI 的直接托管目标。** 原生 Workers Free 是受限的事件驱动边缘运行时，支持 JavaScript/Wasm 等 Worker 运行时语言接口，限制为每天 100,000 请求、每次 10 ms CPU、128 MB 内存；可为轻量转发/缓存/鉴权层提供 HTTPS，但不能原样运行当前 Python FastAPI Docker Compose。Cloudflare Containers 能运行任意语言和容器镜像，但仅限 Workers Paid，按实例活动时间计费且实例会休眠，因此也不是免费常驻 FastAPI 方案。Workers Custom Domain 能自动创建 DNS 和证书，但要求活动的 Cloudflare zone；Free 计划资料未列出绑卡要求。

## 方案对比

| 候选 | 免费性质与付款方式 | 休眠/连续运行 | Docker/FastAPI | PostgreSQL/TimescaleDB | TLS、域名与 Windy HTTPS | 判定 |
| --- | --- | --- | --- | --- | --- | --- |
| OCI Always Free VM | Always Free 资源；注册通常需要手机和信用卡验证，不升级不会扣卡。 | 可常驻；但满足连续 7 天低 CPU/网络/内存条件的闲置 VM 可被回收，且免费 A1 容量可能不可用。 | 可行：Linux VM 上自管 Docker/Compose。 | 可自管现有 Postgres 容器；TimescaleDB 镜像、ARM 架构和备份策略须在实施前按 Timescale 官方资料另行核验。 | 公开 IP 可对外；需自管反向代理/TLS，或使用 OCI 负载均衡/证书服务。适合形成稳定自有 HTTPS URL 后供 Windy 调用。 | **长期零预算首选，但有运维与回收风险。** |
| Cloud Run | 按量免费额度，不是固定免费实例；部署前必须启用 Billing。 | 默认缩至零；无流量的实例不保留超过约 15 分钟。最小实例/后台 CPU 可能收费。 | 可行：官方有 FastAPI quickstart，接受 OCI/Docker 镜像。容器须监听 `0.0.0.0:$PORT`。 | 仅连接外部/自管数据库；未提供免费的托管 PostgreSQL/TimescaleDB。 | 默认 `run.app` 是 HTTPS；自定义域名推荐负载均衡，Domain Mapping 是 Preview。默认 URL 已可作 Windy HTTPS endpoint。 | **最适合短期 API demo；启用预算、告警和限额后使用。** |
| Render Free | 0 美元 Free Web；官方资料未说创建免费 Web 必绑卡。 | 15 分钟无入站请求即休眠；唤醒约一分钟；750 小时/月共用，可能重启。 | 可行：官方支持 FastAPI、Dockerfile 和镜像。 | 免费 Postgres 1 GB，30 天到期；官方来源未给出免费 TimescaleDB 承诺。 | `onrender.com` HTTPS；免费 Web 支持自定义域名和托管 TLS。 | **仅开发、联调、临时展示。** |
| Railway Free | 每月 1 美元额度；Trial 的 5 美元/30 天明确无需卡。Free 的长期卡要求未被本次资料明确承诺；付费订阅使用后付费卡。 | 无平台强制休眠的官方承诺；资源按秒计费，额度耗尽即不能作为长期服务假设。 | 可行：官方 FastAPI 与 Dockerfile 指南。 | PostgreSQL、TimescaleDB 模板可部署但均消耗额度；官方称这些模板为非托管。 | 自动 SSL 与 `railway.app` 域名；Free 计划为 0 个自定义域名。 | **临时 PoC，不是长期免费。** |
| Koyeb | 公开价格页没有免费应用计算；应用 Free Instance 的现状与价格页不一致，不能据此承诺。卡要求未明确。 | 文档称 Free Instance 1 小时无流量缩零；其他服务默认 5 分钟缩零。 | 可行：有 FastAPI 和预构建 Docker 镜像官方指南。 | 免费 Postgres 5 小时/月、1 GB、5 分钟休眠；TimescaleDB 功能受限。 | `koyeb.app` 与自定义域名均自动 TLS。 | **当前不作为免费承诺方案。** |
| Fly.io | 无持续免费计算；全部普通组织要求信用卡。 | 可选 autostop/autostart；不启用则 Machine 保持运行并计费。 | 可行：官方 FastAPI 指南会生成 Dockerfile。 | 托管 PG Basic 38 美元/月起；未列 TimescaleDB。 | `fly.dev` HTTPS；可配置自定义域名和自动证书。 | **功能可行但非免费。** |
| Cloudflare Workers Free | Workers Free 默认可用；官方页面未列绑卡要求。 | 无常驻进程概念；每请求执行。Containers 仅 Paid 且可睡眠。 | 原生 Worker 不适配现有 FastAPI/Docker；Containers 可运行镜像但付费且需 Worker 代理。 | D1/DO 不是 PostgreSQL；Hyperdrive 是连接加速层，不能替代 TimescaleDB。 | `workers.dev`/Custom Domain 可 HTTPS；自定义域须有活动 Cloudflare zone，证书自动管理。 | **只可作为边缘代理/缓存，不是 API 主机。** |

## 推荐路径

### 路径 A：零预算、需要较长运行时间

选择 OCI Always Free A1 VM，运行经过 ARM 兼容性验证后的 `infra/docker/compose.yml` 或拆分后的生产 Compose。API 前置 HTTPS 反向代理，数据库只开放在 Docker 私网或 loopback；暴露的仅是 `443`。实施前必须完成：

- 为容器与扩展确认 `linux/arm64` 支持，特别是 PostgreSQL/TimescaleDB、迁移和数据处理依赖。
- 配置健康检查、日志、磁盘备份、恢复演练、证书续期和实例回收告警。
- 使用真实域名和 HTTPS；不要把裸 IP 或 HTTP URL 填入 Windy 插件。
- 将 API 路由、数据库和定时/数据摄取分开评估。当前 `scheduler` 为批处理，不能把“API 可访问”误解为所有背景数据生产链路已适合免费 VM。

这条路径可复用现有 Docker 边界，但免费容量、卡验证、闲置回收和单机故障都是真实约束。对 MHEWS 的 RED 级告警链路，不能将它作为唯一运行环境。

### 路径 B：最快获得公开 HTTPS 开发端点

选择 Cloud Run，并将当前 API 与持久数据库解耦：API 部署为一个公有服务，数据库使用经批准的外部 PostgreSQL；不使用容器本地文件保存业务状态。默认 `https://<service>-<hash>-<region>.run.app` 已满足 Windy 的 HTTPS 入口要求。设置最大实例数、Cloud Billing 预算/告警和费用上限，接受缩零与冷启动；不要设置最小实例为长期“免费保活”策略。

### 明确不推荐

- 不为防止 Render/Koyeb/Fly 休眠而部署外部定时 ping。这既不改变免费层的生产限制，也会掩盖真实可用性和费用风险。
- 不将 Render 免费 PostgreSQL、Railway Free 容器额度或 Koyeb 免费数据库用于 Everest 长期时序/风险数据。
- 不把 Cloudflare Workers 重写成主 API，除非另行决定重构为 Worker 运行时。它适合在未来作为 HTTPS 边缘入口、缓存或限流层，而不是直接承载现有 Python Docker 应用。

## Windy 插件与 CORS

托管商负责公网路由和 TLS 终止，不会自动添加浏览器的跨域授权。FastAPI 官方建议使用 `CORSMiddleware` 维护显式 origin 列表；开启凭据时，origin、方法和头不能使用 `*`。当前代码已经从 `EVEREST_CORS_ALLOWED_ORIGINS` 读取逗号分隔的显式来源并拒绝 `*`，因此公开部署时应设置实际插件页面的 origin，例如：

```text
EVEREST_CORS_ALLOWED_ORIGINS=https://www.windy.com
```

若还有独立控制台或本地开发页面，将每个实际 `scheme + host + port` 分别加入该变量。不要把 API 域名本身误当作浏览器 origin，也不要用 `*` 替代明确清单。部署完成后应由浏览器从 Windy 实际页面发起一次 `OPTIONS` 预检和目标 API 请求，核验 `Access-Control-Allow-Origin`、鉴权和缓存行为。

## 官方来源

### Cloud Run

- 定价与免费额度：https://cloud.google.com/run/pricing
- FastAPI 部署与必须启用 Billing：https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service
- 容器契约、HTTPS 终止、缩零和空闲实例生命周期：https://cloud.google.com/run/docs/container-contract
- 请求/实例计费和最小实例：https://cloud.google.com/run/docs/configuring/billing-settings
- 自定义域名限制与 TLS：https://cloud.google.com/run/docs/mapping-custom-domains

### Render

- 免费服务、15 分钟休眠、750 小时与免费 Postgres 30 天限制：https://render.com/docs/free
- Web 服务、FastAPI、Docker 和 HTTPS：https://render.com/docs/web-services
- Docker 部署：https://render.com/docs/docker
- 自定义域名与自动 TLS：https://render.com/docs/custom-domains
- 当前公开定价：https://render.com/pricing

### Koyeb

- 当前公开定价：https://www.koyeb.com/pricing
- FastAPI 与 Docker 部署：https://www.koyeb.com/docs/deploy/fastapi
- 预构建 Docker 镜像：https://www.koyeb.com/docs/build-and-deploy/prebuilt-docker-images
- Scale-to-Zero 与 Free Instance 行为：https://www.koyeb.com/docs/run-and-scale/scale-to-zero
- 域名与自动 TLS：https://www.koyeb.com/docs/run-and-scale/domains
- PostgreSQL、TimescaleDB 扩展和空闲休眠：https://www.koyeb.com/docs/databases

### Fly.io

- 资源计费、信用卡要求、TLS 和存储费用：https://fly.io/docs/about/pricing/
- FastAPI 部署：https://fly.io/docs/python/frameworks/fastapi/
- 自动停机/启动：https://fly.io/docs/reference/fly-proxy-autostop-autostart/
- 自定义域名和 TLS：https://fly.io/docs/networking/custom-domain/
- 托管 PostgreSQL 价格与扩展：https://fly.io/docs/mpg/

### Railway

- 当前公开定价、Free 计划与域名额度：https://railway.com/pricing
- 计划、资源价格与付款方式说明：https://docs.railway.com/reference/pricing/plans
- FastAPI 和 Dockerfile 部署：https://docs.railway.com/guides/fastapi
- Dockerfile 构建：https://docs.railway.com/deploy/dockerfiles
- 公网 HTTPS、自动 SSL 和自定义域名：https://docs.railway.com/guides/public-networking
- PostgreSQL 与 TimescaleDB 模板状态：https://docs.railway.com/guides/postgresql

### Oracle Cloud Infrastructure

- Free Tier、注册验证和账户规则：https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- Always Free VM、空闲回收、证书、负载均衡和资源额度：https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- 创建公开 VM：https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm
- 公开 IP、互联网连接前置条件：https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingpublicIPs.htm

### Cloudflare Workers

- Workers Free 与 Containers 定价：https://developers.cloudflare.com/workers/platform/pricing/
- Workers 限额：https://developers.cloudflare.com/workers/platform/limits/
- Containers（仅 Workers Paid）：https://developers.cloudflare.com/containers/
- Worker Custom Domain 与自动证书：https://developers.cloudflare.com/workers/configuration/routing/custom-domains/

### FastAPI

- CORS、中间件和显式 origin 要求：https://fastapi.tiangolo.com/tutorial/cors/

## 资料边界

- “免费”只指本文件所列官方额度和价格页面在调查日的公开表述；配额、可用区容量、风控规则、税费和功能资格会变化，实施前必须再次核验对应官方页面。
- 未将域名注册费用计为平台免费额度；所有自定义域名都需已有可控制 DNS 的域名。
- 没有官方来源明确承诺的绑卡条件，本文标为“未明确”，而不是推断为“无需绑卡”。
- 本文件不构成生命安全生产部署批准。EVEREST-MHEWS 的告警、数据库备份、数据质量与多区域故障恢复应按生产风险单独评估。
