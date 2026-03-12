"""
Replicates SAS PROC FORMAT functionality.

SAS formats map values to labels for display; SAS informats map input strings
to values during data reading.  This module provides:

- SASFormat      – value formats (display)
- SASInformat    – invalue formats (input conversion)
- FormatRegistry – singleton registry of named formats/informats
- All concrete format definitions used in the Learning SAS codebase
"""

from __future__ import annotations

import datetime
import math
import re
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Core classes
# ---------------------------------------------------------------------------

class SASFormat:
    """A SAS value format – maps data values to display labels.

    Parameters
    ----------
    name : str
        Format name (e.g. ``'$gender'``, ``'age'``).
    mappings : list[tuple]
        Each element is either:
        - ``(value, label)``  for exact-match mappings, or
        - ``(low, high, inclusive_low, inclusive_high, label)`` for ranges.
    other : str | None
        Fallback label when no mapping matches.
    missing : str | None
        Label for missing values (NaN / None / ``' '``).
    multilabel : bool
        If True, :meth:`format` returns a *list* of all matching labels.
    picture : callable | None
        If set, used instead of mappings (picture format).
    date_format_range : callable | None
        If set, used for the "passthrough formatted date" range in
        ``Registration``-style formats.
    """

    def __init__(
        self,
        name: str,
        mappings: Optional[List[tuple]] = None,
        other: Optional[str] = None,
        missing: Optional[str] = None,
        multilabel: bool = False,
        picture: Optional[Callable] = None,
        date_format_range: Optional[List[tuple]] = None,
    ) -> None:
        self.name = name
        self.other = other
        self.missing = missing
        self.multilabel = multilabel
        self.picture = picture

        # Separate exact vs range mappings
        self.exact: dict[Any, str] = {}
        self.ranges: list[tuple] = []
        self.date_format_ranges: list[tuple] = date_format_range or []

        if mappings:
            for m in mappings:
                if len(m) == 2:
                    self.exact[m[0]] = m[1]
                elif len(m) == 5:
                    self.ranges.append(m)

        # Sort ranges by lower bound for efficient lookup
        def _sort_key(r):
            lo = r[0]
            if lo is None or lo == -math.inf:
                return -math.inf
            try:
                return float(lo)
            except (TypeError, ValueError):
                return -math.inf

        self.ranges.sort(key=_sort_key)

    # -- single-value formatting -------------------------------------------

    def format(self, value: Any) -> Any:
        """Apply the format to a single value, returning the label string."""
        # Picture format
        if self.picture is not None:
            if _is_missing(value):
                return self.missing if self.missing is not None else value
            return self.picture(value)

        # Missing check
        if _is_missing(value):
            if self.missing is not None:
                return self.missing
            if self.other is not None:
                return self.other
            return value

        # Multilabel mode – return ALL matching labels
        if self.multilabel:
            labels: list[str] = []
            if value in self.exact:
                labels.append(self.exact[value])
            for lo, hi, inc_lo, inc_hi, label in self.ranges:
                if _in_range(value, lo, hi, inc_lo, inc_hi):
                    labels.append(label)
            for lo, hi, inc_lo, inc_hi, fmt_fn in self.date_format_ranges:
                if _in_range(value, lo, hi, inc_lo, inc_hi):
                    labels.append(fmt_fn(value))
            if labels:
                return labels
            if self.other is not None:
                return [self.other]
            return [str(value)]

        # Exact match first
        if value in self.exact:
            return self.exact[value]

        # String coercion exact match (e.g. int 1 matching key '1')
        str_val = str(value)
        if str_val in self.exact:
            return self.exact[str_val]

        # Date format ranges (Registration-style)
        for lo, hi, inc_lo, inc_hi, fmt_fn in self.date_format_ranges:
            if _in_range(value, lo, hi, inc_lo, inc_hi):
                return fmt_fn(value)

        # Range match
        for lo, hi, inc_lo, inc_hi, label in self.ranges:
            if _in_range(value, lo, hi, inc_lo, inc_hi):
                return label

        # Other / fallback
        if self.other is not None:
            return self.other
        return value

    # -- Series formatting -------------------------------------------------

    def format_series(self, series: pd.Series) -> pd.Series:
        """Apply the format to a pandas Series, returning a new Series."""
        return series.map(self.format)


