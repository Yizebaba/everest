FROM node:22-bookworm-slim AS dependencies

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:22-bookworm-slim AS builder

WORKDIR /app
ARG NEXT_PUBLIC_EVEREST_API_BASE_URL=http://localhost:52147
ARG NEXT_PUBLIC_CESIUM_ION_TOKEN=
ENV NEXT_PUBLIC_EVEREST_API_BASE_URL=${NEXT_PUBLIC_EVEREST_API_BASE_URL} \
    NEXT_PUBLIC_CESIUM_ION_TOKEN=${NEXT_PUBLIC_CESIUM_ION_TOKEN} \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=dependencies /app/node_modules ./node_modules
COPY apps/web/ ./

# CESIUM_BASE_URL points at /cesium/. Generate those public assets from the
# exact locked npm dependency instead of relying on ignored local copies.
RUN mkdir -p public/cesium \
    && cp -R node_modules/cesium/Build/Cesium/Workers public/cesium/ \
    && cp -R node_modules/cesium/Build/Cesium/ThirdParty public/cesium/ \
    && cp -R node_modules/cesium/Build/Cesium/Assets public/cesium/ \
    && cp -R node_modules/cesium/Build/Cesium/Widgets public/cesium/ \
    && npm run build \
    && npm prune --omit=dev

FROM node:22-bookworm-slim AS runner

ARG NEXT_PUBLIC_EVEREST_API_BASE_URL=http://localhost:52147
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    NEXT_PUBLIC_EVEREST_API_BASE_URL=${NEXT_PUBLIC_EVEREST_API_BASE_URL}

WORKDIR /app
COPY --from=builder --chown=node:node /app/package.json /app/package-lock.json ./
COPY --from=builder --chown=node:node /app/next.config.mjs ./
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/.next ./.next
COPY --from=builder --chown=node:node /app/public ./public

USER node
EXPOSE 52148

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:52148/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

CMD ["npm", "start"]
