"""Deterministic tests for optional high-level weather retrieval."""

# Fakes intentionally expose only the provider methods used by each adapter.
# pylint: disable=too-few-public-methods,missing-class-docstring
# pylint: disable=missing-function-docstring,import-outside-toplevel,duplicate-code

from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.weather.aoi import AreaOfInterest, subset_dataset
from services.weather.retrieval import RetrievalRequest, open_grib_dataset


def test_rectilinear_subset_normalizes_longitude_and_descending_latitude() -> (
    None
):
    """A 0..360 grid is selected with a -180..180 AOI without changing input."""
    xr = pytest.importorskip("xarray")
    source = xr.Dataset(
        {
            "temperature": (
                ("latitude", "longitude"),
                [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            ),
            "wind": (
                ("latitude", "longitude"),
                [[9, 8, 7], [6, 5, 4], [3, 2, 1]],
            ),
        },
        coords={
            "latitude": [30.0, 20.0, 10.0],
            "longitude": [80.0, 90.0, 350.0],
        },
    )

    result = subset_dataset(
        source,
        AreaOfInterest(south=15, north=30, west=-15, east=95),
        variables=("temperature",),
    )

    assert tuple(result.data_vars) == ("temperature",)
    assert result.latitude.values.tolist() == [30.0, 20.0]
    assert result.longitude.values.tolist() == [80.0, 90.0, 350.0]
    assert tuple(source.data_vars) == ("temperature", "wind")


def test_curvilinear_subset_masks_and_drops_outside_cells() -> None:
    """Two-dimensional coordinates use an AOI mask and retain intersecting cells."""
    xr = pytest.importorskip("xarray")
    source = xr.Dataset(
        {"t": (("y", "x"), [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])},
        coords={
            "latitude": (("y", "x"), [[10.0, 10.0, 10.0], [20.0, 20.0, 20.0]]),
            "longitude": (
                ("y", "x"),
                [[80.0, 90.0, 100.0], [80.0, 90.0, 100.0]],
            ),
        },
    )

    result = subset_dataset(
        source,
        AreaOfInterest(south=15, north=25, west=85, east=95),
        variables=("t",),
    )

    assert result.sizes == {"y": 1, "x": 1}
    assert result["t"].item() == 5.0


def test_variable_selection_is_explicit_and_validated() -> None:
    """Empty or unknown variable requests fail instead of reading everything."""
    xr = pytest.importorskip("xarray")
    source = xr.Dataset({"t": ("latitude", [1.0])}, coords={"latitude": [0.0]})
    area = AreaOfInterest(-1, 1, -1, 1)

    with pytest.raises(ValueError, match="at least one"):
        subset_dataset(source, area, variables=())
    with pytest.raises(KeyError, match="missing"):
        subset_dataset(source, area, variables=("missing",))


def test_open_grib_uses_cfgrib_without_persistent_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shared decoder passes safe deterministic cfgrib backend options."""
    calls = []

    class FakeXarray:
        @staticmethod
        def open_dataset(path: Path, **kwargs: object) -> str:
            calls.append((path, kwargs))
            return "dataset"

    monkeypatch.setattr(
        "services.weather.retrieval._import_xarray", lambda: FakeXarray
    )
    result = open_grib_dataset(
        Path("sample.grib2"), filter_by_keys={"typeOfLevel": "surface"}
    )

    assert result == "dataset"
    assert calls == [
        (
            Path("sample.grib2"),
            {
                "engine": "cfgrib",
                "backend_kwargs": {
                    "indexpath": "",
                    "filter_by_keys": {"typeOfLevel": "surface"},
                },
            },
        )
    ]


def test_retrieval_request_is_immutable_and_normalizes_utc() -> None:
    """Requests reject ambiguous cycles and expose immutable tuples."""
    cycle = datetime(2026, 8, 27, 6, tzinfo=timezone.utc)
    request = RetrievalRequest(
        cycle=cycle, lead_hours=6, variables=("2t",), target_dir=Path("raw")
    )
    assert request.cycle == cycle
    with pytest.raises((AttributeError, TypeError)):
        request.lead_hours = 12  # type: ignore[misc]
    with pytest.raises(ValueError, match="timezone-aware"):
        RetrievalRequest(datetime(2026, 8, 27), 0, ("2t",), Path("raw"))


def test_herbie_client_uses_official_gfs_contract(tmp_path: Path) -> None:
    """Herbie receives the pinned GFS identity and ordered source priority."""
    from services.weather.gfs.herbie_client import HerbieGfsClient

    calls = []

    class FakeHerbie:
        def __init__(self, cycle: datetime, **kwargs: object) -> None:
            calls.append(("init", cycle, kwargs))

        def download(self, search: str, **kwargs: object) -> Path:
            calls.append(("download", search, kwargs))
            path = tmp_path / "gfs.grib2"
            path.write_bytes(b"GRIB")
            return path

    request = RetrievalRequest(
        datetime(2026, 8, 27, 0, tzinfo=timezone.utc),
        6,
        ("TMP", "UGRD"),
        tmp_path,
    )
    artifact = HerbieGfsClient(herbie_factory=FakeHerbie).retrieve(request)

    assert calls[0][1] == datetime(2026, 8, 27, 0)
    assert calls[0][2] == {
        "model": "gfs",
        "product": "pgrb2.0p25",
        "fxx": 6,
        "priority": ["aws", "google", "nomads"],
    }
    assert artifact.path == tmp_path / "gfs.grib2"
    assert artifact.provider == "noaa-gfs"


@pytest.mark.parametrize(
    ("module", "class_name", "model", "provider"),
    [
        (
            "services.weather.ecmwf.opendata_client",
            "EcmwfIfsOpenDataClient",
            "ifs",
            "ecmwf-ifs",
        ),
        (
            "services.weather.aifs.opendata_client",
            "EcmwfAifsOpenDataClient",
            "aifs-single",
            "ecmwf-aifs",
        ),
    ],
)
def test_ecmwf_clients_use_bounded_official_contract(
    tmp_path: Path, module: str, class_name: str, model: str, provider: str
) -> None:
    """Both ECMWF models use 0p25 and bounded retry configuration."""
    imported = __import__(module, fromlist=[class_name])
    client_class = getattr(imported, class_name)
    calls = []

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("init", kwargs))

        def retrieve(self, request: dict[str, object]) -> None:
            calls.append(("retrieve", request))
            Path(str(request["target"])).write_bytes(b"GRIB")

    request = RetrievalRequest(
        datetime(2026, 8, 27, 6, tzinfo=timezone.utc),
        12,
        ("2t", "10u"),
        tmp_path,
    )
    artifact = client_class(client_factory=FakeClient).retrieve(request)

    assert calls[0][1] == {
        "source": "ecmwf",
        "model": model,
        "resol": "0p25",
        "maximum_retries": 3,
        "retry_after": 5,
        "use_server_retry_after": True,
    }
    assert calls[1][1]["param"] == ["2t", "10u"]
    assert artifact.provider == provider
    assert artifact.path.is_file()