class SASInformat:
    """A SAS invalue format – maps input strings to numeric values.

    Parameters
    ----------
    name : str
        Informat name (e.g. ``'Convert'``).
    mappings : list[tuple]
        ``(input_value, output_value)`` pairs.
    other : float | str | None
        Value for unmatched inputs.  ``None`` → NaN, ``'_same_'`` → pass-through.
    same_range : tuple | None
        ``(low, high)`` for a range that uses ``_same_`` pass-through.
    upcase : bool
        If ``True``, upper-case the input before lookup.
    nested_ranges : list[tuple] | None
        Ranges that delegate to another informat or pass-through with a format.
        Each element: ``(lo, hi, inc_lo, inc_hi, handler)`` where *handler* is
        either ``'_same_'`` or a callable(value) → numeric.
    """

    def __init__(
        self,
        name: str,
        mappings: Optional[List[Tuple[Any, Any]]] = None,
        other: Optional[Any] = None,
        same_range: Optional[Tuple] = None,
        upcase: bool = False,
        nested_ranges: Optional[List[tuple]] = None,
    ) -> None:
        self.name = name
        self.exact: dict[Any, Any] = {}
        if mappings:
            for k, v in mappings:
                self.exact[k] = v
        self.other = other
        self.same_range = same_range
        self.upcase = upcase
        self.nested_ranges = nested_ranges or []

    def convert(self, value: Any) -> Any:
        """Convert a single input value to its numeric equivalent."""
        if _is_missing(value):
            return float("nan")

        lookup = value
        if self.upcase and isinstance(lookup, str):
            lookup = lookup.strip().upper()

        # Exact match
        if lookup in self.exact:
            return self.exact[lookup]

        # Try numeric conversion for same_range
        num_val = _try_numeric(lookup)

        # same_range check
        if self.same_range is not None and num_val is not None:
            lo, hi = self.same_range
            if lo <= num_val <= hi:
                return num_val

        # Nested ranges
        for lo, hi, inc_lo, inc_hi, handler in self.nested_ranges:
            if num_val is not None and _in_range(num_val, lo, hi, inc_lo, inc_hi):
                if handler == "_same_":
                    return num_val
                return handler(num_val)

        # Other
        if self.other == "_same_":
            if num_val is not None:
                return num_val
            return float("nan")
        if self.other is not None:
            return self.other
        return float("nan")

    def convert_series(self, series: pd.Series) -> pd.Series:
        """Apply the informat to a pandas Series."""
        return series.map(self.convert)


class FormatRegistry:
    """Singleton registry of SASFormat and SASInformat instances."""

    _instance: Optional["FormatRegistry"] = None

    def __new__(cls) -> "FormatRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._formats: dict[str, Union[SASFormat, SASInformat]] = {}
        return cls._instance

    def register(self, fmt: Union[SASFormat, SASInformat]) -> None:
        """Register a format/informat by its name (case-insensitive)."""
        self._formats[fmt.name.lower()] = fmt

    def get(self, name: str) -> Union[SASFormat, SASInformat, None]:
        """Retrieve a format/informat by name (case-insensitive)."""
        return self._formats.get(name.lower())

    def apply(self, series: pd.Series, format_name: str) -> pd.Series:
        """Convenience: look up *format_name* and apply it to *series*."""
        fmt = self.get(format_name)
        if fmt is None:
            raise KeyError(f"Format '{format_name}' not found in registry")
        if isinstance(fmt, SASFormat):
            return fmt.format_series(series)
        return fmt.convert_series(series)

    def reset(self) -> None:
        """Clear all registered formats (useful for testing)."""
        self._formats.clear()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_missing(value: Any) -> bool:
    """Return True if *value* is NaN, None, or blank string."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return False


def _in_range(
    value: Any,
    lo: Any,
    hi: Any,
    inc_lo: bool,
    inc_hi: bool,
) -> bool:
    """Check whether *value* falls within [lo, hi] with inclusivity flags."""
    try:
        v = float(value) if not isinstance(value, (datetime.date, datetime.datetime, pd.Timestamp)) else value
    except (TypeError, ValueError):
        return False

    # Resolve sentinels
    if lo is None or lo == -math.inf:
        lo_ok = True
    else:
        lo_ok = (v >= lo) if inc_lo else (v > lo)

    if hi is None or hi == math.inf:
        hi_ok = True
    else:
        hi_ok = (v <= hi) if inc_hi else (v < hi)

    return lo_ok and hi_ok


def _try_numeric(value: Any) -> Optional[float]:
    """Try to convert *value* to float; return None on failure."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Data-driven format helpers
