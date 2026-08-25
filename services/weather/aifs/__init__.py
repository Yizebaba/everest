"""Independent ECMWF AIFS Single connector, parser, normalizer, and adapter."""

from services.weather.aifs.connector import EcmwfAifsConnector
from services.weather.aifs.ingestion import (
    AifsCanonicalRecord,
    AifsIngestionAdapter,
    AifsRawRetentionMetadata,
    aifs_raw_retention_metadata_from_artifact,
    aifs_raw_retention_metadata_from_retrieval,
    compose_aifs_ingestion_adapter,
)
from services.weather.aifs.normalizer import (
    AifsQualityEvidence,
    normalize_messages,
    provider_spatial_key,
)
from services.weather.aifs.parser import (
    parse_grib_bytes,
    validate_decoded_inventory,
)

__all__ = [
    "AifsCanonicalRecord",
    "AifsIngestionAdapter",
    "AifsRawRetentionMetadata",
    "AifsQualityEvidence",
    "EcmwfAifsConnector",
    "aifs_raw_retention_metadata_from_artifact",
    "aifs_raw_retention_metadata_from_retrieval",
    "compose_aifs_ingestion_adapter",
    "normalize_messages",
    "parse_grib_bytes",
    "provider_spatial_key",
    "validate_decoded_inventory",
]
