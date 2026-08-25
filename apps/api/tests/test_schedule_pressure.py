"""Deterministic tests for the scheduler pressure-level ingestion path."""

# Test fakes import helpers inline to keep fixtures self-contained.
# pylint: disable=import-outside-toplevel

from __future__ import annotations

from datetime import UTC, datetime
import urllib.request

import pytest

import schedule_forecast as sched


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
