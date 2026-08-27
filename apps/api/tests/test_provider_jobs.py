"""Deterministic scheduler provider-job tests without network access."""

# Fakes are intentionally tiny and test names carry their behavioral contract.
# pylint: disable=missing-class-docstring,missing-function-docstring
# pylint: disable=too-few-public-methods

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import xarray as xr

from services.weather.retrieval import RetrievedArtifact
from everest_api.scheduler import ProviderRunResult
from everest_api.scheduler.provider_jobs import (
    GFS_SURFACE_INVENTORY,
    ProviderJobConfigurationError,
    _materialize_gfs_wind_field,  # pylint: disable=protected-access
    _resolved_herbie_source,  # pylint: disable=protected-access
    create_aifs_job,
    create_gfs_job,
    create_icon_job,
)


CYCLE = datetime(2026, 8, 27, 12, tzinfo=UTC)


def test_resolved_herbie_source_uses_matching_public_source_fields() -> None:
    """Herbie 2026.x exposes concrete sources as grib_source/idx_source."""
    assert (
        _resolved_herbie_source(
            SimpleNamespace(grib_source="AWS", idx_source="aws")
        )
        == "aws"
    )
    assert (
        _resolved_herbie_source(
            SimpleNamespace(grib_source="aws", idx_source="nomads")
        )
        is None
    )


class _CaptureService:
    def __init__(self) -> None:
        self.calls = []

    def ingest(self, descriptor, records):
        self.calls.append((descriptor, tuple(records)))
        return "ingested"


def _weather(source: str, model: str, lead: int = 0):
    return SimpleNamespace(
        record_type=SimpleNamespace(value="forecast"),
        source=source,
        model=model,
        timestamp=CYCLE,
        latitude=27.9,
        longitude=86.9,
        altitude=6000.0,
        quality_flags=frozenset(("clean",)),
        wind_speed=10.0,
        wind_direction=270.0,
        temperature=-20.0,
        precipitation=0.0,
        visibility=None,
        pressure=None,
        relative_humidity=None,
        dew_point=None,
        cloud_cover=None,
        cloud_base=None,
        cloud_top=None,
        snowfall=None,
        gust_speed=None,
        forecast=SimpleNamespace(cycle=CYCLE, lead_time=timedelta(hours=lead)),
    )


def test_gfs_job_uses_surface_inventory_and_preserves_identity(
    tmp_path: Path, monkeypatch
):
    """Without a derived root, GFS performs only the point-data retrieval."""
    monkeypatch.delenv("EVEREST_WIND_FIELD_DERIVED_ROOT", raising=False)
    service = _CaptureService()
    requests = []

    class FakeClient:
        source_priority = ("aws", "google", "nomads")
        resolved_source = "aws"

        def retrieve(self, request):
            requests.append(request)
            request.target_dir.mkdir(parents=True, exist_ok=True)
            path = request.target_dir / f"gfs-{request.lead_hours}.grib2"
            path.write_bytes(b"GRIB")
            return RetrievedArtifact.from_path(path, "noaa-gfs", request)

    adapter_calls = []
    adapter = SimpleNamespace(
        ingest=lambda raw, records: adapter_calls.append((raw, tuple(records)))
    )
    job = create_gfs_job(
        service,
        tmp_path,
        client_factory=FakeClient,
        parser=lambda _payload: (SimpleNamespace(),),
        normalizer=lambda *_args: _weather("noaa-gfs", "GFS"),
        adapter_factory=lambda _service: adapter,
        now=lambda: CYCLE,
        leads=(0,),
    )

    assert job() == 1
    assert len(requests) == 1
    assert requests[0].variables == GFS_SURFACE_INVENTORY
    raw, records = adapter_calls[0]
    assert (raw.source_id, raw.model) == ("noaa-gfs", "GFS")
    assert (records[0].weather.source, records[0].weather.model) == (
        "noaa-gfs",
        "GFS",
    )


def test_gfs_job_rejects_non_official_resolved_herbie_source(tmp_path: Path):
    class FakeClient:
        source_priority = ("aws", "google", "nomads")
        resolved_source = "community-mirror"

        def retrieve(self, _request):
            raise AssertionError("source must be rejected before parsing")

    job = create_gfs_job(
        object(), tmp_path, client_factory=FakeClient, now=lambda: CYCLE
    )

    with pytest.raises(ProviderJobConfigurationError, match="Herbie source"):
        job()


def test_gfs_job_reports_partial_lead_failure_and_keeps_count(tmp_path: Path):
    """A failed later lead degrades the run without erasing lead-zero work."""

    class FakeClient:
        source_priority = ("aws", "google", "nomads")
        resolved_source = "aws"

        def retrieve(self, request):
            if request.lead_hours == 3:
                raise TimeoutError("lead unavailable")
            request.target_dir.mkdir(parents=True, exist_ok=True)
            path = request.target_dir / "gfs-0.grib2"
            path.write_bytes(b"GRIB")
            return RetrievedArtifact.from_path(path, "noaa-gfs", request)

    adapter = SimpleNamespace(ingest=lambda *_args: None)
    result = create_gfs_job(
        object(),
        tmp_path,
        client_factory=FakeClient,
        parser=lambda _payload: (SimpleNamespace(),),
        normalizer=lambda *_args: _weather("noaa-gfs", "GFS"),
        adapter_factory=lambda _service: adapter,
        now=lambda: CYCLE,
        leads=(0, 3),
    )()

    assert isinstance(result, ProviderRunResult)
    assert result.records_ingested == 1
    assert result.failed_leads[0].lead_hours == 3
    assert result.failed_leads[0].failure_code == "TimeoutError"
    assert result.failed_leads[0].failure_detail == "lead unavailable"


