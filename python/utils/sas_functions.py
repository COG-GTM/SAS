"""
Python equivalents for SAS DATA step functions.

Each function handles missing values (NaN) the way SAS does — SAS propagates
missing in most cases, but aggregate functions like mean() and sum() skip
missing values.

Categories:
- String functions (compress, scan, substr, find, etc.)
- Numeric functions (sas_mean, sas_sum, sas_round, etc.)
- Random number functions (rand, ranuni, rannor, streaminit)
- Date functions (yrdif, intck, intnx, mdy, weekday, etc.)
- Type conversion functions (sas_input, sas_put, sas_inputn)
- Regex functions (prxparse, prxmatch)
"""

from __future__ import annotations

import datetime
import math
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_missing(value: Any) -> bool:
    """Return True if *value* is NaN, None, or empty/blank string."""
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


def _apply_to_series(func, series, *args, **kwargs):
    """Apply a scalar function element-wise to a Series."""
    return series.apply(lambda x: func(x, *args, **kwargs))


# ---------------------------------------------------------------------------
# 2a. String functions
# ---------------------------------------------------------------------------

def compress(
    string: Union[str, pd.Series],
    chars: Optional[str] = None,
    modifiers: Optional[str] = None,
) -> Union[str, pd.Series]:
    """Remove (or keep) characters from *string*.

    Without modifiers, removes *chars* (default: spaces).
    Modifiers: 'k'=keep, 'd'=digits, 'a'=alpha, 's'=whitespace,
    'p'=punctuation, 'l'=lowercase, 'u'=uppercase.
    """
    if isinstance(string, pd.Series):
        return string.apply(lambda s: compress(s, chars, modifiers))
    if _is_missing(string):
        return string

    char_set = set(chars) if chars else set()
    mods = (modifiers or "").lower()

    # Build character classes from modifiers
    if "d" in mods:
        char_set.update("0123456789")
    if "a" in mods:
        char_set.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "s" in mods:
        char_set.update(" \t\n\r\f\v")
    if "l" in mods:
        char_set.update("abcdefghijklmnopqrstuvwxyz")
    if "u" in mods:
        char_set.update("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "p" in mods:
        import string as _string
        char_set.update(_string.punctuation)

    if not char_set and not modifiers:
        char_set = {" "}

    if "k" in mods:
        # Keep only characters in char_set
        return "".join(c for c in string if c in char_set)
    else:
        # Remove characters in char_set
        return "".join(c for c in string if c not in char_set)


def scan(
    string: Union[str, pd.Series],
    n: int,
    delimiters: Optional[str] = None,
) -> Union[str, pd.Series]:
    """Extract the *n*-th word (1-based). Negative *n* counts from end."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: scan(s, n, delimiters))
    if _is_missing(string):
        return ""
    if delimiters:
        pattern = "[" + re.escape(delimiters) + "]+"
    else:
        pattern = r"[\s,;:!?.\-]+"
    words = [w for w in re.split(pattern, string.strip()) if w]
    if not words:
        return ""
    idx = n - 1 if n > 0 else n  # 1-based → 0-based; negative stays
    try:
        return words[idx]
    except IndexError:
        return ""


def substr(
    string: Union[str, pd.Series],
    pos: int,
    length: Optional[int] = None,
) -> Union[str, pd.Series]:
    """Extract substring. SAS uses 1-based positions."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: substr(s, pos, length))
    if _is_missing(string):
        return ""
    start = pos - 1  # 1-based → 0-based
    if start < 0:
        start = 0
    if length is None:
        return string[start:]
    return string[start : start + length]


def find(
    string: Union[str, pd.Series],
    target: str,
    modifier: str = "",
    startpos: int = 1,
) -> Union[int, pd.Series]:
    """Find substring. Returns 1-based position or 0 if not found."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: find(s, target, modifier, startpos))
    if _is_missing(string):
        return 0
    s = string
    t = target
    if "i" in modifier.lower():
        s = s.lower()
        t = t.lower()
    idx = s.find(t, startpos - 1)
    return idx + 1 if idx >= 0 else 0


def findw(
    string: Union[str, pd.Series],
    word: str,
    delimiters: str = " ",
    modifier: str = "",
) -> Union[int, pd.Series]:
    """Find whole word. Returns 1-based position or 0."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: findw(s, word, delimiters, modifier))
    if _is_missing(string):
        return 0
    flags = re.IGNORECASE if "i" in modifier.lower() else 0
    pattern = r"\b" + re.escape(word) + r"\b"
    m = re.search(pattern, string, flags)
    return m.start() + 1 if m else 0


def tranwrd(
    string: Union[str, pd.Series],
    from_str: str,
    to_str: str,
) -> Union[str, pd.Series]:
    """Replace all occurrences of *from_str* with *to_str*."""
    if isinstance(string, pd.Series):
        return string.str.replace(from_str, to_str, regex=False)
    if _is_missing(string):
        return string
    return string.replace(from_str, to_str)


def translate(
    string: Union[str, pd.Series],
    to_chars: str,
    from_chars: str,
) -> Union[str, pd.Series]:
    """Character-level translation."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: translate(s, to_chars, from_chars))
    if _is_missing(string):
        return string
    table = str.maketrans(from_chars, to_chars)
    return string.translate(table)


def propcase(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Title case."""
    if isinstance(string, pd.Series):
        return string.str.title()
    if _is_missing(string):
        return string
    return string.title()


def upcase(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Upper-case."""
    if isinstance(string, pd.Series):
        return string.str.upper()
    if _is_missing(string):
        return string
    return string.upper()


def lowcase(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Lower-case."""
    if isinstance(string, pd.Series):
        return string.str.lower()
    if _is_missing(string):
        return string
    return string.lower()


def catx(sep: str, *args: Any) -> str:
    """Concatenate with separator, stripping blanks & ignoring missing."""
    parts = []
    for a in args:
        if _is_missing(a):
            continue
        s = str(a).strip()
        if s:
            parts.append(s)
    return sep.join(parts)


def cats(*args: Any) -> str:
    """Concatenate after stripping blanks from each argument."""
    parts = []
    for a in args:
        if _is_missing(a):
            continue
        parts.append(str(a).strip())
    return "".join(parts)


def cat(*args: Any) -> str:
    """Simple concatenation without stripping."""
    parts = []
    for a in args:
        if _is_missing(a):
            parts.append("")
        else:
            parts.append(str(a))
    return "".join(parts)


def left(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Left-align (strip leading blanks)."""
    if isinstance(string, pd.Series):
        return string.str.lstrip()
    if _is_missing(string):
        return string
    return string.lstrip()


def trimn(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Remove trailing blanks. Returns empty string for blank input."""
    if isinstance(string, pd.Series):
        return string.str.rstrip()
    if _is_missing(string):
        return ""
    return string.rstrip()


def strip(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Remove leading and trailing blanks."""
    if isinstance(string, pd.Series):
        return string.str.strip()
    if _is_missing(string):
        return ""
    return string.strip()


def compbl(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Compress multiple blanks to a single blank."""
    if isinstance(string, pd.Series):
        return string.str.replace(r" +", " ", regex=True)
    if _is_missing(string):
        return string
    return re.sub(r" +", " ", string)


def lengthn(string: Union[str, pd.Series]) -> Union[int, pd.Series]:
    """Length excluding trailing blanks. Returns 0 for blank/missing."""
    if isinstance(string, pd.Series):
        return string.apply(lengthn)
    if _is_missing(string):
        return 0
    return len(string.rstrip())


def anydigit(
    string: Union[str, pd.Series],
    startpos: int = 1,
) -> Union[int, pd.Series]:
    """Position of first digit (1-based) or 0."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: anydigit(s, startpos))
    if _is_missing(string):
        return 0
    m = re.search(r"\d", string[startpos - 1 :])
    return m.start() + startpos if m else 0


def anyalpha(
    string: Union[str, pd.Series],
    startpos: int = 1,
) -> Union[int, pd.Series]:
    """Position of first alpha character (1-based) or 0."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: anyalpha(s, startpos))
    if _is_missing(string):
        return 0
    m = re.search(r"[a-zA-Z]", string[startpos - 1 :])
    return m.start() + startpos if m else 0


def notalpha(string: Union[str, pd.Series]) -> Union[int, pd.Series]:
    """Position of first non-alpha character (1-based) or 0."""
    if isinstance(string, pd.Series):
        return string.apply(notalpha)
    if _is_missing(string):
        return 0
    m = re.search(r"[^a-zA-Z]", string)
    return m.start() + 1 if m else 0


def notdigit(string: Union[str, pd.Series]) -> Union[int, pd.Series]:
    """Position of first non-digit character (1-based) or 0."""
    if isinstance(string, pd.Series):
        return string.apply(notdigit)
    if _is_missing(string):
        return 0
    m = re.search(r"[^0-9]", string)
    return m.start() + 1 if m else 0


def notalnum(string: Union[str, pd.Series]) -> Union[int, pd.Series]:
    """Position of first non-alphanumeric character (1-based) or 0."""
    if isinstance(string, pd.Series):
        return string.apply(notalnum)
    if _is_missing(string):
        return 0
    m = re.search(r"[^a-zA-Z0-9]", string)
    return m.start() + 1 if m else 0


def spedis(string1: str, string2: str) -> int:
    """SAS spelling distance.

    Cost model (per operation, scaled by 100/max(len(s1),len(s2))):
    - deletion:      10
    - insertion:      20
    - replacement:    50 (first char) / 25 (other)
    - transposition:  25 (first char) / 10 (other)
    """
    if _is_missing(string1) or _is_missing(string2):
        return 0
    s1 = string1.upper()
    s2 = string2.upper()
    if s1 == s2:
        return 0

    base_len = max(len(s1), len(s2))
    if base_len == 0:
        return 0

    cost = 0
    s1_list = list(s1)
    s2_list = list(s2)

    i = 0
    while i < len(s1_list) and i < len(s2_list):
        if s1_list[i] != s2_list[i]:
            # Check transposition
            if (
                i + 1 < len(s1_list)
                and i + 1 < len(s2_list)
                and s1_list[i] == s2_list[i + 1]
                and s1_list[i + 1] == s2_list[i]
            ):
                tcost = 25 if i == 0 else 10
                cost += tcost
                # Swap to align
                s1_list[i], s1_list[i + 1] = s1_list[i + 1], s1_list[i]
                i += 2
                continue
            # Replacement
            rcost = 50 if i == 0 else 25
            cost += rcost
            i += 1
            continue
        i += 1

    # Remaining characters → deletion or insertion
    if len(s1_list) > len(s2_list):
        cost += (len(s1_list) - len(s2_list)) * 10  # deletion
    elif len(s2_list) > len(s1_list):
        cost += (len(s2_list) - len(s1_list)) * 20  # insertion

    return int(cost * 100 / base_len)


def countw(
    string: Union[str, pd.Series],
    delimiters: Optional[str] = None,
) -> Union[int, pd.Series]:
    """Count words."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: countw(s, delimiters))
    if _is_missing(string):
        return 0
    s = string.strip()
    if not s:
        return 0
    if delimiters:
        pattern = "[" + re.escape(delimiters) + "]+"
    else:
        pattern = r"\s+"
    return len([w for w in re.split(pattern, s) if w])


def count(
    string: Union[str, pd.Series],
    substring: str,
) -> Union[int, pd.Series]:
    """Count occurrences of *substring*."""
    if isinstance(string, pd.Series):
        return string.str.count(re.escape(substring))
    if _is_missing(string):
        return 0
    return string.count(substring)


def reverse(string: Union[str, pd.Series]) -> Union[str, pd.Series]:
    """Reverse string."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: s[::-1] if not _is_missing(s) else s)
    if _is_missing(string):
        return string
    return string[::-1]


def verify(
    string: Union[str, pd.Series],
    chars: str,
) -> Union[int, pd.Series]:
    """Position of first char in string NOT in *chars*. 0 if all in set."""
    if isinstance(string, pd.Series):
        return string.apply(lambda s: verify(s, chars))
    if _is_missing(string):
        return 0
    char_set = set(chars)
    for i, c in enumerate(string):
        if c not in char_set:
            return i + 1
    return 0


# ---------------------------------------------------------------------------
# 2b. Numeric functions
# ---------------------------------------------------------------------------

def _collect_args(*args) -> np.ndarray:
    """Flatten args into a 1-D numpy float array."""
    vals: list = []
    for a in args:
        if isinstance(a, (list, tuple, np.ndarray, pd.Series)):
            vals.extend(a)
        else:
            vals.append(a)
    return np.array(vals, dtype=float)


def sas_mean(*args) -> float:
    """Mean of non-missing values. NaN if all missing."""
    arr = _collect_args(*args)
    if np.all(np.isnan(arr)):
        return float("nan")
    return float(np.nanmean(arr))


def sas_sum(*args) -> float:
    """Sum of non-missing values. Returns 0 if all missing (SAS behaviour)."""
    arr = _collect_args(*args)
    if np.all(np.isnan(arr)):
        return 0.0
    return float(np.nansum(arr))


def sas_n(*args) -> int:
    """Count of non-missing values."""
    arr = _collect_args(*args)
    return int(np.count_nonzero(~np.isnan(arr)))


def sas_nmiss(*args) -> int:
    """Count of missing values."""
    arr = _collect_args(*args)
    return int(np.count_nonzero(np.isnan(arr)))


def largest(k: int, *args) -> float:
    """K-th largest non-missing value (1 = largest)."""
    arr = _collect_args(*args)
    valid = arr[~np.isnan(arr)]
    if len(valid) < k:
        return float("nan")
    valid.sort()
    return float(valid[-k])


def smallest(k: int, *args) -> float:
    """K-th smallest non-missing value (1 = smallest)."""
    arr = _collect_args(*args)
    valid = arr[~np.isnan(arr)]
    if len(valid) < k:
        return float("nan")
    valid.sort()
    return float(valid[k - 1])


def sas_round(value: float, round_to: float = 1) -> float:
    """Round to nearest *round_to*, rounding 0.5 away from zero."""
    if _is_missing(value):
        return float("nan")
    if round_to == 0:
        return float(value)
    # Use Decimal for correct rounding-half-away-from-zero
    d = Decimal(str(value)) / Decimal(str(round_to))
    rounded = d.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return float(rounded * Decimal(str(round_to)))


def sas_int(value: float) -> Union[int, float]:
    """Truncate toward zero."""
    if _is_missing(value):
        return float("nan")
    return math.trunc(value)


def sas_ceil(value: float) -> Union[int, float]:
    """Ceiling."""
    if _is_missing(value):
        return float("nan")
    return math.ceil(value)


def sas_floor(value: float) -> Union[int, float]:
    """Floor."""
    if _is_missing(value):
        return float("nan")
    return math.floor(value)


def sas_abs(value: float) -> float:
    """Absolute value."""
    if _is_missing(value):
        return float("nan")
    return abs(value)


def sas_sqrt(value: float) -> float:
    """Square root."""
    if _is_missing(value):
        return float("nan")
    return math.sqrt(value)


def sas_log(value: float) -> float:
    """Natural log."""
    if _is_missing(value):
        return float("nan")
    return math.log(value)


def sas_exp(value: float) -> float:
    """Exponential (e^x)."""
    if _is_missing(value):
        return float("nan")
    return math.exp(value)


def sas_mod(a: float, b: float) -> float:
    """Modulo."""
    if _is_missing(a) or _is_missing(b) or b == 0:
        return float("nan")
    return a % b


def sas_constant(name: str, *args) -> float:
    """Return mathematical constants.

    'pi' → math.pi, 'e' → math.e,
    'exactint',n → largest exact integer for n-byte float.
    """
    name_lower = name.lower()
    if name_lower == "pi":
        return math.pi
    if name_lower == "e":
        return math.e
    if name_lower == "exactint":
        n = args[0] if args else 8
        # Number of bits in mantissa for an n-byte IEEE 754 float
        if n == 8:
            return float(2**53)
        if n == 4:
            return float(2**24)
        if n == 3:
            return float(2**16)
        return float(2 ** (n * 8 - 1))
    raise ValueError(f"Unknown constant: {name}")


def lag(series: pd.Series, n: int = 1) -> pd.Series:
    """Wrapper around ``series.shift(n)``."""
    return series.shift(n)


def lag2(series: pd.Series) -> pd.Series:
    """``series.shift(2)``."""
    return series.shift(2)


def dif(series: pd.Series, n: int = 1) -> pd.Series:
    """``series.diff(n)``."""
    return series.diff(n)


def call_sortn(row_values: list) -> list:
    """Sort values in place; missing values sort to the end."""
    non_missing = []
    missing_count = 0
    for v in row_values:
        if _is_missing(v):
            missing_count += 1
        else:
            non_missing.append(v)
    non_missing.sort()
    result = non_missing + [float("nan")] * missing_count
    # Mutate in place
    for i, v in enumerate(result):
        row_values[i] = v
    return row_values


def missing(value: Any) -> bool:
    """Returns True if value is NaN, None, or empty string."""
    return _is_missing(value)


def call_missing(*args) -> list:
    """Set all values to missing (NaN). Returns a list of NaN values."""
    return [float("nan")] * len(args)


# ---------------------------------------------------------------------------
# 2c. Random number functions
# ---------------------------------------------------------------------------

def rand(distribution: str, *params) -> float:
    """Generate a random number from the named distribution."""
    dist = distribution.lower()
    if dist == "uniform":
        return float(np.random.random())
    if dist == "normal":
        mean = params[0] if len(params) > 0 else 0
        std = params[1] if len(params) > 1 else 1
        return float(np.random.normal(mean, std))
    if dist == "bernoulli":
        p = params[0] if params else 0.5
        return float(np.random.binomial(1, p))
    if dist == "integer":
        lo = int(params[0])
        hi = int(params[1])
        return float(np.random.randint(lo, hi + 1))
    raise ValueError(f"Unknown distribution: {distribution}")


def ranuni(seed: Optional[int] = None) -> float:
    """Uniform random [0, 1). If seed > 0, set seed first."""
    if seed is not None and seed > 0:
        np.random.seed(seed)
    return float(np.random.random())


def rannor(seed: Optional[int] = None) -> float:
    """Standard normal random. If seed > 0, set seed first."""
    if seed is not None and seed > 0:
        np.random.seed(seed)
    return float(np.random.standard_normal())


def streaminit(seed: int) -> None:
    """Set the global random seed."""
    np.random.seed(seed)


# ---------------------------------------------------------------------------
# 2d. Date functions
# ---------------------------------------------------------------------------

def _to_date(d: Any) -> datetime.date:
    """Coerce to datetime.date."""
    if isinstance(d, pd.Timestamp):
        return d.date()
    if isinstance(d, datetime.datetime):
        return d.date()
    if isinstance(d, datetime.date):
        return d
    raise TypeError(f"Cannot convert {type(d)} to date")


def yrdif(
    start_date: Any,
    end_date: Any,
    basis: str = "AGE",
) -> float:
    """Year difference between two dates.

    For 'AGE' basis, uses dateutil.relativedelta for exact computation.
    """
    start = _to_date(start_date)
    end = _to_date(end_date)
    rd = relativedelta(end, start)
    return rd.years + rd.months / 12.0 + rd.days / 365.25


def intck(
    interval: str,
    start_date: Any,
    end_date: Any,
) -> int:
    """Count complete intervals between two dates.

    Supported: 'year', 'month', 'qtr', 'week', 'day'.
    """
    start = _to_date(start_date)
    end = _to_date(end_date)
    iv = interval.lower()
    if iv == "day":
        return (end - start).days
    if iv == "week":
        return (end - start).days // 7
    if iv == "month":
        return (end.year - start.year) * 12 + (end.month - start.month)
    if iv == "qtr":
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return months // 3
    if iv == "year":
        return end.year - start.year
    raise ValueError(f"Unknown interval: {interval}")


def intnx(
    interval: str,
    date: Any,
    n: int,
    alignment: str = "beginning",
) -> datetime.date:
    """Advance *date* by *n* intervals.

    Alignment: 'beginning' (default), 'middle', 'end', 'sameday'.
    """
    d = _to_date(date)
    iv = interval.lower()
    align = alignment.lower()

    if iv == "day":
        result = d + datetime.timedelta(days=n)
        return result  # alignment doesn't matter for days

    if iv == "week":
        result = d + datetime.timedelta(weeks=n)
        if align == "beginning":
            # Monday of that week (SAS uses Sunday; adjust: weekday 0=Mon)
            result = result - datetime.timedelta(days=result.weekday())
            # SAS convention: week starts Sunday
            result = result - datetime.timedelta(days=1)
            if result < d + datetime.timedelta(weeks=n) - datetime.timedelta(days=6):
                result = result + datetime.timedelta(days=7)
            # Simpler: just get the Sunday of that week
            result = d + datetime.timedelta(weeks=n)
            dow = (result.isoweekday() % 7)  # 0=Sun
            result = result - datetime.timedelta(days=dow)
        elif align == "end":
            result = d + datetime.timedelta(weeks=n)
            dow = (result.isoweekday() % 7)
            result = result - datetime.timedelta(days=dow) + datetime.timedelta(days=6)
        elif align == "middle":
            result = d + datetime.timedelta(weeks=n)
            dow = (result.isoweekday() % 7)
            result = result - datetime.timedelta(days=dow) + datetime.timedelta(days=3)
        # sameday: just return result
        return result

    if iv == "month":
        new_date = d + relativedelta(months=n)
        if align == "beginning":
            return new_date.replace(day=1)
        if align == "end":
            # Last day of month
            if new_date.month == 12:
                return new_date.replace(day=31)
            next_month = new_date.replace(day=1) + relativedelta(months=1)
            return next_month - datetime.timedelta(days=1)
        if align == "middle":
            first = new_date.replace(day=1)
            if new_date.month == 12:
                last = new_date.replace(day=31)
            else:
                last = (first + relativedelta(months=1)) - datetime.timedelta(days=1)
            mid_day = (first.day + last.day) // 2
            return new_date.replace(day=mid_day)
        # sameday
        return new_date

    if iv == "year":
        new_date = d + relativedelta(years=n)
        if align == "beginning":
            return new_date.replace(month=1, day=1)
        if align == "end":
            return new_date.replace(month=12, day=31)
        if align == "middle":
            return new_date.replace(month=7, day=1)
        return new_date

    if iv == "qtr":
        new_date = d + relativedelta(months=n * 3)
        qtr_month = ((new_date.month - 1) // 3) * 3 + 1
        if align == "beginning":
            return new_date.replace(month=qtr_month, day=1)
        if align == "end":
            end_month = qtr_month + 2
            first_of_next = datetime.date(new_date.year, end_month, 1) + relativedelta(months=1)
            return first_of_next - datetime.timedelta(days=1)
        if align == "middle":
            mid_month = qtr_month + 1
            return new_date.replace(month=mid_month, day=15)
        return new_date

    raise ValueError(f"Unknown interval: {interval}")


def mdy(month: int, day_val: int, year: int) -> datetime.date:
    """Create date from components."""
    return datetime.date(year, month, day_val)


def weekday(date: Any) -> int:
    """Day of week, SAS convention: 1=Sunday, 2=Monday, ..., 7=Saturday."""
    d = _to_date(date)
    return (d.isoweekday() % 7) + 1


def day(date: Any) -> int:
    """Day of month."""
    return _to_date(date).day


def month(date: Any) -> int:
    """Month."""
    return _to_date(date).month


def year(date: Any) -> int:
    """Year."""
    return _to_date(date).year


def today() -> datetime.date:
    """Today's date."""
    return datetime.date.today()


def datepart(datetime_val: Any) -> datetime.date:
    """Extract date from datetime."""
    if isinstance(datetime_val, pd.Timestamp):
        return datetime_val.date()
    if isinstance(datetime_val, datetime.datetime):
        return datetime_val.date()
    if isinstance(datetime_val, datetime.date):
        return datetime_val
    raise TypeError(f"Cannot extract date from {type(datetime_val)}")


def sas_date_literal(s: str) -> datetime.date:
    """Parse SAS date literals like ``'01Jan2017'd`` to datetime.date."""
    cleaned = re.sub(r"['\"]?[dD]$", "", s.strip().strip("'").strip('"'))
    return datetime.datetime.strptime(cleaned, "%d%b%Y").date()


# ---------------------------------------------------------------------------
# 2e. Type conversion functions
# ---------------------------------------------------------------------------

def sas_input(
    string: Any,
    informat: Any,
) -> Any:
    """Convert string to numeric or date based on informat.

    *informat* can be a string (e.g. ``'8.'``, ``'mmddyy10.'``) or a
    :class:`~python.utils.sas_formats.SASInformat` instance.
    """
    from python.utils.sas_formats import SASInformat as _SASInformat

    if isinstance(informat, _SASInformat):
        return informat.convert(string)

    if _is_missing(string):
        return float("nan")

    fmt = informat.lower().rstrip(".")
    s = str(string).strip()

    # Numeric informats
    if re.match(r"^\d+$", fmt):
        try:
            return float(s)
        except ValueError:
            return float("nan")

    # Dollar / comma informats
    if fmt.startswith("dollar") or fmt.startswith("comma"):
        cleaned = s.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return float("nan")

    # Date informats
    if fmt.startswith("mmddyy"):
        for pat in ("%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.datetime.strptime(s, pat).date()
            except ValueError:
                continue
        return float("nan")

    if fmt.startswith("date9"):
        try:
            return datetime.datetime.strptime(s, "%d%b%Y").date()
        except ValueError:
            return float("nan")

    if fmt.startswith("date7"):
        try:
            return datetime.datetime.strptime(s, "%d%b%y").date()
        except ValueError:
            return float("nan")

    # Fallback: try float
    try:
        return float(s)
    except ValueError:
        return float("nan")


def sas_put(value: Any, format_name: Any) -> str:
    """Convert numeric/date to string based on format name.

    *format_name* can be a string or a :class:`~python.utils.sas_formats.SASFormat`.
    """
    from python.utils.sas_formats import SASFormat as _SASFormat

    if isinstance(format_name, _SASFormat):
        return str(format_name.format(value))

    if _is_missing(value):
        return "."

    fmt = format_name.lower().rstrip(".")

    # Date formats
    if fmt == "date9":
        d = _to_date(value)
        return d.strftime("%d%b%Y").upper()

    if fmt.startswith("mmddyy"):
        d = _to_date(value)
        return d.strftime("%m/%d/%Y")

    if fmt == "weekdate":
        d = _to_date(value)
        return d.strftime("%A, %B %d, %Y")

    # Dollar formats
    m = re.match(r"dollar(\d+)\.?(\d+)?", fmt)
    if m:
        decimals = int(m.group(2)) if m.group(2) else 0
        if decimals:
            return f"${value:,.{decimals}f}"
        return f"${value:,.0f}"

    # Comma formats
    if fmt.startswith("comma"):
        return f"{value:,}"

    # Numeric (e.g. "8", "12", "best")
    if re.match(r"^\d+$", fmt) or fmt.startswith("best"):
        return str(value)

    return str(value)


def sas_inputn(
    string: Any,
    format_name: str,
    registry: Any = None,
) -> Any:
    """Dynamic numeric input using a format name from the registry."""
    if registry is None:
        from python.utils.sas_formats import default_registry
        registry = default_registry

    # Strip width/decimal spec (e.g. "Exp1944fmt8." → "Exp1944fmt")
    clean_name = re.sub(r"\d*\.\d*$", "", format_name).rstrip(".")

    fmt = registry.get(clean_name)
    if fmt is None:
        # Try as standard informat
        return sas_input(string, format_name)
    if hasattr(fmt, "convert"):
        return fmt.convert(string)
    return sas_input(string, format_name)


# ---------------------------------------------------------------------------
# 2f. Regex functions
# ---------------------------------------------------------------------------

def prxparse(pattern: str) -> re.Pattern:
    """Compile a regex pattern.

    SAS uses ``/pattern/`` delimiters — strip those if present.
    """
    p = pattern.strip()
    if p.startswith("/") and p.endswith("/"):
        p = p[1:-1]
    elif p.startswith("/") and "/" in p[1:]:
        last_slash = p.rindex("/")
        flags_str = p[last_slash + 1 :]
        p = p[1:last_slash]
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        return re.compile(p, flags)
    return re.compile(p)


def prxmatch(
    pattern_or_compiled: Union[str, re.Pattern],
    string: Union[str, pd.Series],
) -> Union[int, pd.Series]:
    """Match regex. Returns 1-based position or 0 if no match."""
    if isinstance(pattern_or_compiled, str):
        compiled = prxparse(pattern_or_compiled)
    else:
        compiled = pattern_or_compiled

    if isinstance(string, pd.Series):
        return string.apply(lambda s: prxmatch(compiled, s))
    if _is_missing(string):
        return 0
    m = compiled.search(string)
    return m.start() + 1 if m else 0
