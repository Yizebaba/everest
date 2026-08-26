"""Unit tests for the Everest AWS observation connector, parser, and QC."""

from __future__ import annotations

import pytest

from services.weather.everest_aws.connector import (
    StationFeed,
    download_station,
)
from services.weather.everest_aws.parser import parse_rows
from services.weather.everest_aws.qc import run_qc

BASE_CAMP_CSV = (
    "Time (NPT),Temperature (Celsius),Relative Humidity,col3,col4,col5,"
    "Weather,Precipitation,Missing\n"
    "2025-10-23 12:00:00,-4.833,61.82,0.0,1094.0,0,NP,0.0,False\n"
    "2025-10-23 13:00:00,NAN,39.08,0.0,1094.0,0,NP,1001.0,True\n"
)
CAMP2_CSV = (
    "Time (NPT),Temperature (Celsius),Relative Humidity,col3,col4,col5,Missing\n"
    "2025-10-24 02:00:00,-13.06,10.49,22.74,8.38,462.1,False\n"
    "2025-10-24 03:00:00,bad,9.29,523.3,4.457,462.4,False\n"
)


def test_station_feed_url() -> None:
    feed = StationFeed("Base Camp")
    assert feed.url().endswith("Base%20Camp.csv")


def test_download_station_invalid(tmp_path) -> None:
    with pytest.raises(ValueError):
        download_station("Not A Station", tmp_path / "x.csv")


def test_parse_base_camp_utc(tmp_path) -> None:
    path = tmp_path / "bc.csv"
    path.write_text(BASE_CAMP_CSV, encoding="utf-8")
    rows = parse_rows(path, "Base Camp")
    assert len(rows) == 2
    first = rows[0]
    # NPT 12:00 on 2025-10-23 == UTC 06:15
    assert first.timestamp.isoformat() == "2025-10-23T06:15:00+00:00"
    assert first.temperature_c == pytest.approx(-4.833)
    assert rows[1].temperature_c is None  # NAN -> None
    assert rows[1].precipitation == pytest.approx(1001.0)
    assert rows[1].missing is True


def test_parse_camp2_layout(tmp_path) -> None:
    path = tmp_path / "c2.csv"
    path.write_text(CAMP2_CSV, encoding="utf-8")
    rows = parse_rows(path, "Camp 2")
    assert len(rows) == 2
    assert rows[0].temperature_c == pytest.approx(-13.06)
    assert rows[0].precipitation is None  # column absent
    assert rows[1].temperature_c is None  # 'bad' -> None


def test_qc_flags_precipitation_anomaly(tmp_path) -> None:
    path = tmp_path / "bc.csv"
    path.write_text(BASE_CAMP_CSV, encoding="utf-8")
    rows = parse_rows(path, "Base Camp")
    report = run_qc(rows, "Base Camp")
    assert not report.passed
    assert "precipitation_anomaly" in report.flags
    assert report.precipitation_anomaly_count == 1
    assert report.missing_flag_count == 1
