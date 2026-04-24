"""
Shared helpers for locating data files and common I/O patterns.

All file paths use ``pathlib.Path`` to stay platform-independent.
"""
from __future__ import annotations

from pathlib import Path
from io import StringIO

import pandas as pd


def data_dir() -> Path:
    """Return the absolute path to the ``Data/`` directory in the repo root."""
    return Path(__file__).resolve().parent.parent.parent / "Data"


def output_dir() -> Path:
    """Return the ``python/output/`` directory, creating it if needed."""
    d = Path(__file__).resolve().parent.parent / "output"
    d.mkdir(exist_ok=True)
    return d


def read_space_delimited(filename: str, names: list[str],
                         **kwargs) -> pd.DataFrame:
    """Read a whitespace-delimited text file from the Data/ folder."""
    return pd.read_csv(
        data_dir() / filename,
        sep=r"\s+",
        names=names,
        **kwargs,
    )


def read_fixed_width(filename: str, colspecs: list[tuple[int, int]],
                     names: list[str], **kwargs) -> pd.DataFrame:
    """Read a fixed-width file from the Data/ folder."""
    return pd.read_fwf(
        data_dir() / filename,
        colspecs=colspecs,
        names=names,
        header=None,
        **kwargs,
    )


def df_from_inline(text: str, names: list[str],
                   **kwargs) -> pd.DataFrame:
    """Create a DataFrame from inline data (SAS ``datalines``)."""
    return pd.read_csv(
        StringIO(text.strip()),
        sep=r"\s+",
        names=names,
        **kwargs,
    )


def print_dataset(df: pd.DataFrame, title: str = "",
                  max_rows: int | None = None) -> None:
    """Pretty-print a DataFrame with an optional title (like PROC PRINT)."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    with pd.option_context("display.max_rows", max_rows or len(df),
                           "display.width", 120):
        print(df.to_string(index=False))
    print()