def test_aifs_job_builds_safe_descriptor_with_aifs_identity(tmp_path: Path):
    service = _CaptureService()

    class FakeClient:
        def retrieve(self, request):
            request.target_dir.mkdir(parents=True, exist_ok=True)
            path = request.target_dir / "aifs.grib2"
            path.write_bytes(b"GRIB")
            return RetrievedArtifact.from_path(path, "ecmwf-aifs", request)

    message = SimpleNamespace()
    weather = _weather("ecmwf-aifs", "AIFS")
    job = create_aifs_job(
        service,
        tmp_path,
        client_factory=FakeClient,
        parser=lambda _payload: (message,),
        normalizer=lambda *_args: weather,
        spatial_key_factory=lambda _message, _index: "aifs:grid:0",
        nearest_index=lambda *_args: 0,
        now=lambda: CYCLE,
        leads=(0,),
    )

    assert job() == 1
    descriptor, records = service.calls[0]
    assert descriptor.source_id == "ecmwf-aifs"
    assert descriptor.metadata["provider_model"] == "AIFS"
    assert (records[0].source, records[0].model) == ("ecmwf-aifs", "AIFS")


def test_icon_job_uses_connector_and_adapter_with_icon_identity(tmp_path: Path):
    retrieval = SimpleNamespace(payload_path=tmp_path / "icon.grib2")
    retrieval.payload_path.write_bytes(b"GRIB")
    adapter_calls = []
    adapter = SimpleNamespace(
        ingest=lambda raw, records: adapter_calls.append((raw, tuple(records)))
    )

    class FakeConnector:
        def retrieve(self, cycle, lead_hours):
            assert cycle == CYCLE
            assert lead_hours == 0
            return retrieval

    job = create_icon_job(
        object(),
        connector_factory=FakeConnector,
        parser=lambda _payload: (SimpleNamespace(),),
        normalizer=lambda *_args: SimpleNamespace(
            weather=_weather("dwd-icon", "ICON"), spatial_key="icon:grid:0"
        ),
        raw_metadata_factory=lambda _retrieval: SimpleNamespace(
            source_id="dwd-icon", model="ICON"
        ),
        adapter_factory=lambda _service: adapter,
        now=lambda: CYCLE,
        leads=(0,),
    )

    assert job() == 1
    raw, records = adapter_calls[0]
    assert (raw.source_id, raw.model) == ("dwd-icon", "ICON")
    assert (records[0].weather.source, records[0].weather.model) == (
        "dwd-icon",
        "ICON",
    )


def test_materialize_gfs_wind_field_clips_regional_aoi(
    tmp_path: Path,
) -> None:
    """A retained GFS isobaric U/V artifact becomes a regional grid frame."""
    captured: dict[str, object] = {}
    dataset = xr.Dataset(
        {
            "u": (
                ("latitude", "longitude"),
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
            ),
            "v": (
                ("latitude", "longitude"),
                [[-1.0, -2.0, -3.0], [-4.0, -5.0, -6.0], [-7.0, -8.0, -9.0]],
            ),
        },
        coords={
            "latitude": [29.0, 28.0, 27.0],
            "longitude": [85.0, 87.0, 89.0],
        },
    )

    def _open(path, **kwargs):
        captured["path"] = path
        captured["kwargs"] = kwargs
        return dataset

    artifact = tmp_path / "gfs-wind.grib2"
    artifact.write_bytes(b"GRIB fixture")
    cycle = datetime(2026, 8, 27, 0, tzinfo=UTC)

    target = _materialize_gfs_wind_field(  # pylint: disable=protected-access
        artifact,
        cycle,
        6,
        derived_root=tmp_path / "derived",
        raw_root=tmp_path / "raw",
        opener=_open,
    )

    assert target is not None
    assert captured["path"] == artifact
    backend = captured["kwargs"]["backend_kwargs"]
    assert backend == {
        "indexpath": "",
        "filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": 400},
        "cache_geo_coords": False,
    }
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["source"] == "noaa-gfs"
    assert payload["model"] == "GFS"
    assert payload["latitude"] == [28.0]
    assert payload["longitude"] == [87.0]
    assert payload["u"] == [5.0]
    assert payload["v"] == [-5.0]
    assert payload["valid_time"] == "2026-08-27T06:00:00Z"
    assert payload["bounds"] == {
        "west": 86.4,
        "south": 27.5,
        "east": 87.4,
        "north": 28.5,
    }


def test_materialize_gfs_wind_field_is_disabled_without_root(
    tmp_path: Path, monkeypatch
) -> None:
    """A missing derived root leaves the point ingestion untouched."""
    monkeypatch.delenv("EVEREST_WIND_FIELD_DERIVED_ROOT", raising=False)
    assert (
        _materialize_gfs_wind_field(  # pylint: disable=protected-access
            tmp_path / "unused.grib2",
            datetime(2026, 8, 27, tzinfo=UTC),
            0,
        )
        is None
    )
