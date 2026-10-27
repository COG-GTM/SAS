"""Single source of truth for file locations.

Replaces the hard-coded ``c:\\books\\learning`` paths used throughout the SAS
programs: raw input files live in ``data_dir`` (the repo's ``Data/``) and the
rebuilt ``Learn`` library is stored as Parquet in ``learn_dir``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

DATA_DIR_ENV = "SAS_EXAMPLES_DATA_DIR"
LEARN_DIR_ENV = "SAS_EXAMPLES_LEARN_DIR"

_PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = _PACKAGE_DIR.parent
REPO_ROOT = PROJECT_DIR.parent

DEFAULT_DATA_DIR = REPO_ROOT / "Data"
DEFAULT_LEARN_DIR = PROJECT_DIR / "output" / "learn"

_SAS_ROOT = re.compile(r"^[a-z]:[\\/]books[\\/]learning", re.IGNORECASE)


@dataclass(frozen=True)
class Config:
    data_dir: Path
    learn_dir: Path


def get_config() -> Config:
    """Return the active configuration, honouring the override env vars."""
    data_dir = os.environ.get(DATA_DIR_ENV)
    learn_dir = os.environ.get(LEARN_DIR_ENV)
    return Config(
        data_dir=Path(data_dir) if data_dir else DEFAULT_DATA_DIR,
        learn_dir=Path(learn_dir) if learn_dir else DEFAULT_LEARN_DIR,
    )


def data_path(name: str, config: Config | None = None) -> Path:
    """Return the path of raw input file ``name`` in ``data_dir``.

    The lookup is case-insensitive because the SAS code and ``Data/`` disagree
    on file name case (``Veggies.txt`` vs ``veggies.txt``).
    """
    data_dir = (config or get_config()).data_dir
    exact = data_dir / name
    if exact.is_file():
        return exact
    matches = [p for p in data_dir.iterdir() if p.is_file() and p.name.lower() == name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(sorted(p.name for p in matches))
        raise FileNotFoundError(f"Ambiguous data file {name!r} in {data_dir}: {names}")
    raise FileNotFoundError(f"Data file {name!r} not found in {data_dir}")


def learn_path(dataset: str, config: Config | None = None, *, create_dir: bool = False) -> Path:
    """Return the Parquet path of ``Learn.<dataset>`` (SAS names are case-insensitive)."""
    if not dataset or not re.fullmatch(r"\w+", dataset):
        raise ValueError(f"Invalid SAS dataset name: {dataset!r}")
    learn_dir = (config or get_config()).learn_dir
    if create_dir:
        learn_dir.mkdir(parents=True, exist_ok=True)
    return learn_dir / f"{dataset.lower()}.parquet"


def resolve_sas_path(sas_path: str, config: Config | None = None) -> Path:
    """Map a ``c:\\books\\learning\\...`` literal from the SAS code to a local path.

    Names with an extension are raw files (``data_path``); bare names such as
    ``c:\\books\\learning\\Mydata`` refer to permanent datasets (``learn_path``).
    """
    if not _SAS_ROOT.match(sas_path):
        raise ValueError(f"Not a c:\\books\\learning path: {sas_path!r}")
    name = PureWindowsPath(sas_path).name
    if name.lower() == "learning":
        return (config or get_config()).learn_dir
    if PureWindowsPath(name).suffix:
        return data_path(name, config)
    return learn_path(name, config)
