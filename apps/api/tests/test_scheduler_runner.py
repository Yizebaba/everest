"""One-pass scheduler orchestration tests with no provider network access."""

# The two protected-access calls directly verify the standalone script's IFS
# compatibility wrapper; it is intentionally not part of the package API.
# pylint: disable=protected-access

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from everest_api.scheduler import (
    FailedLead,
    ProviderJob,
    ProviderRunResult,
    RunStatus,
    SchedulerConfig,
    run_once,
)
from everest_api.scheduler.recording import DataSourceRunRecorder
import schedule_forecast


def _surface_record(cycle: datetime, lead: int) -> SimpleNamespace:
    """Build the smallest normalized IFS surface record used by scheduler tests."""
    return SimpleNamespace(
        record_type=SimpleNamespace(value="forecast"),
        timestamp=cycle + timedelta(hours=lead),
        latitude=28.0,
        longitude=87.0,
        altitude=6000.0,
        source="ecmwf-ifs",
        model="IFS",
        quality_flags=("clean",),
        wind_speed=10.0,
        wind_direction=270.0,
        temperature=-20.0,
        precipitation=0.0,
        visibility=None,
        forecast=SimpleNamespace(cycle=cycle, lead_time=timedelta(hours=lead)),
    )


def _surface_retrieval(tmp_path: Path, cycle: datetime, lead: int):
    """Create one retained retrieval result with deterministic metadata."""
    payload_path = tmp_path / f"surface-{lead}.grib2"
    payload_path.write_bytes(str(lead).encode())
    return SimpleNamespace(
        payload_path=payload_path,
        checksum_sha256=f"sha-{lead}",
        cycle=cycle,
        size_bytes=payload_path.stat().st_size,
    )


class _FakeSession:
    """Minimal context-managed session for recorder state-transition tests."""

    def __init__(self, source, added=None) -> None:
        self.source = source
        self.added = [] if added is None else added

    def __enter__(self):
        """Return this fake session."""
        return self

    def __exit__(self, *_args):
        """Do not suppress test exceptions."""
        return False

    def get(self, _model, source_id):
        """Return the configured source for its stable id."""
        return self.source if source_id == "ecmwf-ifs" else None

    def add(self, row):
        """Capture one added model."""
        self.added.append(row)

    def commit(self):
        """Represent a successful no-op commit."""
        return None


def test_partial_failure_is_degraded_and_keeps_independent_counts() -> None:
    """One provider failure does not erase another provider's success."""
    calls: list[str] = []

    def succeeds() -> int:
        calls.append("ifs")
        return 17

    def fails() -> int:
        calls.append("gfs")
        raise RuntimeError("provider unavailable")

    result = run_once(
        (
            ProviderJob("ecmwf-ifs", succeeds),
            ProviderJob("noaa-gfs", fails),
        )
    )

    assert result.status is RunStatus.DEGRADED
    assert result.succeeded_sources == ("ecmwf-ifs",)
    assert result.failed_sources == ("noaa-gfs",)
    assert result.records_ingested == 17
    assert calls == ["ifs", "gfs"]


def test_partial_lead_failure_is_explicit_provider_degradation() -> None:
    """A provider keeps successful records and exposes failed lead details."""
    result = run_once(
        (
            ProviderJob(
                "ecmwf-aifs",
                lambda: ProviderRunResult(
                    records_ingested=2,
                    failed_leads=(
                        FailedLead(6, "TimeoutError", "lead timed out"),
                    ),
                ),
            ),
        )
    )

    assert result.status is RunStatus.DEGRADED
    assert result.records_ingested == 2
    assert not result.succeeded_sources
    assert result.degraded_sources == ("ecmwf-aifs",)
    assert result.outcomes[0].outcome == "degraded"
    assert result.outcomes[0].failed_leads[0].lead_hours == 6


