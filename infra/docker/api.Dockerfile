FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/mnt/d/Everest

RUN groupadd --gid 10001 everest \
    && useradd --uid 10001 --gid everest --create-home everest

WORKDIR /mnt/d/Everest

COPY --chown=everest:everest packages/weather_ingestion_contract/ \
    packages/weather_ingestion_contract/
COPY --chown=everest:everest apps/api/ apps/api/
COPY --chown=everest:everest services/ services/

RUN python -m pip install --no-cache-dir \
    ./packages/weather_ingestion_contract ./apps/api

USER everest

EXPOSE 52147

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:52147/healthz', timeout=3).read()"]

CMD ["python", "apps/api/run_dev.py"]
