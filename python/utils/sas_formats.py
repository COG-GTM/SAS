"""SAS format and informat equivalents for Python.

Provides SASFormat (value → label mapping), SASInformat (string → numeric),
and a FormatRegistry with all formats found in the example SAS programs.
"""

import math
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# SASFormat – maps values to display labels
# ---------------------------------------------------------------------------

class SASFormat:
    """SAS VALUE format: maps raw values to display labels.

    Supports exact-match (dict), range-match (interval list), and special
    fallbacks for ``other`` and ``missing`` (NaN / None / empty-string).

    Parameters
    ----------
    name : str
        Format name (e.g. ``'$gender'``, ``'age'``).
    exact : dict, optional
        ``{value: label}`` for exact matches.
    ranges : list of tuples, optional
        Each tuple is ``(low, high, label, low_exclusive, high_exclusive)``.
        *low* / *high* may be the strings ``'low'`` or ``'high'`` for open
        bounds.
    other : str or None
        Label returned when no match is found.
    missing : str or None
        Label returned for missing values (NaN / None / ``''``).
    is_char : bool
        ``True`` when the format works on character (string) values.
    nested_format : dict, optional
        ``{(low, high): format_name}`` for [format.] picture ranges.
    """

    def __init__(
        self,
        name: str,
        exact: Optional[Dict[Any, str]] = None,
        ranges: Optional[List[Tuple]] = None,
        other: Optional[str] = None,
        missing: Optional[str] = None,
        is_char: bool = False,
        nested_format: Optional[Dict[Tuple, str]] = None,
    ):
        self.name = name
        self.exact = exact or {}
        self.ranges = ranges or []
        self.other = other
        self.missing = missing
        self.is_char = is_char
        self.nested_format = nested_format or {}

    # ------------------------------------------------------------------
    def _is_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, float) and math.isnan(value):
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    # ------------------------------------------------------------------
    def format(self, value: Any) -> str:  # noqa: A003 – shadows builtin
        """Return the label for *value*, following SAS precedence."""
        # 1. Missing
        if self._is_missing(value):
            if self.missing is not None:
                return self.missing
            if self.other is not None:
                return self.other
            return ""

        # 2. Exact match
        lookup = str(value) if self.is_char else value
        if lookup in self.exact:
            return self.exact[lookup]

        # For character formats, also try the raw value
        if self.is_char and value in self.exact:
            return self.exact[value]

        # 3. Range match (numeric only)
        if not self.is_char:
            try:
                num = float(value)
            except (TypeError, ValueError):
                num = None
            if num is not None:
                for low, high, label, low_excl, high_excl in self.ranges:
                    lo = -math.inf if low == "low" else float(low)
                    hi = math.inf if high == "high" else float(high)
                    if low_excl:
                        lo_ok = num > lo
                    else:
                        lo_ok = num >= lo
                    if high_excl:
                        hi_ok = num < hi
                    else:
                        hi_ok = num <= hi
                    if lo_ok and hi_ok:
                        # Check for nested format
                        for (nlo, nhi), fmt_name in self.nested_format.items():
                            n_lo = -math.inf if nlo == "low" else float(nlo)
                            n_hi = math.inf if nhi == "high" else float(nhi)
                            if n_lo <= num <= n_hi:
                                return _apply_builtin_format(num, fmt_name)
                        return label

        # 4. Other
        if self.other is not None:
            return self.other
        return str(value)


# ---------------------------------------------------------------------------
# SASInformat – maps input strings to numeric values
# ---------------------------------------------------------------------------