def test_all_enabled_failures_produce_failure_without_all_source_claim() -> (
    None
):
    """The result names only attempted sources and never claims global coverage."""

    def fails() -> int:
        raise ValueError("not published")

    result = run_once(
        (
            ProviderJob("ecmwf-ifs", fails),
            ProviderJob("noaa-gfs", lambda: 99, enabled=False),
            ProviderJob("ecmwf-aifs", lambda: 99, enabled=False),
        )
    )

    assert result.status is RunStatus.FAILURE
    assert result.attempted_sources == ("ecmwf-ifs",)
    assert result.skipped_sources == ("noaa-gfs", "ecmwf-aifs")
    assert not result.succeeded_sources


def test_success_requires_every_enabled_provider_to_succeed() -> None:
    """A successful pass reports its exact enabled source set and total count."""
    result = run_once(
        (
            ProviderJob("ecmwf-ifs", lambda: 3),
            ProviderJob("dwd-icon", lambda: 4),
        )
    )

    assert result.status is RunStatus.SUCCESS
    assert result.attempted_sources == ("ecmwf-ifs", "dwd-icon")
    assert result.records_ingested == 7


def test_recorder_receives_one_terminal_outcome_per_attempt() -> None:
    """Run recording is isolated behind a callable extension seam."""
    recorded = []

    result = run_once(
        (
            ProviderJob("ecmwf-ifs", lambda: 2),
            ProviderJob(
                "noaa-gfs",
                lambda: (_ for _ in ()).throw(RuntimeError("down")),
            ),
        ),
        recorder=recorded.append,
    )

    assert result.status is RunStatus.DEGRADED
    assert [(item.source_id, item.outcome) for item in recorded] == [
        ("ecmwf-ifs", "succeeded"),
        ("noaa-gfs", "failed"),
    ]
    assert all(item.finished_at >= item.started_at for item in recorded)


def test_optional_sources_are_disabled_by_default() -> None:
    """Configuration does not represent GFS, AIFS, or ICON as live by default."""
    config = SchedulerConfig.from_environment({})

    assert config.ifs_enabled
    assert not config.gfs_enabled
    assert not config.aifs_enabled
    assert not config.icon_enabled


def test_build_provider_jobs_only_executes_enabled_real_factories(
    monkeypatch,
) -> None:
    """Enabled optional jobs are concrete lazy factories; disabled ones do not run."""
    calls: list[str] = []

    monkeypatch.setattr(
        schedule_forecast,
        "create_gfs_job",
        lambda *_args, **_kwargs: lambda: calls.append("gfs") or 2,
        raising=False,
    )
    monkeypatch.setattr(
        schedule_forecast,
        "create_aifs_job",
        lambda *_args, **_kwargs: lambda: calls.append("aifs") or 3,
        raising=False,
    )
    monkeypatch.setattr(
        schedule_forecast,
        "create_icon_job",
        lambda *_args, **_kwargs: lambda: calls.append("icon") or 4,
        raising=False,
    )
    config = SchedulerConfig(
        ifs_enabled=False,
        gfs_enabled=True,
        aifs_enabled=False,
        icon_enabled=True,
    )

    jobs = schedule_forecast.build_provider_jobs(config, lambda: 1, object())
    result = run_once(jobs)

    assert result.status is RunStatus.SUCCESS
    assert result.records_ingested == 6
    assert calls == ["gfs", "icon"]


def test_failure_detail_is_bounded_and_redacted() -> None:
    """Provider failure accounting cannot persist an obvious credential value."""

    def fails() -> int:
        raise RuntimeError("access_token=do-not-store")

    result = run_once((ProviderJob("ecmwf-ifs", fails),))

    assert result.outcomes[0].failure_detail == "access_token=[REDACTED]"


