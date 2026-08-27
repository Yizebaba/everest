"""One-pass scheduler orchestration tests with no provider network access."""

# The two protected-access calls directly verify the standalone script's IFS
# compatibility wrapper; it is intentionally not part of the package API.
# pylint: disable=protected-access

from __future__ import annotations

import pytest

from everest_api.scheduler import (
    ProviderJob,
    RunStatus,
    SchedulerConfig,
    run_once,
)
import schedule_forecast


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


def test_failure_detail_is_bounded_and_redacted() -> None:
    """Provider failure accounting cannot persist an obvious credential value."""

    def fails() -> int:
        raise RuntimeError("access_token=do-not-store")

    result = run_once((ProviderJob("ecmwf-ifs", fails),))

    assert result.outcomes[0].failure_detail == "access_token=[REDACTED]"


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