class SASInformat:
    """SAS INVALUE informat: converts input strings to numeric values.

    Parameters
    ----------
    name : str
        Informat name.
    exact : dict
        ``{string: numeric_value}`` for exact matches.
    ranges : list of tuples, optional
        ``(low, high, value_or_same, low_excl, high_excl)`` where
        *value_or_same* is a number or ``'_same_'``.
    other : float or str or None
        Default for unmatched values – may be ``'_same_'``.
    upcase : bool
        If ``True``, input strings are upper-cased before matching.
    nested_informat : dict, optional
        ``{(low, high): informat_name}`` for [informat.] ranges.
    """

    def __init__(
        self,
        name: str,
        exact: Optional[Dict[str, float]] = None,
        ranges: Optional[List[Tuple]] = None,
        other: Optional[Union[float, str]] = None,
        upcase: bool = False,
        nested_informat: Optional[Dict[Tuple, str]] = None,
    ):
        self.name = name
        self.exact = exact or {}
        self.ranges = ranges or []
        self.other = other
        self.upcase = upcase
        self.nested_informat = nested_informat or {}

    def convert(self, value: str) -> float:
        """Convert *value* (a string) to a numeric result."""
        s = str(value).strip()
        if self.upcase:
            s = s.upper()

        # Exact match
        if s in self.exact:
            return self.exact[s]

        # Try interpreting as numeric for range matching
        try:
            num = float(s)
        except (TypeError, ValueError):
            num = None

        if num is not None:
            for low, high, result, low_excl, high_excl in self.ranges:
                lo = -math.inf if low == "low" else float(low)
                hi = math.inf if high == "high" else float(high)
                lo_ok = num > lo if low_excl else num >= lo
                hi_ok = num < hi if high_excl else num <= hi
                if lo_ok and hi_ok:
                    # Check for nested informat
                    for (nlo, nhi), ifmt_name in self.nested_informat.items():
                        n_lo = -math.inf if nlo == "low" else float(nlo)
                        n_hi = math.inf if nhi == "high" else float(nhi)
                        if n_lo <= num <= n_hi:
                            reg = _get_global_registry()
                            ifmt = reg.get_informat(ifmt_name)
                            if ifmt is not None:
                                return ifmt.convert(s)
                            return num
                    if result == "_same_":
                        return num
                    return float(result)

        # Other
        if self.other is not None:
            if self.other == "_same_":
                if num is not None:
                    return num
                return float("nan")
            return float(self.other)
        return float("nan")


# ---------------------------------------------------------------------------
# Built-in SAS format helper
# ---------------------------------------------------------------------------

def _apply_builtin_format(value: Any, fmt_name: str) -> str:
    """Apply a simple built-in SAS format name to *value*."""
    fmt_lower = fmt_name.lower().rstrip(".")
    # mmddyy10.
    if fmt_lower.startswith("mmddyy"):
        if isinstance(value, (date, datetime)):
            return value.strftime("%m/%d/%Y")
        # Interpret as SAS date number
        try:
            d = _sas_date_to_python(int(value))
            return d.strftime("%m/%d/%Y")
        except Exception:
            return str(value)
    # date9.
    if fmt_lower.startswith("date"):
        if isinstance(value, (date, datetime)):
            return value.strftime("%d%b%Y").upper()
        try:
            d = _sas_date_to_python(int(value))
            return d.strftime("%d%b%Y").upper()
        except Exception:
            return str(value)
    # dollar
    if fmt_lower.startswith("dollar"):
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
    # Numeric with width.d
    m = re.match(r"(\d+)\.(\d+)", fmt_name)
    if m:
        width = int(m.group(1))
        dec = int(m.group(2))
        try:
            return f"{float(value):{width}.{dec}f}"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


_SAS_EPOCH = date(1960, 1, 1)


def _sas_date_to_python(sas_date: int) -> date:
    from datetime import timedelta
    return _SAS_EPOCH + timedelta(days=sas_date)


# ---------------------------------------------------------------------------
# FormatRegistry
# ---------------------------------------------------------------------------

def _get_global_registry() -> "FormatRegistry":
    return registry