@pytest.mark.parametrize("failure_stage", ("parse", "ingest"))
def test_surface_nonzero_pipeline_failure_keeps_success_and_degrades(
    monkeypatch, tmp_path: Path, failure_stage: str
) -> None:
    """Parse and persistence failures after lead zero are bounded per lead."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)

    connector = SimpleNamespace(
        retrieve=lambda requested_cycle, lead_hours: _surface_retrieval(
            tmp_path, requested_cycle, lead_hours
        )
    )

    parse_calls = 0

    def parse(payload):
        nonlocal parse_calls
        parse_calls += 1
        if failure_stage == "parse" and parse_calls == 2:
            raise ValueError("access_token=surface-secret")
        return int(payload.decode())

    def normalize(lead, *_args):
        return _surface_record(cycle, lead)

    ingest_calls = 0

    def ingest(*_args) -> None:
        nonlocal ingest_calls
        ingest_calls += 1
        if failure_stage == "ingest" and ingest_calls == 2:
            raise RuntimeError("password=surface-secret")

    service = SimpleNamespace(ingest=ingest)
    monkeypatch.setattr(schedule_forecast, "LEADS_IFS", [0, 3])
    monkeypatch.setattr(
        schedule_forecast, "EcmwfOpenDataConnector", lambda _root: connector
    )
    monkeypatch.setattr(schedule_forecast, "parse_grib_bytes", parse)
    monkeypatch.setattr(schedule_forecast, "normalize_ifs", normalize)

    result = schedule_forecast._as_provider_result(
        schedule_forecast._ingest_ifs(service, cycle)
    )

    assert isinstance(result, ProviderRunResult)
    assert result.records_ingested == 1
    assert result.failed_leads[0].lead_hours == 3
    assert "secret" not in result.failed_leads[0].failure_detail


def test_surface_lead_zero_pipeline_failure_signals_cycle_fallback(
    monkeypatch, tmp_path: Path
) -> None:
    """A complete lead-zero parse failure remains a cycle-unavailable signal."""
    cycle = datetime(2026, 8, 27, tzinfo=UTC)
    connector = SimpleNamespace(
        retrieve=lambda requested_cycle, lead_hours: _surface_retrieval(
            tmp_path, requested_cycle, lead_hours
        )
    )
    monkeypatch.setattr(schedule_forecast, "LEADS_IFS", [0])
    monkeypatch.setattr(
        schedule_forecast, "EcmwfOpenDataConnector", lambda _root: connector
    )
    monkeypatch.setattr(
        schedule_forecast,
        "parse_grib_bytes",
        lambda _payload: (_ for _ in ()).throw(ValueError("bad lead zero")),
    )

    with pytest.raises(ValueError, match="bad lead zero"):
        schedule_forecast._ingest_ifs(SimpleNamespace(), cycle)


def test_partial_new_cycle_success_never_falls_back_and_mixes_cycles(
    monkeypatch,
) -> None:
    """Persisted surface success makes pressure lead-zero failure degraded."""
    surface_cycles = []
    pressure_cycles = []

    def surface(_service, cycle):
        surface_cycles.append(cycle)
        return 1

    def pressure(_service, cycle):
        pressure_cycles.append(cycle)
        raise RuntimeError("pressure parse failed")

    monkeypatch.setattr(schedule_forecast, "_ingest_ifs", surface)
    monkeypatch.setattr(schedule_forecast, "_ingest_ifs_pressure", pressure)

    result = schedule_forecast._run_ifs_with_fallback(object())

    assert isinstance(result, ProviderRunResult)
    assert result.records_ingested == 1
    assert result.failed_leads[0].lead_hours == 0
    assert len(surface_cycles) == 1
    assert pressure_cycles == surface_cycles


def test_ifs_job_falls_back_to_an_older_cycle_on_unavailable_cycle(
    monkeypatch,
) -> None:
    """The IFS wrapper retains the existing previous-cycle publication fallback."""
    surface_calls = 0

    def surface(_service, _cycle) -> int:
        nonlocal surface_calls
        surface_calls += 1
        if surface_calls == 1:
            raise RuntimeError("not published")
        return 2

    monkeypatch.setattr(schedule_forecast, "_ingest_ifs", surface)
    monkeypatch.setattr(
        schedule_forecast, "_ingest_ifs_pressure", lambda *_args: 3
    )

    count = schedule_forecast._run_ifs_with_fallback(object())

    assert count == 5
    assert surface_calls == 2


def test_ifs_available_empty_cycle_is_a_failure_without_older_substitution(
    monkeypatch,
) -> None:
    """An empty completed cycle retains the prior terminal-failure behavior."""
    surface_calls = 0

    def empty_surface(_service, _cycle) -> int:
        nonlocal surface_calls
        surface_calls += 1
        return 0

    monkeypatch.setattr(schedule_forecast, "_ingest_ifs", empty_surface)
    monkeypatch.setattr(
        schedule_forecast, "_ingest_ifs_pressure", lambda *_args: 0
    )

    with pytest.raises(RuntimeError, match="yielded no records"):
        schedule_forecast._run_ifs_with_fallback(object())
    assert surface_calls == 1


def test_run_recorder_updates_explicit_operational_health() -> None:
    """Terminal run facts, not canonical row presence, own health timestamps."""
    source = SimpleNamespace(
        health_status="unknown", last_success_at=None, last_failure_at=None
    )
    added = []

    recorder = DataSourceRunRecorder(lambda: _FakeSession(source, added))
    succeeded = run_once((ProviderJob("ecmwf-ifs", lambda: 1),))
    recorder(succeeded.outcomes[0])

    assert source.health_status == "healthy"
    assert source.last_success_at == succeeded.outcomes[0].finished_at
    assert source.last_failure_at is None
    assert added[0].outcome == "succeeded"


def test_run_recorder_marks_failed_source_without_verifying_it() -> None:
    """A failed run updates failure health but never changes lifecycle status."""
    source = SimpleNamespace(
        status="connected",
        health_status="healthy",
        last_success_at=None,
        last_failure_at=None,
    )

    failed = run_once(
        (
            ProviderJob(
                "ecmwf-ifs",
                lambda: (_ for _ in ()).throw(RuntimeError("unavailable")),
            ),
        )
    )
    DataSourceRunRecorder(lambda: _FakeSession(source))(failed.outcomes[0])

    assert source.status == "connected"
    assert source.health_status == "failed"
    assert source.last_failure_at == failed.outcomes[0].finished_at


def test_run_recorder_marks_partial_provider_degraded_with_details() -> None:
    """Partial lead failures persist diagnostics and degraded source health."""
    source = SimpleNamespace(
        status="configured",
        health_status="unknown",
        last_success_at=None,
        last_failure_at=None,
    )
    added = []
    outcome = run_once(
        (
            ProviderJob(
                "ecmwf-ifs",
                lambda: ProviderRunResult(
                    3, (FailedLead(12, "TimeoutError", "not published"),)
                ),
            ),
        )
    ).outcomes[0]

    DataSourceRunRecorder(lambda: _FakeSession(source, added))(outcome)

    assert source.status == "configured"
    assert source.health_status == "degraded"
    assert source.last_success_at == outcome.finished_at
    assert source.last_failure_at == outcome.finished_at
    assert added[0].outcome == "succeeded"
    assert added[0].failure_code == "PARTIAL_LEAD_FAILURE"
    assert "+12h TimeoutError: not published" in added[0].failure_detail


def test_seed_creates_all_known_sources_without_live_health_claim() -> None:
    """Registry discovery includes disabled providers as configured/unknown."""
    added = []

    class _SeedSession:
        def get(self, _model, _source_id):
            """Represent every known source as not yet seeded."""
            return None

        def add(self, source):
            """Capture one registry source."""
            added.append(source)

        def commit(self):
            """Represent a successful registry transaction."""
            return None

    schedule_forecast._seed(_SeedSession())

    assert {source.source_id for source in added} == {
        "ecmwf-ifs",
        "noaa-gfs",
        "ecmwf-aifs",
        "dwd-icon",
    }
    assert all(source.status == "configured" for source in added)
    assert all(source.health_status == "unknown" for source in added)
