"""Unit tests for the Himawari connector, parser, and QC."""

from __future__ import annotations

import bz2
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from himawari.connector import (
    FlDkTimeSlot,
    segment_filename,
)
from himawari.parser import parse_segment
from himawari.qc import run_qc


def _synthetic_segment(tmp_path, satellite: bytes, area: bytes) -> str:
    """Write a synthetic bz2 Himawari segment and return its path."""
    payload = bytearray(512)
    payload[6:14] = satellite
    payload[38:42] = area
    path = tmp_path / "segment.DAT.bz2"
    path.write_bytes(bz2.compress(bytes(payload)))
    return str(path)


def test_segment_filename_discovers_r_code() -> None:
    """segment_filename must handle band-dependent R codes via the listing."""
    slot = FlDkTimeSlot(datetime(2026, 8, 24, 13, 50, tzinfo=timezone.utc))
    keys = [
        f"{slot.path_prefix()}/HS_H09_20260824_1350_B03_FLDK_R05_S0110.DAT.bz2",
        f"{slot.path_prefix()}/HS_H09_20260824_1350_B03_FLDK_R05_S0210.DAT.bz2",
        f"{slot.path_prefix()}/HS_H09_20260824_1350_B01_FLDK_R10_S0110.DAT.bz2",
    ]
    with patch("himawari.connector._list_keys", return_value=keys):
        name = segment_filename(slot, 3, 1)
        assert name == "HS_H09_20260824_1350_B03_FLDK_R05_S0110.DAT.bz2"
        name_b01 = segment_filename(slot, 1, 1)
        assert name_b01 == "HS_H09_20260824_1350_B01_FLDK_R10_S0110.DAT.bz2"


def test_parse_segment_identity(tmp_path) -> None:
    path = _synthetic_segment(tmp_path, b"Himawari", b"FLDK")
    info = parse_segment(tmp_path / "segment.DAT.bz2")
    assert info.satellite_name == "Himawari"
    assert info.observation_area == "FLDK"


def test_qc_pass(tmp_path) -> None:
    path = _synthetic_segment(tmp_path, b"Himawari", b"FLDK")
    info = parse_segment(tmp_path / "segment.DAT.bz2")
    report = run_qc(info, 3, 1)
    assert report.passed


def test_qc_flags_bad_satellite_and_area(tmp_path) -> None:
    path = _synthetic_segment(tmp_path, b"WRONG", b"XXXX")
    info = parse_segment(tmp_path / "segment.DAT.bz2")
    report = run_qc(info, 3, 1)
    assert not report.passed
    assert "unexpected_satellite" in report.flags
    assert "unexpected_observation_area" in report.flags


def test_invalid_band_rejected() -> None:
    slot = FlDkTimeSlot(datetime(2026, 8, 24, 13, 50, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        segment_filename(slot, 99, 1)
