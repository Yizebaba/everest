"""Everest AWS observation QC: flag anomalies, never delete data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.weather.everest_aws.parser import AwsObservationRow


@dataclass(frozen=True)
class AwsQcReport:
    """QC findings for one station's parsed rows."""

    station: str
    row_count: int
    utc_min: str
    utc_max: str
    temperature_min: float | None
    temperature_max: float | None
    missing_flag_count: int
    precipitation_anomaly_count: int
    skipped_rows: int
    flags: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """True when no blocking flags are raised."""
        return not self.flags


def run_qc(
    rows: list[AwsObservationRow], station: str, skipped_rows: int = 0
) -> AwsQcReport:
    """Run QC over parsed rows.

    Checks: row count > 0; temperature within plausible range (-60..+60 C);
    precipitation anomalies flagged (provider artifacts such as ~1000 mm
    spikes); missing flags counted. QC flags rather than deletes.
    """
    flags: list[str] = []
    temps = [r.temperature_c for r in rows if r.temperature_c is not None]
    missing_flags = sum(1 for r in rows if r.missing)
    precip_anomalies = sum(1 for r in rows if (r.precipitation or 0) > 500.0)
    if not rows:
        flags.append("no_rows")
        return AwsQcReport(
            station=station,
            row_count=0,
            utc_min="",
            utc_max="",
            temperature_min=None,
            temperature_max=None,
            missing_flag_count=0,
            precipitation_anomaly_count=0,
            skipped_rows=skipped_rows,
            flags=tuple(flags),
        )
    if temps:
        temp_min = min(temps)
        temp_max = max(temps)
        if temp_min < -60.0 or temp_max > 60.0:
            flags.append("temperature_out_of_range")
    else:
        temp_min = None
        temp_max = None
    if precip_anomalies:
        flags.append("precipitation_anomaly")
    return AwsQcReport(
        station=station,
        row_count=len(rows),
        utc_min=min(r.timestamp for r in rows).isoformat(),
        utc_max=max(r.timestamp for r in rows).isoformat(),
        temperature_min=temp_min,
        temperature_max=temp_max,
        missing_flag_count=missing_flags,
        precipitation_anomaly_count=precip_anomalies,
        skipped_rows=skipped_rows,
        flags=tuple(flags),
    )


def summary_lines(report: AwsQcReport) -> Sequence[str]:
    """Render a QC report as stable text lines for evidence logs."""
    return (
        f"rows: {report.row_count} (skipped {report.skipped_rows})",
        f"utc: {report.utc_min} .. {report.utc_max}",
        f"temperature: {report.temperature_min} .. {report.temperature_max} C",
        f"missing flags: {report.missing_flag_count}",
        f"precipitation anomalies: {report.precipitation_anomaly_count}",
        f"flags: {','.join(report.flags) or 'none'}",
        f"qc: {'PASS' if report.passed else 'FAIL'}",
    )
