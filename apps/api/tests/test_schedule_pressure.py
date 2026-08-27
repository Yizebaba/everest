"""Deterministic tests for the scheduler pressure-level ingestion path."""

# Test fakes import helpers inline to keep fixtures self-contained.
# pylint: disable=import-outside-toplevel,protected-access

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
import urllib.request

import pytest
import xarray as xr

from everest_api.scheduler import ProviderRunResult
import schedule_forecast as sched


def _pressure_record(cycle: datetime, lead: int) -> object:
    """Build a normalized pressure record for scheduler pipeline tests."""
    return SimpleNamespace(
        timestamp=cycle,
        latitude=28.0,
        longitude=87.0,
        altitude=7600.0,
        level_hpa=400,
        source="ecmwf-ifs",
        model="IFS",
        wind_speed=20.0,
        wind_direction=270.0,
        temperature_c=-30.0,
        cycle=cycle,
        lead_seconds=lead * 3600,
    )


def test_fetch_pressure_selects_expected_levels(monkeypatch) -> None:
    """_fetch_pressure builds range requests only for the configured levels."""
    import json

    index_rows = []
    for param in ("u", "v", "t", "gh"):
        for level in ("850", "700", "500", "300", "100"):
            index_rows.append(
                {
                    "param": param,
                    "levtype": "pl",
                    "levelist": level,
                    "_offset": len(index_rows) * 100,
                    "_length": 100,
                }
            )
    index_text = "\n".join(json.dumps(r) for r in index_rows)

    requested: list[tuple[str, str]] = []

    class _FakeResp:
        status = 206

        def __init__(self, body: bytes) -> None:
            self._body = body

        def read(self) -> bytes:
            """Return the fake response body."""
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _FakeIndex:
        def __init__(self, text: str) -> None:
            self._text = text

        def read(self) -> bytes:
            """Return the fake index text bytes."""
            return self._text.encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _urlopen(url, **_kwargs):
        target = getattr(url, "full_url", url)
        requested.append(target)
        if target.endswith(".index"):
            return _FakeIndex(index_text)
        # range response: echo 100 bytes
        return _FakeResp(b"x" * 100)

    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
    cycle = datetime(2026, 8, 24, 0, tzinfo=UTC)
    payload = sched._fetch_pressure(cycle)  # pylint: disable=protected-access

    # 4 levels x 4 params = 16 selected (100hPa excluded)
    assert len(payload) == 16 * 100
    # every selected range URL is the lead-0 file
    assert all(".grib2" in u or ".index" in u for u in requested)
    assert any(u.endswith(".index") for u in requested)


def test_pressure_cycle_url_uses_cycle_date_and_hour() -> None:
    """The pressure fetch URL is built from the cycle date/hour, lead 0."""
    from unittest.mock import patch

    cycle = datetime(2026, 8, 25, 12, tzinfo=UTC)
    captured: dict[str, str] = {}

    def _fake_urlopen(url, **_kwargs):
        captured["url"] = url
        raise RuntimeError("stop")

    with patch.object(urllib.request, "urlopen", _fake_urlopen):
        with pytest.raises(RuntimeError):
            sched._fetch_pressure(cycle)  # pylint: disable=protected-access
    assert "20260825" in captured["url"]
    assert "/12z/" in captured["url"]
    assert "20260825120000-0h-oper-fc" in captured["url"]


def test_materialize_wind_field_uses_real_aoi_grid(tmp_path: Path) -> None:
    """Retained 400 hPa U/V is clipped and published without interpolation."""
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

    artifact = tmp_path / "pressure.grib2"
    artifact.write_bytes(b"GRIB fixture")
    cycle = datetime(2026, 8, 27, 0, tzinfo=UTC)

    target = (
        sched._materialize_ifs_wind_field(  # pylint: disable=protected-access
            artifact,
            cycle,
            6,
            derived_root=tmp_path / "derived",
            opener=_open,
        )
    )

    assert target is not None
    assert captured["path"] == artifact
    backend = captured["kwargs"]["backend_kwargs"]
    assert backend == {
        "indexpath": "",
        "filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": 400},
    }
    payload = __import__("json").loads(target.read_text(encoding="utf-8"))
    assert payload["latitude"] == [28.0]
    assert payload["longitude"] == [87.0]
    assert payload["u"] == [5.0]
    assert payload["v"] == [-5.0]
    assert payload["valid_time"] == "2026-08-27T06:00:00Z"


