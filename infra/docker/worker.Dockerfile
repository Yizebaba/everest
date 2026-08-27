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
    ./packages/weather_ingestion_contract './apps/api[weather-ingestion]'

USER everest

CMD ["python", "apps/api/schedule_forecast.py"]
