"""Deterministic tests for optional high-level weather retrieval."""

# Fakes intentionally expose only the provider methods used by each adapter.
# pylint: disable=too-few-public-methods,missing-class-docstring
# pylint: disable=missing-function-docstring,import-outside-toplevel,duplicate-code

from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.weather.aoi import AreaOfInterest, subset_dataset
from services.weather.retrieval import (
    RetrievalRequest,
    RetrievedArtifact,
    open_grib_dataset,
)


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
    """Two-dimensional coordinates retain only intersecting AOI cells."""
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


def test_retrieval_request_is_immutable_and_normalizes_utc(
    tmp_path: Path,
) -> None:
    """Requests reject ambiguous cycles and expose immutable tuples."""
    cycle = datetime(2026, 8, 27, 6, tzinfo=timezone.utc)
    request = RetrievalRequest(
        cycle=cycle, lead_hours=6, variables=("2t",), target_dir=tmp_path
    )
    assert request.cycle == cycle
    with pytest.raises((AttributeError, TypeError)):
        request.lead_hours = 12  # type: ignore[misc]
    with pytest.raises(ValueError, match="timezone-aware"):
        RetrievalRequest(datetime(2026, 8, 27), 0, ("2t",), tmp_path)


def test_retrieval_request_rejects_relative_target_dir() -> None:
    """Destinations must not depend on the process working directory."""
    with pytest.raises(ValueError, match="absolute"):
        RetrievalRequest(
            datetime(2026, 8, 27, tzinfo=timezone.utc),
            0,
            ("2t",),
            Path("raw"),
        )


def test_retrieval_request_rejects_symlinked_target_dir(
    tmp_path: Path,
) -> None:
    """A destination symlink cannot redirect provider output elsewhere."""
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(ValueError, match="symlink"):
        RetrievalRequest(
            datetime(2026, 8, 27, tzinfo=timezone.utc),
            0,
            ("2t",),
            linked,
        )


def test_retrieved_artifact_rejects_path_outside_target(tmp_path: Path) -> None:
    """A provider cannot redirect the scheduler to an arbitrary local file."""
    target = tmp_path / "raw"
    target.mkdir()
    outside = tmp_path / "outside.grib2"
    outside.write_bytes(b"GRIB")
    request = RetrievalRequest(
        datetime(2026, 8, 27, tzinfo=timezone.utc),
        0,
        ("2t",),
        target,
    )

    with pytest.raises(ValueError, match="target_dir"):
        RetrievedArtifact.from_path(outside, "ecmwf-ifs", request)


def test_retrieved_artifact_rejects_relative_path(tmp_path: Path) -> None:
    """Provider results must be explicit absolute filesystem paths."""
    request = RetrievalRequest(
        datetime(2026, 8, 27, tzinfo=timezone.utc),
        0,
        ("2t",),
        tmp_path,
    )

    with pytest.raises(ValueError, match="absolute"):
        RetrievedArtifact.from_path(
            Path("forecast.grib2"), "ecmwf-ifs", request
        )

    with pytest.raises(ValueError, match="absolute"):
        RetrievedArtifact(
            path=Path("forecast.grib2"),
            provider="ecmwf-ifs",
            request=request,
            sha256="0" * 64,
            size_bytes=4,
        )


def test_retrieved_artifact_rejects_symlink(tmp_path: Path) -> None:
    """A symlinked artifact is never accepted as provider-retained content."""
    target = tmp_path / "raw"
    target.mkdir()
    actual = target / "actual.grib2"
    actual.write_bytes(b"GRIB")
    linked = target / "linked.grib2"
    try:
        linked.symlink_to(actual)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    request = RetrievalRequest(
        datetime(2026, 8, 27, tzinfo=timezone.utc),
        0,
        ("2t",),
        target,
    )

    with pytest.raises(ValueError, match="symlink"):
        RetrievedArtifact.from_path(linked, "ecmwf-ifs", request)


def test_retrieved_artifact_rejects_intermediate_symlink(
    tmp_path: Path,
) -> None:
    """No parent directory in the provider-returned path may be a symlink."""
    target = tmp_path / "raw"
    target.mkdir()
    actual = target / "actual"
    actual.mkdir()
    artifact = actual / "forecast.grib2"
    artifact.write_bytes(b"GRIB")
    linked = target / "linked"
    try:
        linked.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    request = RetrievalRequest(
        datetime(2026, 8, 27, tzinfo=timezone.utc),
        0,
        ("2t",),
        target,
    )

    with pytest.raises(ValueError, match="symlink"):
        RetrievedArtifact.from_path(
            linked / artifact.name,
            "ecmwf-ifs",
            request,
        )


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


@pytest.mark.parametrize(
    ("module", "class_name"),
    [
        ("services.weather.ecmwf.opendata_client", "EcmwfIfsOpenDataClient"),
        ("services.weather.aifs.opendata_client", "EcmwfAifsOpenDataClient"),
    ],
)
def test_ecmwf_filename_changes_with_variable_inventory(
    tmp_path: Path, module: str, class_name: str
) -> None:
    """Same run/lead with a different inventory cannot reuse one target name."""
    imported = __import__(module, fromlist=[class_name])
    client_class = getattr(imported, class_name)
    targets = []

    class FakeClient:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def retrieve(self, request: dict[str, object]) -> None:
            target = Path(str(request["target"]))
            targets.append(target)
            target.write_bytes(b"GRIB")

    client = client_class(client_factory=FakeClient)
    cycle = datetime(2026, 8, 27, 6, tzinfo=timezone.utc)
    client.retrieve(RetrievalRequest(cycle, 12, ("2t", "10u"), tmp_path))
    client.retrieve(RetrievalRequest(cycle, 12, ("2t", "10v"), tmp_path))
    client.retrieve(RetrievalRequest(cycle, 12, ("10u", "2t"), tmp_path))

    assert targets[0] != targets[1]
    assert targets[0] == targets[2]
    assert targets[0].stem.count("-") >= 3