def test_materialize_wind_field_is_disabled_without_root(
    tmp_path: Path, monkeypatch
) -> None:
    """Missing derived-root configuration leaves existing ingestion unchanged."""
    monkeypatch.delenv("EVEREST_WIND_FIELD_DERIVED_ROOT", raising=False)
    assert (
        sched._materialize_ifs_wind_field(  # pylint: disable=protected-access
            tmp_path / "unused.grib2",
            datetime(2026, 8, 27, tzinfo=UTC),
            0,
        )
        is None
    )


def test_future_wind_lead_does_not_replace_latest_pointer(
    tmp_path: Path,
) -> None:
    """All leads are stored, but latest remains aligned to cycle valid time."""
    dataset = xr.Dataset(
        {
            "u": (("latitude", "longitude"), [[5.0]]),
            "v": (("latitude", "longitude"), [[-5.0]]),
        },
        coords={"latitude": [28.0], "longitude": [87.0]},
    )
    artifact = tmp_path / "pressure.grib2"
    artifact.write_bytes(b"GRIB fixture")
    root = tmp_path / "derived"
    cycle = datetime(2026, 8, 27, 0, tzinfo=UTC)

    lead_zero = sched._materialize_ifs_wind_field(
        artifact, cycle, 0, derived_root=root, opener=lambda *_a, **_k: dataset
    )
    pointer_before = (root / "wind-field" / "latest.json").read_bytes()
    future = sched._materialize_ifs_wind_field(
        artifact, cycle, 6, derived_root=root, opener=lambda *_a, **_k: dataset
    )

    assert future != lead_zero
    assert future.is_file()
    assert (root / "wind-field" / "latest.json").read_bytes() == pointer_before


@pytest.mark.parametrize("failure_stage", ("parse", "ingest"))
def test_pressure_nonzero_pipeline_failure_keeps_success_and_degrades(
    monkeypatch, tmp_path: Path, failure_stage: str
) -> None:
    """Pressure parse and persistence failures are isolated after lead zero."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    parse_calls = 0

    def parse(payload):
        nonlocal parse_calls
        parse_calls += 1
        if failure_stage == "parse" and parse_calls == 2:
            raise ValueError("access_token=pressure-secret")
        return int(payload.decode())

    def normalize(lead, *_args):
        return [_pressure_record(cycle, lead)]

    ingest_calls = 0

    def ingest(*_args) -> None:
        nonlocal ingest_calls
        ingest_calls += 1
        if failure_stage == "ingest" and ingest_calls == 2:
            raise RuntimeError("password=pressure-secret")

    service = SimpleNamespace(ingest=ingest)
    monkeypatch.setattr(sched, "RAW_ROOT", tmp_path)
    monkeypatch.setattr(
        sched, "_fetch_pressure", lambda _cycle, lead: str(lead).encode()
    )
    monkeypatch.setattr(sched, "parse_pressure_messages", parse)
    monkeypatch.setattr(sched, "normalize_pressure_levels", normalize)
    monkeypatch.setattr(sched, "_pressure_quality_flags", lambda _record: ())
    monkeypatch.setattr(sched, "_ingest_route_profiles", lambda *_args: 0)
    monkeypatch.setattr(
        sched, "_materialize_ifs_wind_field", lambda *_args: None
    )

    result = sched._as_provider_result(
        sched._ingest_ifs_pressure(service, cycle, leads=(0, 6))
    )

    assert isinstance(result, ProviderRunResult)
    assert result.records_ingested == 1
    assert result.failed_leads[0].lead_hours == 6
    assert "secret" not in result.failed_leads[0].failure_detail


def test_pressure_lead_zero_pipeline_failure_signals_cycle_fallback(
    monkeypatch,
) -> None:
    """A complete pressure lead-zero parse failure remains exceptional."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    monkeypatch.setattr(sched, "_fetch_pressure", lambda *_args: b"bad")
    monkeypatch.setattr(
        sched,
        "parse_pressure_messages",
        lambda _payload: (_ for _ in ()).throw(ValueError("bad lead zero")),
    )

    with pytest.raises(ValueError, match="bad lead zero"):
        sched._ingest_ifs_pressure(SimpleNamespace(), cycle, leads=(0,))