# ---------------------------------------------------------------------------

def create_format_from_dataframe(
    df: pd.DataFrame,
    fmtname: str,
    start_col: str,
    label_col: str,
    other_label: Optional[str] = None,
) -> SASFormat:
    """Create a SASFormat from a control DataFrame (``proc format cntlin=``).

    Parameters
    ----------
    df : DataFrame
        Must contain at least *start_col* and *label_col*.
    fmtname : str
        Name for the resulting format.
    start_col, label_col : str
        Column names for lookup keys and labels.
    other_label : str | None
        Fallback label for unmatched values.
    """
    mappings = [(row[start_col], row[label_col]) for _, row in df.iterrows()]
    return SASFormat(name=fmtname, mappings=mappings, other=other_label)


def create_exposure_formats(
    data_matrix: List[List[int]],
    years: List[int],
    job_codes: List[str],
) -> List[SASInformat]:
    """Create dynamic Exp<year>fmt informats from an exposure data matrix.

    Parameters
    ----------
    data_matrix : list[list[int]]
        Each inner list has one value per job code for that year.
    years : list[int]
        The years (e.g. [1944, 1945, 1946, 1947, 1948, 1949]).
    job_codes : list[str]
        Job code letters (e.g. ['A', 'B', 'C', 'D', 'E']).

    Returns
    -------
    list[SASInformat]
        One informat per year.
    """
    formats: list[SASInformat] = []
    for i, year in enumerate(years):
        mappings = list(zip(job_codes, data_matrix[i]))
        fmt = SASInformat(
            name=f"Exp{year}fmt",
            mappings=mappings,
            other=float("nan"),
            upcase=True,
        )
        formats.append(fmt)
    return formats


# ---------------------------------------------------------------------------
# Concrete format definitions
# ---------------------------------------------------------------------------

