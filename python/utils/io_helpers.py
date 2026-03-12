"""I/O helpers for reading/writing SAS-style datasets in Python.

Replaces SAS libname, INFILE, PROC IMPORT, and datalines constructs.
"""

import os
import pickle
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Dataset directory (replaces ``libname learn 'c:\\books\\learning'``)
# ---------------------------------------------------------------------------

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Save / load helpers
# ---------------------------------------------------------------------------

def save_dataset(df: pd.DataFrame, name: str, directory: Optional[str] = None) -> str:
    """Persist *df* as ``<name>.pkl`` (SAS libname equivalent).

    Returns the file path.
    """
    target_dir = directory or DATASETS_DIR
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"{name}.pkl")
    with open(path, "wb") as fh:
        pickle.dump(df, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_dataset(name: str, directory: Optional[str] = None) -> pd.DataFrame:
    """Load a previously saved dataset."""
    target_dir = directory or DATASETS_DIR
    path = os.path.join(target_dir, f"{name}.pkl")
    with open(path, "rb") as fh:
        return pickle.load(fh)


# ---------------------------------------------------------------------------
# SAS date parsing / formatting
# ---------------------------------------------------------------------------

_SAS_EPOCH = date(1960, 1, 1)

# Mapping of SAS informat names → strptime patterns (tried in order)
_DATE_INFORMAT_MAP: Dict[str, List[str]] = {
    "mmddyy": ["%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y"],
    "ddmmyy": ["%d/%m/%Y", "%d/%m/%y"],
    "yymmdd": ["%Y-%m-%d", "%y-%m-%d", "%Y/%m/%d"],
    "date": ["%d%b%Y", "%d%B%Y", "%d%b%y"],
    "anydtdte": ["%m/%d/%Y", "%d%b%Y", "%Y-%m-%d"],
    "datetime": ["%d%b%Y:%H:%M:%S", "%m/%d/%Y %H:%M:%S"],
    "monyy": ["%b%Y", "%B%Y"],
}

# Mapping of SAS format names → strftime patterns
_DATE_FORMAT_MAP: Dict[str, str] = {
    "mmddyy10": "%m/%d/%Y",
    "mmddyy8": "%m/%d/%y",
    "date9": "%d%b%Y",
    "date7": "%d%b%y",
    "yymmdd10": "%Y-%m-%d",
    "ddmmyy10": "%d/%m/%Y",
    "monyy7": "%b%Y",
    "worddate": "%B %d, %Y",
    "weekdate": "%A, %B %d, %Y",
}


def parse_sas_date(string: str, informat: str) -> Optional[date]:
    """Parse *string* using a SAS date *informat* name.

    Returns a Python ``date`` or ``None`` on failure.
    """
    if not string or not isinstance(string, str) or string.strip() == "":
        return None
    s = string.strip()
    base = re.sub(r"\d+\.?$", "", informat.lower().rstrip("."))
    patterns = _DATE_INFORMAT_MAP.get(base, [])
    for fmt in patterns:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def format_sas_date(dt: Any, fmt: str) -> str:
    """Format a ``date``/``datetime``/SAS-date-number using a SAS format name."""
    if dt is None:
        return ""
    if isinstance(dt, (int, float)):
        try:
            from datetime import timedelta
            dt = _SAS_EPOCH + timedelta(days=int(dt))
        except Exception:
            return str(dt)
    if not isinstance(dt, (date, datetime)):
        return str(dt)

    key = re.sub(r"\.$", "", fmt.lower())
    pattern = _DATE_FORMAT_MAP.get(key)
    if pattern:
        result = dt.strftime(pattern)
        # SAS uppercases month abbreviations for date9 etc.
        if "b" in pattern.lower():
            result = result.upper()
        return result
    # Fallback: try mmddyy10 style
    return dt.strftime("%m/%d/%Y")


# ---------------------------------------------------------------------------
# Fixed-width file reader (wrapping pd.read_fwf)
# ---------------------------------------------------------------------------

def read_fwf_sas(
    filepath: str,
    colspecs: List[Tuple[int, int]],
    names: List[str],
    dtypes: Optional[Dict[str, type]] = None,
    truncover: bool = False,
    missover: bool = False,
    pad: bool = False,
    firstobs: int = 1,
    obs: Optional[int] = None,
    encoding: str = "latin-1",
) -> pd.DataFrame:
    """Read a fixed-width file with SAS-like options.

    Parameters
    ----------
    filepath : str
        Path to the text file.
    colspecs : list of (start, end) tuples
        0-based column positions for ``pd.read_fwf``.
    names : list of str
        Column names.
    dtypes : dict, optional
        Column name → Python type overrides.
    truncover : bool
        If ``True``, short lines yield missing values instead of errors.
    missover : bool
        Same effect as *truncover* for our purposes.
    pad : bool
        If ``True``, short lines are padded with blanks.
    firstobs : int
        1-based first observation to read.
    obs : int, optional
        Last observation to read (1-based).
    encoding : str
        File encoding.
    """
    skiprows = firstobs - 1 if firstobs > 1 else 0
    nrows = (obs - firstobs + 1) if obs is not None else None

    on_bad = "warn" if (truncover or missover or pad) else "error"

    df = pd.read_fwf(
        filepath,
        colspecs=colspecs,
        names=names,
        skiprows=skiprows,
        nrows=nrows,
        encoding=encoding,
        on_bad_lines=on_bad if hasattr(pd, "__version__") else None,
    )

    if dtypes:
        for col, typ in dtypes.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(typ)
                except (TypeError, ValueError):
                    pass
    return df


# ---------------------------------------------------------------------------
# Delimited file reader (wrapping pd.read_csv)
# ---------------------------------------------------------------------------

def read_csv_sas(
    filepath: str,
    names: Optional[List[str]] = None,
    delimiter: str = ",",
    dsd: bool = True,
    firstobs: int = 1,
    obs: Optional[int] = None,
    encoding: str = "latin-1",
    header: Optional[int] = None,
    dtypes: Optional[Dict[str, type]] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a delimited file with SAS-like options.

    Parameters
    ----------
    dsd : bool
        If ``True``, treat consecutive delimiters as separate (SAS DSD
        also handles quoted strings, which ``pd.read_csv`` does by default).
    dlm / delimiter : str
        Field delimiter.
    """
    skiprows = firstobs - 1 if firstobs > 1 else 0
    nrows = (obs - firstobs + 1) if obs is not None else None

    # SAS DSD: consecutive delimiters mean missing values
    skipinitialspace = not dsd

    df = pd.read_csv(
        filepath,
        sep=delimiter,
        names=names,
        header=header,
        skiprows=skiprows,
        nrows=nrows,
        encoding=encoding,
        skipinitialspace=skipinitialspace,
        keep_default_na=True,
        dtype=dtypes if dtypes else None,
        **kwargs,
    )
    return df


# ---------------------------------------------------------------------------
# Inline data reader (SAS ``datalines`` / ``cards``)
# ---------------------------------------------------------------------------

def read_datalines(
    data_string: str,
    input_spec: Union[List[str], List[Tuple[str, Any]]],
    delimiter: Optional[str] = None,
    dsd: bool = False,
    multiline: int = 1,
    at_at: bool = False,
    date_informats: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Parse an inline data block (SAS ``datalines``).

    Parameters
    ----------
    data_string : str
        The raw text between ``datalines;`` and ``;``.
    input_spec : list
        Either a list of column names (simple list-mode input) **or** a list
        of tuples ``(name, spec)`` where *spec* can be:
        - ``'$'`` or ``'$N'`` for character (optionally with max width N)
        - ``'N.'`` or ``'N.D'`` for numeric column (width.decimals)
        - ``'informat_name'`` for date/custom informats
        - ``int`` for column-mode fixed-width (position)
        - ``(start, end)`` for column ranges
        - ``None`` for default list-mode numeric
    delimiter : str, optional
        Override delimiter; default is whitespace.
    dsd : bool
        Handle quoted strings and consecutive delimiters.
    multiline : int
        Number of raw lines per observation (for ``#n`` patterns).
    at_at : bool
        If ``True``, multiple observations may appear on a single line
        (``@@`` trailing).
    date_informats : dict, optional
        ``{column_name: informat_name}`` for automatic date parsing.
    """
    lines = data_string.strip().split("\n")
    lines = [ln for ln in lines if ln.strip()]

    # Determine simple vs complex spec
    if input_spec and isinstance(input_spec[0], str):
        col_names = list(input_spec)
        col_specs = [(name, None) for name in col_names]
    else:
        col_specs = list(input_spec)
        col_names = [cs[0] for cs in col_specs]

    rows: List[Dict[str, Any]] = []

    if multiline > 1:
        # Group lines into observations
        i = 0
        while i + multiline - 1 < len(lines):
            group = lines[i: i + multiline]
            combined_tokens: List[str] = []
            for g_line in group:
                if delimiter:
                    combined_tokens.extend(g_line.strip().split(delimiter))
                else:
                    combined_tokens.extend(g_line.split())
            row = _parse_tokens(combined_tokens, col_specs, date_informats)
            rows.append(row)
            i += multiline
    elif at_at:
        # All tokens across all lines form a pool
        all_tokens: List[str] = []
        for line in lines:
            if delimiter:
                all_tokens.extend(line.strip().split(delimiter))
            else:
                all_tokens.extend(line.split())
        n_cols = len(col_specs)
        idx = 0
        while idx + n_cols <= len(all_tokens):
            tokens = all_tokens[idx: idx + n_cols]
            row = _parse_tokens(tokens, col_specs, date_informats)
            rows.append(row)
            idx += n_cols
    else:
        for line in lines:
            if delimiter:
                tokens = line.strip().split(delimiter)
            else:
                tokens = line.split()
            row = _parse_tokens(tokens, col_specs, date_informats)
            rows.append(row)

    df = pd.DataFrame(rows, columns=col_names)
    return df


def _parse_tokens(
    tokens: List[str],
    col_specs: List[Tuple[str, Any]],
    date_informats: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Parse a list of tokens into a row dict according to *col_specs*."""

    row: Dict[str, Any] = {}
    date_informats = date_informats or {}

    for i, (name, spec) in enumerate(col_specs):
        raw = tokens[i].strip() if i < len(tokens) else ""

        if name in date_informats:
            if raw == "" or raw == ".":
                row[name] = np.nan
            else:
                parsed = parse_sas_date(raw, date_informats[name])
                if parsed is not None:
                    from datetime import timedelta
                    row[name] = (_SAS_EPOCH + timedelta(0)).year  # placeholder
                    row[name] = (parsed - _SAS_EPOCH).days
                else:
                    row[name] = np.nan
            continue

        if spec is not None:
            spec_str = str(spec).strip()
            if spec_str.startswith("$"):
                # Character column
                row[name] = raw if raw != "." else ""
                continue
            if spec_str.endswith(".") or "." in spec_str:
                # Possible informat – try date then numeric
                base = re.sub(r"\d+\.?\d*$", "", spec_str.lower())
                if base in ("mmddyy", "date", "ddmmyy", "yymmdd", "monyy", "anydtdte"):
                    if raw == "" or raw == ".":
                        row[name] = np.nan
                    else:
                        parsed = parse_sas_date(raw, base)
                        if parsed is not None:
                            row[name] = (parsed - _SAS_EPOCH).days
                        else:
                            row[name] = np.nan
                    continue
                if base in ("comma", "dollar"):
                    cleaned = raw.replace("$", "").replace(",", "").strip()
                    try:
                        row[name] = float(cleaned)
                    except ValueError:
                        row[name] = np.nan
                    continue

        # Default: try numeric, fall back to string
        if raw == "" or raw == ".":
            row[name] = np.nan
        else:
            try:
                row[name] = float(raw)
                if row[name] == int(row[name]):
                    row[name] = int(row[name])
            except ValueError:
                row[name] = raw

    return row


# ---------------------------------------------------------------------------
# Convenience: read SAS-style text files with list-mode input
# ---------------------------------------------------------------------------

def read_sas_list_input(
    filepath: str,
    names: List[str],
    dtypes: Optional[Dict[str, str]] = None,
    date_informats: Optional[Dict[str, str]] = None,
    delimiter: Optional[str] = None,
    truncover: bool = False,
    missover: bool = False,
    pad: bool = False,
    firstobs: int = 1,
    obs: Optional[int] = None,
    encoding: str = "latin-1",
) -> pd.DataFrame:
    """Read a text file using SAS list-mode input (space-delimited by default).

    This is simpler than ``read_fwf_sas`` for files where columns are
    separated by whitespace or a specific delimiter.
    """
    sep = delimiter if delimiter else r"\s+"
    skiprows = firstobs - 1 if firstobs > 1 else 0
    nrows = (obs - firstobs + 1) if obs is not None else None

    df = pd.read_csv(
        filepath,
        sep=sep,
        names=names,
        header=None,
        skiprows=skiprows,
        nrows=nrows,
        encoding=encoding,
        engine="python" if delimiter is None else None,
        na_values=["."],
        keep_default_na=True,
    )

    if date_informats:
        from .sas_functions import sas_input
        for col, ifmt in date_informats.items():
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x, fmt=ifmt: (
                        sas_input(str(x), fmt) if pd.notna(x) else np.nan
                    )
                )

    if dtypes:
        for col, dt in dtypes.items():
            if col in df.columns:
                if dt == "$" or dt.startswith("$"):
                    df[col] = df[col].astype(str)
                else:
                    try:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    except Exception:
                        pass
    return df
