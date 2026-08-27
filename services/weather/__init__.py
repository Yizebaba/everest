"""Canonical weather contract package."""

from services.weather.aoi import (
    AreaOfInterest,
    normalize_longitude,
    subset_dataset,
)
from services.weather.contract import (
    ForecastIdentity,
    QualityFlag,
    RecordType,
    WeatherRecord,
    validate_record,
)
from services.weather.retrieval import (
    RetrievalRequest,
    RetrievedArtifact,
    open_grib_dataset,
)

__all__ = [
    "AreaOfInterest",
    "ForecastIdentity",
    "QualityFlag",
    "RecordType",
    "RetrievalRequest",
    "RetrievedArtifact",
    "WeatherRecord",
    "normalize_longitude",
    "open_grib_dataset",
    "subset_dataset",
    "validate_record",
]
