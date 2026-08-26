"""Deterministic unit tests for the Sentinel-2 AOI connector (EV-SAT-002)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from services.satellite.sentinel2 import (
    RgbScene,
    Sentinel2Scene,
    build_rgb,
    summarize,
    write_png,
)
from services.satellite.sentinel2.connector import (  # type: ignore[attr-defined]
    _scale_uint8,
)

_AOI_BOUNDS = (86.8, 27.85, 87.05, 28.05)


def test_scene_prefix_and_band_url() -> None:
    """Scene identity maps to the official S3 prefix and band URLs."""
    scene = Sentinel2Scene("45R", "VK", "2026/8/24", "0", "EPSG:32645")
    assert scene.prefix == "tiles/45R/VK/2026/8/24/0"
    assert scene.band_url(4).endswith(
        "/tiles/45R/VK/2026/8/24/0/B04.jp2"
    )
    assert "sentinel-s2-l1c" in scene.band_url(2)


def test_scale_uint8_normalizes_and_clips() -> None:
    """Percentile scaling maps a finite band to 8-bit and clips outliers."""
    band = np.array([[0, 100], [1000, 5000]], dtype=np.float32)
    out = _scale_uint8(band)
    assert out.dtype == np.uint8
    assert out.max() <= 255
    assert out.min() >= 0


def test_scale_uint8_handles_constant_or_nan() -> None:
    """A constant or all-NaN band returns a zero 8-bit array, not an error."""
    constant = np.full((4, 4), 3.0, dtype=np.float32)
    assert _scale_uint8(constant).shape == (4, 4)
    assert _scale_uint8(constant).dtype == np.uint8
    nan = np.full((4, 4), np.nan, dtype=np.float32)
    out = _scale_uint8(nan)
    assert out.shape == (4, 4)
    assert int(out.max()) == 0


def test_build_rgb_structure_and_hash(monkeypatch) -> None:
    """build_rgb returns an RgbScene with a stable hash and rgb shape."""
    scene = Sentinel2Scene("45R", "VK", "2026/8/24", "0", "EPSG:32645")

    fake = np.full((4, 4), 200.0, dtype=np.float32)

    def _fake_read_band(url, bounds, out_shape):
        return fake

    monkeypatch.setattr(
        "services.satellite.sentinel2.connector._read_band_window",
        _fake_read_band,
    )
    rgb = build_rgb(scene, _AOI_BOUNDS, (4, 4))
    assert isinstance(rgb, RgbScene)
    assert rgb.rgb.shape == (4, 4, 3)
    assert rgb.rgb.dtype == np.uint8
    assert len(rgb.sha256) == 64
    assert rgb.timestamp.tzinfo is not None


def test_write_png_produces_file(tmp_path: Path) -> None:
    """write_png persists an 8-bit RGB PNG at the destination."""
    rgb = np.zeros((8, 8, 3), dtype=np.uint8)
    rgb[:, :, 0] = 200
    dest = tmp_path / "everest-rgb.png"
    write_png(rgb, dest)
    assert dest.exists()
    assert dest.stat().st_size > 0


def test_summarize_lists_key_facts() -> None:
    """summarize returns scene, crs, bands, and hash lines."""
    scene = Sentinel2Scene("45R", "VK", "2026/8/24", "0", "EPSG:32645")
    rgb = RgbScene(
        scene=scene,
        timestamp=datetime(2026, 8, 24, tzinfo=UTC),
        rgb=np.zeros((2, 2, 3), dtype=np.uint8),
        width=2,
        height=2,
        sha256="a" * 64,
    )
    lines = summarize(scene, rgb)
    text = "\n".join(lines)
    assert "45R" in text
    assert "B4,B3,B2" in text
    assert "sha256" in text
