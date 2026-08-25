"""Deterministic AIFS connector, parser, normalizer, and adapter tests."""

# Tests intentionally probe connector-private integrity and range boundaries.
# pylint: disable=duplicate-code,protected-access,too-few-public-methods

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import hashlib
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pytest
import requests

from weather_ingestion_contract import (
    CanonicalRecordInput,
    RawArtifactDescriptor,
)
from services.weather.aifs import (
    AifsCanonicalRecord,
    AifsQualityEvidence,
    EcmwfAifsConnector,
    aifs_raw_retention_metadata_from_retrieval,
    compose_aifs_ingestion_adapter,
    normalize_messages,
    provider_spatial_key,
    validate_decoded_inventory,
)
from services.weather.aifs.connector import RawRetrieval
from services.weather.aifs.parser import ParsedMessage, parse_grib_bytes


class FakeResponse:
    """Controllable requests-compatible response."""

    def __init__(
        self,
        status: int = 200,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status
        self.content = content
        self.headers = headers or {}
        self.text = text

    def raise_for_status(self) -> None:
        """Raise on configured HTTP errors."""
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class FakeSession:
    """Return queued transport outcomes and capture calls."""

    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        """Return or raise the next queued outcome."""
        self.calls.append((url, kwargs))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakePort:
    """Capture owner-neutral ingestion commands."""

    def __init__(self) -> None:
        self.calls: list[
            tuple[RawArtifactDescriptor, tuple[CanonicalRecordInput, ...]]
        ] = []

    def ingest(
        self,
        artifact: RawArtifactDescriptor,
        records: tuple[CanonicalRecordInput, ...],
    ) -> UUID:
        """Capture exactly one adapter invocation."""
        self.calls.append((artifact, records))
        return UUID("12345678-1234-5678-1234-567812345678")


def _message(parameter: str, value: float, units: str) -> ParsedMessage:
    """Create one AIFS Single v2 regular-grid message fixture."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    levels = {
        "z": ("surface", 0.0),
        "10u": ("heightAboveGround", 10.0),
        "10v": ("heightAboveGround", 10.0),
        "2t": ("heightAboveGround", 2.0),
        "tp": ("surface", 0.0),
    }
    level_type, level = levels.get(parameter, ("surface", 0.0))
    return ParsedMessage(
        parameter=parameter,
        valid_time=cycle + timedelta(hours=6),
        cycle=cycle,
        lead_hours=6,
        values=(value, value + 1),
        latitudes=(28.0, 27.75),
        longitudes=(87.0, 86.75),
        units=units,
        level_type=level_type,
        level=level,
        grid_type="regular_ll",
        ni=2,
        nj=1,
        generating_process_identifier=5,
    )


def _messages(tp_units: str = "kg m**-2") -> tuple[ParsedMessage, ...]:
    """Return a complete explicit-unit AIFS field set."""
    return (
        _message("z", 6000 * 9.80665, "m**2 s**-2"),
        _message("10u", 3.0, "m s**-1"),
        _message("10v", 4.0, "m s**-1"),
        _message("2t", 265.15, "K"),
        _message("tp", 1.2, tp_units),
    )


def test_urls_keep_aifs_identity_separate_from_ifs(tmp_path: Path) -> None:
    """AIFS uses its independent official model path and filename."""
    connector = EcmwfAifsConnector(test_raw_root=tmp_path)
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    url, index, _ = connector._urls(cycle, 6)
    assert "/aifs-single/0p25/oper/" in url
    assert "/ifs/" not in url
    assert index.endswith("-6h-oper-fc.index")


def test_index_selection_requires_unique_aifs_surface_identity() -> None:
    """Range selection rejects provider/model identity ambiguity."""
    row = {
        "param": "2t",
        "levtype": "sfc",
        "model": "aifs-single",
        "class": "ai",
        "stream": "oper",
        "type": "fc",
        "_offset": 10,
        "_length": 224,
    }
    assert EcmwfAifsConnector._selected_ranges([row], ("2t",)) == [row]
    with pytest.raises(ValueError, match="exactly one"):
        EcmwfAifsConnector._selected_ranges([{**row, "model": "ifs"}], ("2t",))


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(200, b"ab"),
        FakeResponse(206, b"ab"),
        FakeResponse(206, b"a", {"Content-Range": "bytes 0-1/10"}),
    ],
)
def test_range_rejects_full_malformed_and_truncated_responses(
    tmp_path: Path, response: FakeResponse
) -> None:
    """Only exact HTTP 206 range semantics can cross acquisition."""
    connector = EcmwfAifsConnector(
        FakeSession([response]), test_raw_root=tmp_path
    )
    with pytest.raises(ValueError):
        connector._range("https://data.ecmwf.int/test", 0, 2)


def test_range_accepts_exact_partial_response(tmp_path: Path) -> None:
    """Exact HTTP 206 Content-Range and length return selected bytes."""
    response = FakeResponse(206, b"ab", {"Content-Range": "bytes 3-4/100"})
    connector = EcmwfAifsConnector(
        FakeSession([response]), test_raw_root=tmp_path
    )
    assert connector._range("https://data.ecmwf.int/test", 3, 2) == b"ab"


def test_retry_is_bounded_and_has_no_wall_clock_sleep(tmp_path: Path) -> None:
    """One transient error invokes deterministic backoff then succeeds."""
    session = FakeSession([requests.Timeout("temporary"), FakeResponse()])
    delays: list[float] = []
    connector = EcmwfAifsConnector(
        session,
        retry_limit=1,
        backoff_seconds=0.25,
        sleep=delays.append,
        test_raw_root=tmp_path,
    )
    assert connector._request("https://data.ecmwf.int/test").status_code == 200
    assert len(session.calls) == 2
    assert delays == [0.25]


def test_retry_exhaustion_is_bounded(tmp_path: Path) -> None:
    """Transport exhaustion raises after the configured deterministic limit."""
    session = FakeSession(
        [requests.Timeout("first"), requests.Timeout("second")]
    )
    delays: list[float] = []
    connector = EcmwfAifsConnector(
        session,
        retry_limit=1,
        sleep=delays.append,
        test_raw_root=tmp_path,
    )
    with pytest.raises(requests.Timeout):
        connector._request("https://data.ecmwf.int/test")
    assert len(session.calls) == 2
    assert delays == [1.0]


def test_http_429_uses_bounded_delta_retry_after(tmp_path: Path) -> None:
    """HTTP 429 uses the valid provider delay, not exponential backoff."""
    session = FakeSession(
        [FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse()]
    )
    delays: list[float] = []
    connector = EcmwfAifsConnector(
        session,
        retry_limit=1,
        backoff_seconds=99,
        sleep=delays.append,
        test_raw_root=tmp_path,
    )
    assert connector._request("https://data.ecmwf.int/test").status_code == 200
    assert len(session.calls) == 2
    assert delays == [7.0]


def test_http_429_accepts_injected_retry_after_date(tmp_path: Path) -> None:
    """HTTP-date Retry-After is calculated against an injected UTC clock."""
    now = datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc)
    header = format_datetime(now + timedelta(minutes=1), usegmt=True)
    session = FakeSession(
        [FakeResponse(429, headers={"Retry-After": header}), FakeResponse()]
    )
    delays: list[float] = []
    connector = EcmwfAifsConnector(
        session,
        retry_limit=1,
        sleep=delays.append,
        now=lambda: now,
        test_raw_root=tmp_path,
    )
    connector._request("https://data.ecmwf.int/test")
    assert delays == [60.0]


@pytest.mark.parametrize("header", ["", "later", "-1", "1.5", "999"])
def test_http_429_rejects_malformed_or_excessive_retry_after(
    tmp_path: Path, header: str
) -> None:
    """Malformed and over-limit server delays are deterministic failures."""
    session = FakeSession(
        [FakeResponse(429, headers={"Retry-After": header})] * 3
    )
    connector = EcmwfAifsConnector(
        session, retry_limit=0, test_raw_root=tmp_path
    )
    with pytest.raises(ValueError, match="Retry-After"):
        connector._request("https://data.ecmwf.int/test")
    assert len(session.calls) == 1


def test_http_429_exhaustion_preserves_attempt_limit(tmp_path: Path) -> None:
    """Repeated 429 responses stop after the configured attempt count."""
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "1"}),
            FakeResponse(429, headers={"Retry-After": "2"}),
        ]
    )
    delays: list[float] = []
    connector = EcmwfAifsConnector(
        session, retry_limit=1, sleep=delays.append, test_raw_root=tmp_path
    )
    with pytest.raises(requests.HTTPError):
        connector._request("https://data.ecmwf.int/test")
    assert len(session.calls) == 2
    assert delays == [1.0]


def test_runtime_raw_root_is_required_and_external(tmp_path: Path) -> None:
    """Runtime cannot retain under an absent or repository-contained root."""
    repository = tmp_path / "repository"
    repository.mkdir()
    raw_inside = repository / "raw"
    raw_inside.mkdir()
    with pytest.raises(ValueError, match="must be configured"):
        EcmwfAifsConnector(environment={}, repository_root=repository.resolve())
    with pytest.raises(ValueError, match="outside"):
        EcmwfAifsConnector(
            environment={"EVEREST_RAW_ROOT": str(raw_inside.resolve())},
            repository_root=repository.resolve(),
        )


def test_metadata_integrity_rejects_payload_and_sidecar_tamper(
    tmp_path: Path,
) -> None:
    """Retention reuse never silently accepts changed immutable bytes."""
    connector = EcmwfAifsConnector(test_raw_root=tmp_path)
    path = tmp_path / "metadata.json"
    metadata = {"source": "ecmwf-aifs", "model": "AIFS"}
    connector._write_metadata(path, metadata)
    connector._write_metadata(
        path, {**metadata, "retrieved_at": "later factual retry"}
    )
    path.chmod(0o644)
    path.write_bytes(b'{"model":"IFS","source":"ecmwf-aifs"}\n')
    with pytest.raises(ValueError, match="sidecar|provenance"):
        connector._write_metadata(path, metadata)


def test_normalizer_preserves_aifs_model_and_provider_spatial_key() -> None:
    """Keep AIFS identity, units, QC, values, and native grid key explicit."""
    messages = _messages()
    record = normalize_messages(messages, 27.98806, 86.92528)
    index = 0
    assert record.source == "ecmwf-aifs"
    assert record.model == "AIFS"
    assert record.altitude == 6000.0
    assert record.temperature == -8.0
    assert record.wind_speed == 5.0
    assert record.precipitation == 1.2
    assert record.latitude == 28.0
    assert record.longitude == 87.0
    assert "missing_value" in record.quality_flags
    assert provider_spatial_key(messages[0], index) == (
        "aifs-single:0p25:2x1:0"
    )


def test_normalizer_flags_invalid_native_unit_without_guessing() -> None:
    """AIFS WMO-unit mismatch yields null canonical value and additive QC."""
    record = normalize_messages(_messages("m"), 27.98806, 86.92528)
    assert record.precipitation is None
    assert "invalid_unit" in record.quality_flags


@pytest.mark.parametrize(
    ("messages", "detail"),
    [
        (lambda: (*_messages(), _messages()[0]), "duplicates"),
        (lambda: _messages()[:-1], "missing"),
        (
            lambda: (*_messages(), _message("msl", 100000.0, "Pa")),
            "unexpected",
        ),
    ],
)
def test_inventory_rejects_duplicate_missing_and_unexpected(
    messages, detail: str
) -> None:
    """Decoded inventory must contain each approved field exactly once."""
    with pytest.raises(ValueError, match=detail):
        validate_decoded_inventory(tuple(messages()))


def test_inventory_rejects_parameter_at_wrong_native_level() -> None:
    """A 10 metre wind encoded at the surface cannot enter normalization."""
    wrong = replace(_messages()[1], level_type="surface", level=0.0)
    with pytest.raises(ValueError, match="level mismatch for 10u"):
        validate_decoded_inventory((_messages()[0], wrong, *_messages()[2:]))


def test_source_specific_qc_flags_evidence_without_deleting_record() -> None:
    """Source/checksum/inventory, stale, and duplicate evidence is additive."""
    record = normalize_messages(
        _messages(),
        27.98806,
        86.92528,
        AifsQualityEvidence(
            source_identity_valid=False,
            checksum_valid=False,
            inventory_valid=False,
            stale=True,
            duplicate=True,
        ),
    )
    assert record.altitude == 6000.0
    assert {
        "provenance_error",
        "stale",
        "duplicate",
    }.issubset(record.quality_flags)


def _retrieval(tmp_path: Path) -> RawRetrieval:
    """Create exact connector-shaped retained files for adapter conversion."""
    cycle = datetime(2026, 8, 21, tzinfo=timezone.utc)
    connector = EcmwfAifsConnector(test_raw_root=tmp_path)
    os.environ["EVEREST_RAW_ROOT"] = str(tmp_path)
    payload = b"GRIB retained AIFS"
    digest = hashlib.sha256(payload).hexdigest()
    artifact = tmp_path / "ecmwf-aifs" / digest
    artifact.mkdir(parents=True)
    payload_path = artifact / "sample.grib2"
    payload_path.write_bytes(payload)
    url = "https://data.ecmwf.int/forecasts/sample.grib2"
    index_url = "https://data.ecmwf.int/forecasts/sample.index"
    metadata = connector._metadata(
        cycle,
        6,
        url,
        index_url,
        [
            {"param": name, "_offset": offset, "_length": length}
            for offset, (name, length) in zip(
                (0, 4, 7, 10, 13),
                (("z", 4), ("10u", 3), ("10v", 3), ("2t", 3), ("tp", 5)),
            )
        ],
        payload,
        digest,
    )
    metadata["retrieved_at"] = "2026-08-21T01:02:03+00:00"
    metadata_path = artifact / "metadata.json"
    connector._write_metadata(metadata_path, metadata)
    return RawRetrieval(
        payload_path,
        metadata_path,
        url,
        index_url,
        digest,
        len(payload),
        cycle,
        6,
        ("z", "10u", "10v", "2t", "tp"),
    )


def _convert_retrieval(
    retrieval: RawRetrieval,
    messages: tuple[ParsedMessage, ...] | None = None,
):
    """Convert synthetic bytes with one explicit parser result."""
    decoded = messages or _messages()
    with patch(
        "services.weather.aifs.ingestion.parse_grib_bytes",
        return_value=decoded,
    ):
        return aifs_raw_retention_metadata_from_retrieval(retrieval)


def test_connector_conversion_and_adapter_are_lossless(tmp_path: Path) -> None:
    """Exact retained descriptor crosses only the thin owner-neutral adapter."""
    raw = _convert_retrieval(_retrieval(tmp_path))
    weather = normalize_messages(_messages(), 27.98806, 86.92528)
    canonical = AifsCanonicalRecord(
        weather,
        provider_spatial_key(_messages()[0], 0),
    )
    port = FakePort()
    compose_aifs_ingestion_adapter(port).ingest(raw, (canonical,))
    descriptor, records = port.calls[0]
    assert descriptor.source_id == "ecmwf-aifs"
    assert descriptor.metadata["provider_model"] == "AIFS"
    assert descriptor.metadata["provider_decoded_inventory"] == (
        "z,10u,10v,2t,tp"
    )
    assert descriptor.metadata["provider_generating_process_identifier"] == 5
    assert descriptor.metadata["provider_decoded_level_bindings"] == (
        "z:surface:0,10u:heightAboveGround:10,"
        "10v:heightAboveGround:10,2t:heightAboveGround:2,tp:surface:0"
    )
    assert descriptor.metadata["provider_aoi_scope_id"].endswith("100km")
    assert records[0].model == "AIFS"
    assert records[0].spatial_key == "aifs-single:0p25:2x1:0"


@pytest.mark.parametrize("target", ("payload", "sidecar"))
def test_connector_conversion_rejects_integrity_tamper(
    tmp_path: Path, target: str
) -> None:
    """Payload and metadata declaration changes fail before adapter use."""
    retrieval = _retrieval(tmp_path)
    if target == "payload":
        retrieval.payload_path.write_bytes(b"GRIB changed AIFS")
    else:
        sidecar = retrieval.metadata_path.with_name("metadata.json.sha256")
        sidecar.chmod(0o644)
        sidecar.write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="integrity|sidecar"):
        _convert_retrieval(retrieval)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda messages: tuple(
                replace(item, cycle=item.cycle + timedelta(hours=6))
                for item in messages
            ),
            "cycle",
        ),
        (
            lambda messages: tuple(
                replace(item, lead_hours=12) for item in messages
            ),
            "lead",
        ),
        (
            lambda messages: tuple(
                replace(
                    item,
                    valid_time=item.valid_time + timedelta(hours=6),
                )
                for item in messages
            ),
            "valid time",
        ),
        (
            lambda messages: tuple(
                replace(item, generating_process_identifier=4)
                for item in messages
            ),
            "process",
        ),
    ],
)
def test_connector_conversion_rejects_decoded_metadata_mismatch(
    tmp_path: Path, mutator, message: str
) -> None:
    """Decoded run/process facts must match retained retrieval metadata."""
    messages = mutator(_messages())
    with pytest.raises(ValueError, match=message):
        _convert_retrieval(_retrieval(tmp_path), tuple(messages))


def test_connector_conversion_rejects_decoded_inventory_mismatch(
    tmp_path: Path,
) -> None:
    """Decoded inventory is bound to the connector-selected metadata list."""
    retrieval = replace(
        _retrieval(tmp_path), parameters=("tp", "2t", "10v", "10u", "z")
    )
    with pytest.raises(ValueError, match="inventory"):
        _convert_retrieval(retrieval)


def test_adapter_rejects_ifs_conflation_before_port(tmp_path: Path) -> None:
    """An IFS-labelled record can never enter the AIFS persistence command."""
    raw = _convert_retrieval(_retrieval(tmp_path))
    weather = replace(
        normalize_messages(_messages(), 27.98806, 86.92528), model="IFS"
    )
    port = FakePort()
    with pytest.raises(ValueError, match="identity"):
        compose_aifs_ingestion_adapter(port).ingest(
            raw,
            (
                AifsCanonicalRecord(
                    weather,
                    provider_spatial_key(_messages()[0], 0),
                ),
            ),
        )
    assert not port.calls


def test_parser_rejects_non_grib_payload() -> None:
    """Parser cannot invent AIFS messages from arbitrary bytes."""
    with pytest.raises(Exception):
        parse_grib_bytes(b"not GRIB2")


@pytest.mark.real_data
def test_retained_real_aifs_grib_semantics() -> None:
    """Lock factual retained AIFS v2 parse, grid selection, values, and QC."""
    configured = os.environ.get("AIFS_REAL_GRIB")
    if not configured:
        pytest.skip("AIFS_REAL_GRIB is required for retained real-data smoke")
    path = Path(configured)
    messages = parse_grib_bytes(path.read_bytes())
    record = normalize_messages(messages, 27.98806, 86.92528)
    index = 358188
    assert [message.parameter for message in messages] == [
        "z",
        "10u",
        "10v",
        "2t",
        "tp",
    ]
    assert {message.generating_process_identifier for message in messages} == {
        5
    }
    assert [
        (message.parameter, message.level_type, message.level)
        for message in messages
    ] == [
        ("z", "surface", 0.0),
        ("10u", "heightAboveGround", 10.0),
        ("10v", "heightAboveGround", 10.0),
        ("2t", "heightAboveGround", 2.0),
        ("tp", "surface", 0.0),
    ]
    assert messages[0].grid_type == "regular_ll"
    assert (messages[0].ni, messages[0].nj) == (1440, 721)
    assert (messages[0].latitudes[index], messages[0].longitudes[index]) == (
        28.0,
        87.0,
    )
    assert provider_spatial_key(messages[0], index) == (
        "aifs-single:0p25:1440x721:358188"
    )
    assert record.model == "AIFS"
    assert record.altitude == 5346.3264215561
    assert record.temperature == 0.45586547851564774
    assert record.wind_speed == 0.16091116689523915
    assert record.wind_direction == 86.4729776688032
    assert record.precipitation == 0.0
    assert record.visibility is None
    assert record.quality_flags == frozenset({"missing_value"})
    retrieval = RawRetrieval(
        payload_path=path,
        metadata_path=path.with_name("metadata.json"),
        url=(
            "https://data.ecmwf.int/forecasts/20260821/00z/"
            "aifs-single/0p25/oper/20260821000000-0h-oper-fc.grib2"
        ),
        index_url=(
            "https://data.ecmwf.int/forecasts/20260821/00z/"
            "aifs-single/0p25/oper/20260821000000-0h-oper-fc.index"
        ),
        sha256=(
            "46760ee149ee317f1c652595398be40a185a7c2c04a8ca29be46c4394d6edbe5"
        ),
        size_bytes=3_061_386,
        cycle=datetime(2026, 8, 21, tzinfo=timezone.utc),
        lead_hours=0,
        parameters=("z", "10u", "10v", "2t", "tp"),
    )
    os.environ["EVEREST_RAW_ROOT"] = str(path.parents[2])
    raw = aifs_raw_retention_metadata_from_retrieval(retrieval)
    assert raw.decoded_parameters == ("z", "10u", "10v", "2t", "tp")
    assert raw.decoded_process_identifier == 5
    assert raw.decoded_level_bindings == (
        "z:surface:0",
        "10u:heightAboveGround:10",
        "10v:heightAboveGround:10",
        "2t:heightAboveGround:2",
        "tp:surface:0",
    )


def test_adapter_source_has_no_backend_dependency() -> None:
    """AIFS adapter imports only the owner-neutral shared contract."""
    source = Path(__file__).parents[1] / "ingestion.py"
    text = source.read_text(encoding="utf-8")
    assert "everest_api" not in text
    assert "apps.api" not in text
    assert "weather_ingestion_contract" in text
