"""
Data I/O helpers – replaces SAS ``libname``, ``INFILE``, and ``datalines``.

Provides:
- Dataset library management (save/load/list datasets)
- Fixed-width file reader (``read_fwf_sas``)
- Delimited file reader (``read_csv_sas``)
- Inline data reader (``read_datalines``)
- Date/format parsing helpers
"""

from __future__ import annotations

import datetime
import io
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 3a. Dataset library management
# ---------------------------------------------------------------------------

DATASETS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "datasets")
"""Default dataset directory – replaces ``libname learn 'c:\\books\\learning'``."""


def save_dataset(
    df: pd.DataFrame,
    name: str,
    directory: Optional[str] = None,
) -> None:
    """Save a DataFrame as ``{name}.pkl`` (and ``.csv`` for readability).

    Parameters
    ----------
    df : DataFrame
    name : str
        Dataset name (no extension).
    directory : str | None
        Target directory (defaults to :data:`DATASETS_DIR`).
    """
    target = directory or DATASETS_DIR
    os.makedirs(target, exist_ok=True)
    df.to_pickle(os.path.join(target, f"{name}.pkl"))
    df.to_csv(os.path.join(target, f"{name}.csv"), index=False)


def load_dataset(
    name: str,
    directory: Optional[str] = None,
) -> pd.DataFrame:
    """Load a DataFrame from ``{name}.pkl``.

    Parameters
    ----------
    name : str
        Dataset name (no extension).
    directory : str | None
        Source directory (defaults to :data:`DATASETS_DIR`).
    """
    target = directory or DATASETS_DIR
    path = os.path.join(target, f"{name}.pkl")
    return pd.read_pickle(path)


def list_datasets(directory: Optional[str] = None) -> List[str]:
    """List available dataset names (based on ``.pkl`` files).

    Parameters
    ----------
    directory : str | None
        Source directory (defaults to :data:`DATASETS_DIR`).
    """
    target = directory or DATASETS_DIR
    if not os.path.isdir(target):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(target)
        if f.endswith(".pkl")
    )


# ---------------------------------------------------------------------------
# 3b. Fixed-width file reader
# ---------------------------------------------------------------------------

def read_fwf_sas(
    filepath: str,
    colspecs: List[Tuple[int, int]],
    names: List[str],
    dtypes: Optional[Dict[str, type]] = None,
    firstobs: int = 1,
    obs: Optional[int] = None,
    truncover: bool = False,
    missover: bool = False,
    pad: bool = False,
) -> pd.DataFrame:
    """Read a fixed-width file with SAS-style parameters.

    Parameters
    ----------
    filepath : str
        Path to the data file.
    colspecs : list[(start, width)]
        1-based SAS column positions and widths.
    names : list[str]
        Column names.
    dtypes : dict | None
        Optional dtype overrides.
    firstobs : int
        First observation to read (1-based).
    obs : int | None
        Last observation number to read.
    truncover : bool
        If True, don't error on short lines – assign missing.
    missover : bool
        If True, assign missing to variables past end-of-line.
    pad : bool
        If True, pad short lines with blanks to expected length.
    """
    # Convert 1-based (start, width) to 0-based (start, end) for pandas
    pd_colspecs: list[tuple[int, int]] = []
    for start, width in colspecs:
        s = start - 1  # 1-based → 0-based
        pd_colspecs.append((s, s + width))

    skiprows = firstobs - 1 if firstobs > 1 else 0
    nrows = (obs - firstobs + 1) if obs is not None else None

    if pad or truncover or missover:
        # Read the file manually, pad/truncate lines as needed
        max_col = max(s + w for s, w in colspecs)
        lines: list[str] = []
        with open(filepath, "r") as fh:
            for i, line in enumerate(fh):
                if i < skiprows:
                    continue
                if nrows is not None and len(lines) >= nrows:
                    break
                line = line.rstrip("\n").rstrip("\r")
                if pad or truncover or missover:
                    if len(line) < max_col:
                        line = line.ljust(max_col)
                lines.append(line)

        if not lines:
            return pd.DataFrame(columns=names)

        buf = io.StringIO("\n".join(lines))
        df = pd.read_fwf(buf, colspecs=pd_colspecs, header=None, names=names)
    else:
        df = pd.read_fwf(
            filepath,
            colspecs=pd_colspecs,
            header=None,
            names=names,
            skiprows=skiprows,
            nrows=nrows,
        )

    if dtypes:
        for col, dtype in dtypes.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)

    return df