def _build_default_registry() -> FormatRegistry:
    """Populate and return the default FormatRegistry."""
    reg = FormatRegistry()
    reg.reset()

    # ---- Value formats (display) -----------------------------------------

    # 1. $gender (Create_Datasets.sas 234-237)
    reg.register(SASFormat(
        name="$gender",
        mappings=[("M", "Male"), ("F", "Female")],
        missing="Not entered",
        other="Miscoded",
    ))

    # 2. age (Create_Datasets.sas 238-240)
    reg.register(SASFormat(
        name="age",
        mappings=[
            (-math.inf, 29, True, True, "Less than 30"),
            (30, 50, True, True, "30 to 50"),
            (51, math.inf, True, True, "51+"),
        ],
    ))

    # 3. $likert (Create_Datasets.sas 241-245)
    reg.register(SASFormat(
        name="$likert",
        mappings=[
            ("1", "Strongly disagree"),
            ("2", "Disagree"),
            ("3", "No opinion"),
            ("4", "Agree"),
            ("5", "Strongly agree"),
        ],
    ))

    # 4. $dx (Create_Datasets.sas 274-280)
    reg.register(SASFormat(
        name="$dx",
        mappings=[
            ("1", "Routine Visit"),
            ("2", "Cold"),
            ("3", "Heart Problems"),
            ("4", "GI Problems"),
            ("5", "Psychiatric"),
            ("6", "Injury"),
            ("7", "Infection"),
        ],
    ))

    # 5. $yesno (Create_Datasets.sas 861-863)
    reg.register(SASFormat(
        name="$yesno",
        mappings=[
            ("Y", "Yes"),
            ("1", "Yes"),
            ("N", "No"),
            ("0", "No"),
        ],
        missing="Not Given",
    ))

    # 6. $size (Create_Datasets.sas 864-867)
    reg.register(SASFormat(
        name="$size",
        mappings=[
            ("S", "Small"),
            ("M", "Medium"),
            ("L", "Large"),
        ],
        missing="Missing",
    ))

    # 7. groupfmt (Create_Datasets.sas 215)
    reg.register(SASFormat(
        name="groupfmt",
        mappings=[(0, "A"), (1, "B"), (2, "C")],
    ))

    # 8. two (Create_Datasets.sas 1052-1056)
    reg.register(SASFormat(
        name="two",
        mappings=[
            (-math.inf, 3, True, True, "Group 1"),
            (4, 5, True, True, "Group 2"),
        ],
        missing="Missing",
        other="Other values",
    ))

    # 9. $Three (Programs Used in the Second Edition.sas 296-298)
    reg.register(SASFormat(
        name="$Three",
        mappings=[
            ("1", "Disagreement"),
            ("2", "Disagreement"),
            ("3", "No opinion"),
            ("4", "Agreement"),
            ("5", "Agreement"),
        ],
    ))

    # 10. Agefmt (Programs 1375-1377)
    reg.register(SASFormat(
        name="Agefmt",
        mappings=[
            (-math.inf, 20, True, False, "Group One"),
            (20, 40, True, False, "Group Two"),
            (40, math.inf, True, True, "Group Three"),
        ],
    ))

    # 11. Chol_Group (Programs 2209-2211)
    reg.register(SASFormat(
        name="Chol_Group",
        mappings=[
            (-math.inf, 200, True, False, "Low"),
            (200, math.inf, True, True, "High"),
        ],
    ))

    # 12. Colors (Programs 2420-2425)
    reg.register(SASFormat(
        name="Colors",
        mappings=[
            (1, "Yellow"),
            (2, "Blue"),
            (3, "Red"),
            (4, "Green"),
        ],
        missing="Missing",
    ))

    # 13. AgeGroup (Programs 2368-2371)
    reg.register(SASFormat(
        name="AgeGroup",
        mappings=[
            (-math.inf, 30, True, False, "Less than 30"),
            (30, 60, True, False, "30 to 59"),
            (60, math.inf, True, True, "60 and higher"),
        ],
    ))

    # 14. $Agree_Disagree (Programs 2372-2375)
    reg.register(SASFormat(
        name="$Agree_Disagree",
        mappings=[
            ("1", "Generally disagree"),
            ("2", "Generally disagree"),
            ("3", "No opinion"),
            ("4", "Generally agree"),
            ("5", "Generally agree"),
        ],
    ))

    # 15. AgeGroup_multilabel (Programs 3303-3310)
    reg.register(SASFormat(
        name="AgeGroup_multilabel",
        mappings=[
            (0, 20, True, False, "0 to <20"),
            (20, 40, True, False, "20 to <40"),
            (40, 60, True, False, "40 to <60"),
            (60, 80, True, False, "60 to <80"),
            (80, math.inf, True, True, "80 +"),
            (0, 50, True, False, "Less than 50"),
            (50, math.inf, True, True, "> or = to 50"),
        ],
        multilabel=True,
    ))

    # 16. Registration (Programs 3266-3268) – date-based format
    _reg_boundary_lo = datetime.date(2018, 1, 1)
    _reg_boundary_hi = datetime.date(2018, 12, 31)
    _reg_boundary_hi2 = datetime.date(2019, 1, 1)

    def _reg_date_fmt(val):
        if isinstance(val, (pd.Timestamp, datetime.datetime)):
            return val.strftime("%m/%d/%Y")
        if isinstance(val, datetime.date):
            return val.strftime("%m/%d/%Y")
        return str(val)

    reg.register(SASFormat(
        name="Registration",
        mappings=[
            (datetime.date.min, _reg_boundary_lo, True, False, "Not Open"),
            (_reg_boundary_hi2, datetime.date.max, True, True, "Too Late"),
        ],
        date_format_range=[
            (_reg_boundary_lo, _reg_boundary_hi, True, True, _reg_date_fmt),
        ],
    ))

    # 17. NameLookup (Programs 3167-3172)
    reg.register(SASFormat(
        name="NameLookup",
        mappings=[
            (122, "Salt"),
            (188, "Sugar"),
            (101, "Cereal"),
            (755, "Eggs"),
        ],
        other="",
    ))

    # 18. Pctfmt (Programs 2585) – picture format
    reg.register(SASFormat(
        name="Pctfmt",
        picture=lambda val: f"{val:.1f}%",
    ))

    # ---- Invalue formats (input conversion) ------------------------------

    # 19. Convert (Programs 3077-3085)
    reg.register(SASInformat(
        name="Convert",
        mappings=[
            ("A+", 100),
            ("A", 96),
            ("A-", 92),
            ("B+", 88),
            ("B", 84),
            ("B-", 80),
            ("C+", 76),
            ("C", 72),
            ("F", 65),
        ],
    ))

    # 20. ReadTemp (Programs 3139-3142)
    reg.register(SASInformat(
        name="ReadTemp",
        mappings=[("N", 98.6)],
        other=float("nan"),
        same_range=(96, 106),
        upcase=True,
    ))

    # 21. ReadGrade (Programs 3152-3157)
    reg.register(SASInformat(
        name="ReadGrade",
        mappings=[
            ("A", 95),
            ("B", 85),
            ("C", 75),
            ("F", 65),
        ],
        other="_same_",
        upcase=True,
    ))

    # 22. PriceLookup (Programs 3173-3178)
    reg.register(SASInformat(
        name="PriceLookup",
        mappings=[
            ("Salt", 3.76),
            ("Sugar", 4.99),
            ("Cereal", 5.97),
            ("Eggs", 2.65),
        ],
        other=float("nan"),
    ))

    # 23. YearExp (Programs 3285-3290)
    reg.register(SASInformat(
        name="YearExp",
        mappings=[
            (1946, 250),
            (1947, 244),
            (1948, 240),
            (1949, 200),
            (1950, 188),
            (1951, 150),
            (1952, 100),
        ],
    ))

    # 24. Exp (Programs 3292-3294) – nested informat
    yearexp_fmt = reg.get("YearExp")

    def _yearexp_handler(val):
        return yearexp_fmt.convert(int(val))

    reg.register(SASInformat(
        name="Exp",
        nested_ranges=[
            (-math.inf, 1946, True, False, "_same_"),
            (1946, 1952, True, True, _yearexp_handler),
            (1952, math.inf, False, True, "_same_"),
        ],
    ))

    # 25. $ICDFMT placeholder – built from a control dataset at runtime
    # We provide a factory; see create_format_from_dataframe()

    # 26. Exp1944fmt–Exp1949fmt (Programs 3366-3388)
    exposure_data = [
        [220, 180, 210, 110, 90],
        [202, 170, 208, 100, 85],
        [150, 110, 150, 60, 50],
        [105, 56, 88, 40, 30],
        [60, 30, 40, 20, 10],
        [45, 22, 22, 10, 8],
    ]
    exposure_years = [1944, 1945, 1946, 1947, 1948, 1949]
    exposure_codes = ["A", "B", "C", "D", "E"]
    for fmt in create_exposure_formats(exposure_data, exposure_years, exposure_codes):
        reg.register(fmt)

    return reg


# Module-level default registry
default_registry: FormatRegistry = _build_default_registry()
