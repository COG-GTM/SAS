"""Single source of truth for file locations.

Replaces the hard-coded ``c:\\books\\learning`` paths used throughout the SAS
programs: raw input files are read from ``data_dir`` (the repo's ``Data/``),
the rebuilt ``Learn`` library is stored as Parquet in ``learn_dir`` and other
generated files (ODS CSV/HTML, exports) go to ``output_dir``.

Defaults are derived from the repository checkout (editable install). When the
package is installed elsewhere, set the ``SAS_EXAMPLES_*`` environment variables.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Literal

DATA_DIR_ENV = "SAS_EXAMPLES_DATA_DIR"
LEARN_DIR_ENV = "SAS_EXAMPLES_LEARN_DIR"
OUTPUT_DIR_ENV = "SAS_EXAMPLES_OUTPUT_DIR"

_PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = _PACKAGE_DIR.parent
REPO_ROOT = PROJECT_DIR.parent

DEFAULT_DATA_DIR = REPO_ROOT / "Data"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "output"
DEFAULT_LEARN_DIR = DEFAULT_OUTPUT_DIR / "learn"

_SAS_ROOT = re.compile(r"^[a-z]:[\\/]books[\\/]learning(?:[\\/]|$)", re.IGNORECASE)


@dataclass(frozen=True)
class Config:
    data_dir: Path
    learn_dir: Path
    output_dir: Path


def _in_repo_checkout() -> bool:
    return (REPO_ROOT / "Example code").is_dir() and DEFAULT_DATA_DIR.is_dir()


def _dir_setting(env_var: str, default: Path) -> Path:
    value = os.environ.get(env_var)
    if value:
        return Path(value)
    if not _in_repo_checkout():
        raise RuntimeError(
            f"sas_examples is not running from a COG-GTM/SAS checkout; set {env_var}"
        )
    return default


def get_config() -> Config:
    """Return the active configuration, honouring the override env vars."""
    return Config(
        data_dir=_dir_setting(DATA_DIR_ENV, DEFAULT_DATA_DIR),
        learn_dir=_dir_setting(LEARN_DIR_ENV, DEFAULT_LEARN_DIR),
        output_dir=_dir_setting(OUTPUT_DIR_ENV, DEFAULT_OUTPUT_DIR),
    )


def _file_name(name: str) -> str:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or ":" in name:
        raise ValueError(f"Expected a bare file name, got {name!r}")
    return name


def data_path(name: str, config: Config | None = None) -> Path:
    """Return the path of raw input file ``name`` in ``data_dir``.

    The lookup is case-insensitive because the SAS code and ``Data/`` disagree
    on file name case (``Veggies.txt`` vs ``veggies.txt``).
    """
    name = _file_name(name)
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


def output_path(name: str, config: Config | None = None, *, create_dir: bool = False) -> Path:
    """Return the path for generated file ``name`` (ODS CSV/HTML, exports) in ``output_dir``."""
    name = _file_name(name)
    output_dir = (config or get_config()).output_dir
    if create_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / name


def resolve_sas_path(
    sas_path: str,
    config: Config | None = None,
    *,
    mode: Literal["read", "write"] = "read",
) -> Path:
    """Map a ``c:\\books\\learning\\...`` literal from the SAS code to a local path.

    Bare names such as ``c:\\books\\learning\\Mydata`` are permanent datasets
    (``learn_path``). Names with an extension are raw inputs (``data_path``) in
    ``read`` mode and generated files (``output_path``) in ``write`` mode, so
    outputs such as ``ods csv file=...`` never overwrite files in ``Data/``.
    The bare library root maps to ``learn_dir`` (read) or ``output_dir`` (write).
    """
    if mode not in ("read", "write"):
        raise ValueError(f"mode must be 'read' or 'write', got {mode!r}")
    if not _SAS_ROOT.match(sas_path):
        raise ValueError(f"Not a c:\\books\\learning path: {sas_path!r}")
    cfg = config or get_config()
    parts = PureWindowsPath(sas_path.replace("/", "\\")).parts[3:]
    if not parts:
        return cfg.learn_dir if mode == "read" else cfg.output_dir
    if len(parts) > 1:
        raise ValueError(f"Nested paths are not supported: {sas_path!r}")
    name = parts[0]
    if not PureWindowsPath(name).suffix:
        return learn_path(name, cfg)
    return data_path(name, cfg) if mode == "read" else output_path(name, cfg)