# ---------------------------------------------------------------------------
# 3c. Delimited file reader
# ---------------------------------------------------------------------------

def read_csv_sas(
    filepath: str,
    names: List[str],
    sep: Optional[str] = None,
    dsd: bool = False,
    dlm: Optional[str] = None,
    firstobs: int = 1,
    obs: Optional[int] = None,
) -> pd.DataFrame:
    """Read a delimited file with SAS-style parameters.

    Parameters
    ----------
    filepath : str
        Path to the data file.
    names : list[str]
        Column names.
    sep : str | None
        Explicit separator (takes precedence over *dsd* / *dlm*).
    dsd : bool
        If True, use comma delimiter with consecutive-delimiter-as-missing.
    dlm : str | None
        Custom delimiter string (e.g. ``' ,'``).
    firstobs : int
        First observation to read (1-based).
    obs : int | None
        Last observation number.
    """
    skiprows = firstobs - 1 if firstobs > 1 else 0
    nrows = (obs - firstobs + 1) if obs is not None else None

    if sep is not None:
        delimiter = sep
    elif dsd:
        delimiter = ","
    elif dlm is not None:
        # Multiple delimiters: read with regex separator
        delimiter = f"[{re.escape(dlm)}]+"
        return pd.read_csv(
            filepath,
            sep=delimiter,
            engine="python",
            header=None,
            names=names,
            skiprows=skiprows,
            nrows=nrows,
            skipinitialspace=True,
        )
    else:
        delimiter = r"\s+"
        return pd.read_csv(
            filepath,
            sep=delimiter,
            engine="python",
            header=None,
            names=names,
            skiprows=skiprows,
            nrows=nrows,
        )

    kwargs: dict[str, Any] = {}
    if dsd:
        kwargs["skipinitialspace"] = True
        kwargs["keep_default_na"] = True

    return pd.read_csv(
        filepath,
        sep=delimiter,
        header=None,
        names=names,
        skiprows=skiprows,
        nrows=nrows,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 3d. Inline data reader
# ---------------------------------------------------------------------------

def read_datalines(
    data_string: str,
    input_spec: Union[List[str], List[tuple]],
    truncover: bool = False,
    missover: bool = False,
    double_trailing_at: bool = False,
) -> pd.DataFrame:
    """Parse inline data (SAS ``datalines`` blocks) from a multi-line string.

    Parameters
    ----------
    data_string : str
        The raw text of the data block.
    input_spec : list
        Either:
        - A list of column names (list-mode / space-delimited), or
        - A list of ``(name, start, width, type)`` tuples for column-mode.
    truncover : bool
        Pad short lines with missing.
    missover : bool
        Assign missing to variables past end-of-line.
    double_trailing_at : bool
        If True, multiple observations per line (``@@``).
    """
    raw_lines = [ln for ln in data_string.strip().splitlines() if ln.strip()]

    # Detect mode: list of str → list-mode; list of tuple → column-mode
    if not input_spec:
        return pd.DataFrame()

    if isinstance(input_spec[0], str):
        return _read_datalines_list(raw_lines, input_spec, truncover, missover, double_trailing_at)
    else:
        return _read_datalines_column(raw_lines, input_spec, truncover, missover)


def _read_datalines_list(
    lines: list[str],
    names: list[str],
    truncover: bool,
    missover: bool,
    double_trailing_at: bool,
) -> pd.DataFrame:
    """List-mode: split each line on whitespace."""
    rows: list[list] = []
    n_cols = len(names)

    if double_trailing_at:
        # Multiple obs per line
        all_tokens: list[str] = []
        for line in lines:
            all_tokens.extend(line.split())
        for i in range(0, len(all_tokens), n_cols):
            chunk = all_tokens[i : i + n_cols]
            if len(chunk) < n_cols:
                if truncover or missover:
                    chunk.extend([None] * (n_cols - len(chunk)))
                else:
                    continue
            rows.append(chunk)
    else:
        for line in lines:
            tokens = line.split()
            if len(tokens) < n_cols:
                if truncover or missover:
                    tokens.extend([None] * (n_cols - len(tokens)))
                else:
                    # Pad with None
                    tokens.extend([None] * (n_cols - len(tokens)))
            rows.append(tokens[:n_cols])

    df = pd.DataFrame(rows, columns=names)
    # Try numeric conversion
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def _read_datalines_column(
    lines: list[str],
    specs: list[tuple],
    truncover: bool,
    missover: bool,
) -> pd.DataFrame:
    """Column-mode: fixed positions."""
    rows: list[dict] = []
    for line in lines:
        row: dict = {}
        for spec in specs:
            name, start, width, dtype = spec
            s = start - 1
            e = s + width
            if s >= len(line):
                row[name] = None
            else:
                raw = line[s:e].strip()
                if dtype == "char":
                    row[name] = raw
                else:
                    try:
                        row[name] = float(raw) if raw else None
                    except ValueError:
                        row[name] = raw
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3e. Date/format parsing helpers
# ---------------------------------------------------------------------------

def parse_sas_date(string: str, informat: str) -> Optional[datetime.date]:
    """Parse a date string using a SAS informat name.

    Supported: ``'mmddyy10.'``, ``'mmddyy8.'``, ``'date9.'``, ``'date7.'``.
    """
    if not string or not string.strip():
        return None
    s = string.strip()
    fmt = informat.lower().rstrip(".")

    fmt_map = {
        "mmddyy10": "%m/%d/%Y",
        "mmddyy8": "%m/%d/%y",
        "date9": "%d%b%Y",
        "date7": "%d%b%y",
    }

    py_fmt = fmt_map.get(fmt)
    if py_fmt is None:
        raise ValueError(f"Unknown date informat: {informat}")

    try:
        return datetime.datetime.strptime(s, py_fmt).date()
    except ValueError:
        return None


def parse_sas_numeric(string: str, informat: str) -> Optional[float]:
    """Parse a numeric string using a SAS informat name.

    Supported: ``'dollar9.'``, ``'dollar10.2'``, ``'comma8.'``, ``'8.'``, etc.
    """
    if not string or not string.strip():
        return None
    s = string.strip()
    fmt = informat.lower().rstrip(".")

    if fmt.startswith("dollar") or fmt.startswith("comma"):
        cleaned = s.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Plain numeric
    try:
        return float(s)
    except ValueError:
        return None


def format_sas_date(date: datetime.date, fmt: str) -> str:
    """Format a date to string using a SAS format name.

    Supported: ``'mmddyy10.'``, ``'date9.'``, ``'date7.'``, ``'weekdate.'``.
    """
    fmt_lower = fmt.lower().rstrip(".")

    if fmt_lower == "mmddyy10":
        return date.strftime("%m/%d/%Y")
    if fmt_lower == "mmddyy8":
        return date.strftime("%m/%d/%y")
    if fmt_lower == "date9":
        return date.strftime("%d%b%Y").upper()
    if fmt_lower == "date7":
        return date.strftime("%d%b%y").upper()
    if fmt_lower == "weekdate":
        return date.strftime("%A, %B %d, %Y")

    raise ValueError(f"Unknown date format: {fmt}")


def format_sas_number(value: float, fmt: str) -> str:
    """Format a numeric value using a SAS format name.

    Supported: ``'dollar10.2'``, ``'comma8.'``, ``'8.'``, ``'best12.'``, etc.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "."

    fmt_lower = fmt.lower().rstrip(".")

    # Dollar format
    m = re.match(r"dollar(\d+)\.?(\d+)?", fmt_lower)
    if m:
        decimals = int(m.group(2)) if m.group(2) else 0
        if decimals:
            return f"${value:,.{decimals}f}"
        return f"${value:,.0f}"

    # Comma format
    m = re.match(r"comma(\d+)\.?(\d+)?", fmt_lower)
    if m:
        decimals = int(m.group(2)) if m.group(2) else 0
        if decimals:
            return f"{value:,.{decimals}f}"
        return f"{value:,}"

    # Percent format
    if fmt_lower.startswith("percent"):
        m2 = re.match(r"percent(\d+)\.?(\d+)?", fmt_lower)
        decimals = int(m2.group(2)) if m2 and m2.group(2) else 0
        return f"{value * 100:.{decimals}f}%"

    # Plain numeric (e.g. "8", "12", "best12")
    m = re.match(r"(\d+)\.?(\d+)?", fmt_lower)
    if m:
        width = int(m.group(1))
        decimals = int(m.group(2)) if m.group(2) else None
        if decimals is not None:
            return f"{value:.{decimals}f}"
        return str(value)

    if fmt_lower.startswith("best"):
        return str(value)

    return str(value)