class FormatRegistry:
    """Stores and retrieves SAS formats and informats by name."""

    def __init__(self) -> None:
        self._formats: Dict[str, SASFormat] = {}
        self._informats: Dict[str, SASInformat] = {}

    def register_format(self, fmt: SASFormat) -> None:
        self._formats[fmt.name.lower().rstrip(".")] = fmt

    def register_informat(self, ifmt: SASInformat) -> None:
        self._informats[ifmt.name.lower().rstrip(".")] = ifmt

    def get_format(self, name: str) -> Optional[SASFormat]:
        return self._formats.get(name.lower().rstrip("."))

    def get_informat(self, name: str) -> Optional[SASInformat]:
        return self._informats.get(name.lower().rstrip("."))

    def list_formats(self) -> List[str]:
        return sorted(self._formats.keys())

    def list_informats(self) -> List[str]:
        return sorted(self._informats.keys())


# ---------------------------------------------------------------------------
# Global registry instance & pre-registered formats
# ---------------------------------------------------------------------------

registry = FormatRegistry()


def _register_all() -> None:
    """Pre-register every format/informat from the example SAS programs."""

    # ---- Create_Datasets.sas line 215 ----
    registry.register_format(SASFormat(
        "groupfmt",
        exact={0: "A", 1: "B", 2: "C"},
    ))

    # ---- Create_Datasets.sas lines 233-246 ----
    registry.register_format(SASFormat(
        "$gender",
        exact={"M": "Male", "F": "Female"},
        missing="Not entered",
        other="Miscoded",
        is_char=True,
    ))

    registry.register_format(SASFormat(
        "age",
        ranges=[
            ("low", 29, "Less than 30", False, False),
            (30, 50, "30 to 50", False, False),
            (51, "high", "51+", False, False),
        ],
    ))

    registry.register_format(SASFormat(
        "$likert",
        exact={"1": "Strongly disagree", "2": "Disagree",
               "3": "No opinion", "4": "Agree", "5": "Strongly agree"},
        is_char=True,
    ))

    # ---- Create_Datasets.sas lines 274-280 ----
    registry.register_format(SASFormat(
        "$dx",
        exact={"1": "Routine Visit", "2": "Cold", "3": "Heart Problems",
               "4": "GI Problems", "5": "Psychiatric", "6": "Injury",
               "7": "Infection"},
        is_char=True,
    ))

    # ---- Create_Datasets.sas lines 861-867 ----
    registry.register_format(SASFormat(
        "$yesno",
        exact={"Y": "Yes", "1": "Yes", "N": "No", "0": "No"},
        missing="Not Given",
        is_char=True,
    ))
    registry.register_format(SASFormat(
        "$size",
        exact={"S": "Small", "M": "Medium", "L": "Large"},
        missing="Missing",
        is_char=True,
    ))
    # Re-register $gender with college variant (same keys, different missing)
    registry.register_format(SASFormat(
        "$gender1",
        exact={"F": "Female", "M": "Male"},
        missing="Not Given",
        is_char=True,
    ))

    # ---- Create_Datasets.sas lines 1052-1056 ----
    registry.register_format(SASFormat(
        "two",
        ranges=[
            ("low", 3, "Group 1", False, False),
            (4, 5, "Group 2", False, False),
        ],
        missing="Missing",
        other="Other values",
    ))

    # ---- Programs Used in the Second Edition.sas lines 296-298 ----
    registry.register_format(SASFormat(
        "$three",
        exact={"1": "Disagreement", "2": "Disagreement",
               "3": "No opinion", "4": "Agreement", "5": "Agreement"},
        is_char=True,
    ))

    # ---- Programs lines 1375-1377 ----
    registry.register_format(SASFormat(
        "agefmt",
        ranges=[
            ("low", 20, "Group One", False, True),
            (20, 40, "Group Two", False, True),
            (40, "high", "Group Three", False, False),
        ],
    ))

    # ---- Programs lines 2209-2211 ----
    registry.register_format(SASFormat(
        "chol_group",
        ranges=[
            ("low", 200, "Low", False, True),
            (200, "high", "High", False, False),
        ],
    ))

    # ---- Programs lines 2368-2375 ----
    registry.register_format(SASFormat(
        "agegroup",
        ranges=[
            ("low", 30, "Less than 30", False, True),
            (30, 60, "30 to 59", False, True),
            (60, "high", "60 and higher", False, False),
        ],
    ))
    registry.register_format(SASFormat(
        "$agree_disagree",
        exact={"1": "Generally disagree", "2": "Generally disagree",
               "3": "No opinion",
               "4": "Generally agree", "5": "Generally agree"},
        is_char=True,
    ))

    # ---- Programs lines 2420-2425 ----
    registry.register_format(SASFormat(
        "colors",
        exact={1: "Yellow", 2: "Blue", 3: "Red", 4: "Green"},
        missing="Missing",
    ))

    # ---- Programs lines 3077-3085 ----
    registry.register_informat(SASInformat(
        "convert",
        exact={"A+": 100, "A": 96, "A-": 92,
               "B+": 88, "B": 84, "B-": 80,
               "C+": 76, "C": 72, "F": 65},
    ))

    # ---- Programs lines 3139-3142 ----
    registry.register_informat(SASInformat(
        "readtemp",
        exact={"N": 98.6},
        ranges=[
            (96, 106, "_same_", False, False),
        ],
        other=float("nan"),
        upcase=True,
    ))

    # ---- Programs lines 3152-3157 ----
    registry.register_informat(SASInformat(
        "readgrade",
        exact={"A": 95, "B": 85, "C": 75, "F": 65},
        other="_same_",
        upcase=True,
    ))

    # ---- Programs lines 3167-3178 ----
    registry.register_format(SASFormat(
        "namelookup",
        exact={122: "Salt", 188: "Sugar", 101: "Cereal", 755: "Eggs"},
        other=" ",
    ))
    registry.register_informat(SASInformat(
        "pricelookup",
        exact={"Salt": 3.76, "Sugar": 4.99, "Cereal": 5.97, "Eggs": 2.65},
        other=float("nan"),
    ))

    # ---- Programs lines 3266-3268 ----
    registry.register_format(SASFormat(
        "registration",
        ranges=[
            ("low", _sas_date_from_string("01Jan2018"), "Not Open", False, True),
            (_sas_date_from_string("01Jan2018"), _sas_date_from_string("31Dec2018"),
             "", False, False),
            (_sas_date_from_string("01Jan2019"), "high", "Too Late", False, False),
        ],
        nested_format={
            (_sas_date_from_string("01Jan2018"), _sas_date_from_string("31Dec2018")): "mmddyy10.",
        },
    ))

    # ---- Programs lines 3285-3294 ----
    registry.register_informat(SASInformat(
        "yearexp",
        exact={"1946": 250, "1947": 244, "1948": 240,
               "1949": 200, "1950": 188, "1951": 150, "1952": 100},
    ))
    registry.register_informat(SASInformat(
        "exp",
        ranges=[
            ("low", 1946, "_same_", False, True),
            (1952, "high", "_same_", True, False),
        ],
        nested_informat={
            (1946, 1952): "yearexp",
            ("low", 1946): "7.1",
            (1952, "high"): "7.1",
        },
    ))

    # ---- Programs lines 3303-3310 (multilabel AgeGroup) ----
    registry.register_format(SASFormat(
        "agegroup_ml",
        ranges=[
            (0, 20, "0 to <20", False, True),
            (20, 40, "20 to <40", False, True),
            (40, 60, "40 to <60", False, True),
            (60, 80, "60 to <80", False, True),
            (80, "high", "80 +", False, False),
            (0, 50, "Less than 50", False, True),
            (50, "high", "> or = to 50", False, False),
        ],
    ))


def _sas_date_from_string(s: str) -> int:
    """Convert a SAS date literal string like '01Jan2018' to a SAS date number."""
    dt = datetime.strptime(s, "%d%b%Y")
    return (dt.date() - _SAS_EPOCH).days


_register_all()
