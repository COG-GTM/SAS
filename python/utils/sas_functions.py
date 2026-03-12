"""Python equivalents of common SAS functions.

All scalar operations propagate NaN (matching SAS missing-value semantics).
Aggregate operations skip NaN values.
"""

import math
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional, Union

import numpy as np
from dateutil.relativedelta import relativedelta

from .sas_formats import registry as _registry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAS_EPOCH = date(1960, 1, 1)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    try:
        if np.isnan(value):
            return True
    except (TypeError, ValueError):
        pass
    return False


def _to_float(value: Any) -> float:
    """Convert to float, returning NaN for missing."""
    if _is_missing(value):
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


# ===================================================================
# STRING FUNCTIONS (~25)
# ===================================================================

def compress(source: str, chars: str = " ", modifiers: str = "") -> str:
    """SAS COMPRESS: remove characters from *source*.

    Modifiers: 'a' alpha, 'd' digit, 'i' ignore case (no-op in Python),
    'k' keep instead of remove, 'l' lowercase, 'p' punctuation,
    's' whitespace, 'u' uppercase, 't' trim trailing blanks, etc.
    """
    if _is_missing(source):
        return ""
    source = str(source)
    mods = modifiers.lower()

    remove_set = set(chars) if "s" not in mods else set(chars) | set(" \t\n\r")
    if "a" in mods:
        remove_set |= set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "d" in mods:
        remove_set |= set("0123456789")
    if "l" in mods:
        remove_set |= set("abcdefghijklmnopqrstuvwxyz")
    if "u" in mods:
        remove_set |= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if "p" in mods:
        import string as _string
        remove_set |= set(_string.punctuation)
    if "s" in mods:
        remove_set |= set(" \t\n\r\x0b\x0c")

    if "k" in mods:
        return "".join(ch for ch in source if ch in remove_set)
    else:
        return "".join(ch for ch in source if ch not in remove_set)


def scan(source: str, n: int, delimiters: str = " \t") -> str:
    """SAS SCAN: return the *n*-th word from *source*."""
    if _is_missing(source):
        return ""
    s = str(source)
    pattern = "[" + re.escape(delimiters) + "]+"
    words = re.split(pattern, s.strip())
    words = [w for w in words if w]
    if n < 0:
        n = len(words) + n + 1
    if n < 1 or n > len(words):
        return ""
    return words[n - 1]


def substr(source: str, pos: int, length: Optional[int] = None) -> str:
    """SAS SUBSTR: extract substring (1-based *pos*)."""
    if _is_missing(source):
        return ""
    s = str(source)
    start = max(pos - 1, 0)
    if length is None:
        return s[start:]
    return s[start:start + length]


def find(source: str, target: str, start: int = 1, modifier: str = "") -> int:
    """SAS FIND: return position (1-based) of *target* in *source*."""
    if _is_missing(source) or _is_missing(target):
        return 0
    s = str(source)
    t = str(target)
    if "i" in modifier.lower():
        s = s.lower()
        t = t.lower()
    if "t" in modifier.lower():
        s = s.strip()
        t = t.strip()
    idx = s.find(t, start - 1)
    return idx + 1 if idx >= 0 else 0


def findw(source: str, target: str, delimiters: str = " \t", modifier: str = "") -> int:
    """SAS FINDW: find whole word *target* in *source*, return 1-based pos."""
    if _is_missing(source) or _is_missing(target):
        return 0
    s = str(source)
    t = str(target)
    if "i" in modifier.lower():
        s = s.lower()
        t = t.lower()
    pattern = "[" + re.escape(delimiters) + "]+"
    words = re.split(pattern, s)
    pos = 0
    for word in words:
        start_idx = s.find(word, pos)
        if word == t:
            return start_idx + 1
        pos = start_idx + len(word)
    return 0


def tranwrd(source: str, target: str, replacement: str) -> str:
    """SAS TRANWRD: replace all occurrences of *target* with *replacement*."""
    if _is_missing(source):
        return ""
    return str(source).replace(str(target), str(replacement))


def translate(source: str, to_chars: str, from_chars: str) -> str:
    """SAS TRANSLATE: character-by-character translation."""
    if _is_missing(source):
        return ""
    s = str(source)
    table = str.maketrans(from_chars, to_chars)
    return s.translate(table)


def propcase(source: str) -> str:
    """SAS PROPCASE: title-case each word."""
    if _is_missing(source):
        return ""
    return str(source).title()


def upcase(source: str) -> str:
    """SAS UPCASE."""
    if _is_missing(source):
        return ""
    return str(source).upper()


def lowcase(source: str) -> str:
    """SAS LOWCASE."""
    if _is_missing(source):
        return ""
    return str(source).lower()


def catx(sep: str, *args: Any) -> str:
    """SAS CATX: concatenate with separator, stripping blanks, skipping missing."""
    parts = []
    for a in args:
        if not _is_missing(a):
            s = str(a).strip()
            if s:
                parts.append(s)
    return sep.join(parts)


def cats(*args: Any) -> str:
    """SAS CATS: strip and concatenate."""
    parts = []
    for a in args:
        if _is_missing(a):
            parts.append("")
        else:
            parts.append(str(a).strip())
    return "".join(parts)


def cat(*args: Any) -> str:
    """SAS CAT: concatenate without stripping."""
    parts = []
    for a in args:
        if _is_missing(a):
            parts.append("")
        else:
            parts.append(str(a))
    return "".join(parts)


def left(source: str) -> str:
    """SAS LEFT: left-align (strip leading blanks)."""
    if _is_missing(source):
        return ""
    return str(source).lstrip()


def trimn(source: str) -> str:
    """SAS TRIMN: remove trailing blanks; returns '' for blank string."""
    if _is_missing(source):
        return ""
    return str(source).rstrip()


def strip(source: str) -> str:
    """SAS STRIP: remove leading and trailing blanks."""
    if _is_missing(source):
        return ""
    return str(source).strip()


def compbl(source: str) -> str:
    """SAS COMPBL: compress multiple blanks to single blank."""
    if _is_missing(source):
        return ""
    return re.sub(r" {2,}", " ", str(source))


def lengthn(source: str) -> int:
    """SAS LENGTHN: length of trimmed string (0 for blank/missing)."""
    if _is_missing(source):
        return 0
    return len(str(source).rstrip())


def anydigit(source: str, start: int = 1) -> int:
    """SAS ANYDIGIT: 1-based position of first digit, 0 if none."""
    if _is_missing(source):
        return 0
    s = str(source)
    for i in range(start - 1, len(s)):
        if s[i].isdigit():
            return i + 1
    return 0


def anyalpha(source: str, start: int = 1) -> int:
    """SAS ANYALPHA: 1-based position of first alpha character."""
    if _is_missing(source):
        return 0
    s = str(source)
    for i in range(start - 1, len(s)):
        if s[i].isalpha():
            return i + 1
    return 0


def notalpha(source: str, start: int = 1) -> int:
    """SAS NOTALPHA: 1-based position of first non-alpha character."""
    if _is_missing(source):
        return 0
    s = str(source)
    for i in range(start - 1, len(s)):
        if not s[i].isalpha():
            return i + 1
    return 0


def notdigit(source: str, start: int = 1) -> int:
    """SAS NOTDIGIT: 1-based position of first non-digit character."""
    if _is_missing(source):
        return 0
    s = str(source)
    for i in range(start - 1, len(s)):
        if not s[i].isdigit():
            return i + 1
    return 0


def notalnum(source: str, start: int = 1) -> int:
    """SAS NOTALNUM: 1-based position of first non-alphanumeric character."""
    if _is_missing(source):
        return 0
    s = str(source)
    for i in range(start - 1, len(s)):
        if not s[i].isalnum():
            return i + 1
    return 0


def spedis(source: str, target: str) -> int:
    """SAS SPEDIS: generalised edit distance (percentage of target length).

    Operations: delete=100, insert=50, replace=200, first-char-change=250,
    swap=100, truncation=20. Returns 0 for identical strings.
    """
    if _is_missing(source) or _is_missing(target):
        return 0
    s = str(source).upper()
    t = str(target).upper()
    if s == t:
        return 0

    slen = len(s)
    tlen = len(t)
    if tlen == 0:
        return 0

    # Simple Levenshtein-based approximation with SAS-specific costs
    cost = 0
    i = 0
    j = 0
    while i < slen and j < tlen:
        if s[i] == t[j]:
            i += 1
            j += 1
            continue
        # Try swap
        if (i + 1 < slen and j + 1 < tlen and
                s[i] == t[j + 1] and s[i + 1] == t[j]):
            cost += 100  # swap cost
            i += 2
            j += 2
            continue
        # Replace
        replacement_cost = 250 if j == 0 else 200
        cost += replacement_cost
        i += 1
        j += 1

    # Remaining characters in source → insertions
    if i < slen:
        cost += (slen - i) * 50

    # Remaining characters in target → deletions
    if j < tlen:
        cost += (tlen - j) * 100

    return int(round(cost / tlen))


def countw(source: str, delimiters: str = " \t") -> int:
    """SAS COUNTW: count words separated by *delimiters*."""
    if _is_missing(source):
        return 0
    s = str(source).strip()
    if not s:
        return 0
    pattern = "[" + re.escape(delimiters) + "]+"
    words = re.split(pattern, s)
    return len([w for w in words if w])


def reverse(source: str) -> str:
    """SAS REVERSE: reverse a string."""
    if _is_missing(source):
        return ""
    return str(source)[::-1]


def verify(source: str, target: str) -> int:
    """SAS VERIFY: 1-based position of first char in *source* not in *target*."""
    if _is_missing(source) or _is_missing(target):
        return 0
    s = str(source)
    t = set(str(target))
    for i, ch in enumerate(s):
        if ch not in t:
            return i + 1
    return 0


# ===================================================================
# NUMERIC FUNCTIONS (~15)
# ===================================================================

def sas_mean(*args: Any) -> float:
    """SAS MEAN: arithmetic mean, skipping NaN."""
    vals = [_to_float(a) for a in args]
    valid = [v for v in vals if not math.isnan(v)]
    if not valid:
        return float("nan")
    return sum(valid) / len(valid)


def sas_sum(*args: Any) -> float:
    """SAS SUM: sum, skipping NaN (returns 0 if all missing)."""
    vals = [_to_float(a) for a in args]
    valid = [v for v in vals if not math.isnan(v)]
    if not valid:
        return 0.0
    return sum(valid)


def sas_n(*args: Any) -> int:
    """SAS N: count of non-missing numeric values."""
    return sum(1 for a in args if not math.isnan(_to_float(a)))


def sas_nmiss(*args: Any) -> int:
    """SAS NMISS: count of missing values."""
    return sum(1 for a in args if math.isnan(_to_float(a)))


def largest(k: int, *args: Any) -> float:
    """SAS LARGEST: *k*-th largest non-missing value (1-based)."""
    vals = sorted([_to_float(a) for a in args if not math.isnan(_to_float(a))],
                  reverse=True)
    if k < 1 or k > len(vals):
        return float("nan")
    return vals[k - 1]


def smallest(k: int, *args: Any) -> float:
    """SAS SMALLEST: *k*-th smallest non-missing value (1-based)."""
    vals = sorted([_to_float(a) for a in args if not math.isnan(_to_float(a))])
    if k < 1 or k > len(vals):
        return float("nan")
    return vals[k - 1]


def sas_round(value: Any, rounding_unit: float = 1.0) -> float:
    """SAS ROUND: round-half-away-from-zero (banker's rounding avoided)."""
    v = _to_float(value)
    if math.isnan(v):
        return float("nan")
    if rounding_unit == 0:
        return v
    r = _to_float(rounding_unit)
    if math.isnan(r) or r == 0:
        return v
    # Round-half-away-from-zero
    import decimal
    d_val = decimal.Decimal(str(v))
    d_unit = decimal.Decimal(str(r))
    result = (d_val / d_unit).quantize(
        decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP
    ) * d_unit
    return float(result)


def sas_int(value: Any) -> float:
    """SAS INT: truncate toward zero."""
    v = _to_float(value)
    if math.isnan(v):
        return float("nan")
    return float(int(v))


def call_sortn(*args: float) -> list:
    """SAS CALL SORTN: sort values in-place (returns sorted list, NaN last)."""
    vals = list(args)
    missing = [v for v in vals if _is_missing(v)]
    valid = sorted([v for v in vals if not _is_missing(v)])
    return valid + [float("nan")] * len(missing)


def missing(value: Any) -> int:
    """SAS MISSING: returns 1 if value is missing, 0 otherwise."""
    return 1 if _is_missing(value) else 0


def call_missing(*args: Any) -> list:
    """SAS CALL MISSING: return a list of NaN for each argument (set all to missing)."""
    return [float("nan")] * len(args)


def sas_abs(value: Any) -> float:
    """SAS ABS wrapper."""
    v = _to_float(value)
    return float("nan") if math.isnan(v) else abs(v)


def sas_sqrt(value: Any) -> float:
    """SAS SQRT wrapper."""
    v = _to_float(value)
    if math.isnan(v) or v < 0:
        return float("nan")
    return math.sqrt(v)


def sas_log(value: Any) -> float:
    """SAS LOG (natural log) wrapper."""
    v = _to_float(value)
    if math.isnan(v) or v <= 0:
        return float("nan")
    return math.log(v)


def sas_log10(value: Any) -> float:
    """SAS LOG10 wrapper."""
    v = _to_float(value)
    if math.isnan(v) or v <= 0:
        return float("nan")
    return math.log10(v)


def sas_exp(value: Any) -> float:
    """SAS EXP wrapper."""
    v = _to_float(value)
    if math.isnan(v):
        return float("nan")
    return math.exp(v)


def sas_max(*args: Any) -> float:
    """SAS MAX: maximum of non-missing values."""
    vals = [_to_float(a) for a in args]
    valid = [v for v in vals if not math.isnan(v)]
    if not valid:
        return float("nan")
    return max(valid)


def sas_min(*args: Any) -> float:
    """SAS MIN: minimum of non-missing values."""
    vals = [_to_float(a) for a in args]
    valid = [v for v in vals if not math.isnan(v)]
    if not valid:
        return float("nan")
    return min(valid)


def sas_mod(a: Any, b: Any) -> float:
    """SAS MOD: modulo."""
    va = _to_float(a)
    vb = _to_float(b)
    if math.isnan(va) or math.isnan(vb) or vb == 0:
        return float("nan")
    # SAS MOD keeps sign of dividend
    return math.fmod(va, vb)


def sas_ceil(value: Any) -> float:
    """SAS CEIL wrapper."""
    v = _to_float(value)
    return float("nan") if math.isnan(v) else float(math.ceil(v))


def sas_floor(value: Any) -> float:
    """SAS FLOOR wrapper."""
    v = _to_float(value)
    return float("nan") if math.isnan(v) else float(math.floor(v))


# ===================================================================
# DATE FUNCTIONS (~10)
# ===================================================================

def _python_date(value: Any) -> Optional[date]:
    """Try to interpret *value* as a Python date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if _is_missing(value):
        return None
    try:
        n = int(float(value))
        return _SAS_EPOCH + timedelta(days=n)
    except (TypeError, ValueError):
        return None


def _to_sas_date(d: date) -> int:
    return (d - _SAS_EPOCH).days


def yrdif(start: Any, end: Any, basis: str = "ACT/ACT") -> float:
    """SAS YRDIF: difference in years between two dates."""
    d1 = _python_date(start)
    d2 = _python_date(end)
    if d1 is None or d2 is None:
        return float("nan")
    delta = relativedelta(d2, d1)
    years = delta.years + delta.months / 12.0 + delta.days / 365.25
    return years


def intck(interval: str, start: Any, end: Any) -> Union[int, float]:
    """SAS INTCK: count of interval boundaries between two dates."""
    d1 = _python_date(start)
    d2 = _python_date(end)
    if d1 is None or d2 is None:
        return float("nan")

    intv = interval.lower().strip().strip("'\"")

    if intv == "year":
        return d2.year - d1.year
    elif intv == "month":
        return (d2.year - d1.year) * 12 + (d2.month - d1.month)
    elif intv == "qtr":
        q1 = (d1.year * 4) + (d1.month - 1) // 3
        q2 = (d2.year * 4) + (d2.month - 1) // 3
        return q2 - q1
    elif intv == "week":
        return (d2 - d1).days // 7
    elif intv == "day":
        return (d2 - d1).days
    else:
        return (d2 - d1).days


def intnx(interval: str, start: Any, increment: int,
           alignment: str = "beginning") -> Union[int, float]:
    """SAS INTNX: advance a date by *increment* intervals, return SAS date.

    *alignment*: 'beginning', 'middle', 'end', 'same' (or 'b','m','e','s').
    """
    d = _python_date(start)
    if d is None:
        return float("nan")

    intv = interval.lower().strip().strip("'\"")
    align = alignment.lower()[0] if alignment else "b"

    if intv == "year":
        new_date = d + relativedelta(years=increment)
        if align == "b":
            new_date = new_date.replace(month=1, day=1)
        elif align == "e":
            new_date = new_date.replace(month=12, day=31)
        elif align == "m":
            new_date = new_date.replace(month=7, day=1)
        # 's' keeps same day-of-year alignment
    elif intv == "month":
        new_date = d + relativedelta(months=increment)
        if align == "b":
            new_date = new_date.replace(day=1)
        elif align == "e":
            next_month = new_date + relativedelta(months=1)
            new_date = next_month.replace(day=1) - timedelta(days=1)
        elif align == "m":
            new_date = new_date.replace(day=15)
        # 's' keeps same day
    elif intv == "qtr":
        new_date = d + relativedelta(months=3 * increment)
        if align == "b":
            q_month = ((new_date.month - 1) // 3) * 3 + 1
            new_date = new_date.replace(month=q_month, day=1)
        elif align == "e":
            q_month = ((new_date.month - 1) // 3) * 3 + 3
            next_q = date(new_date.year, q_month, 1) + relativedelta(months=1)
            new_date = next_q - timedelta(days=1)
        elif align == "m":
            q_month = ((new_date.month - 1) // 3) * 3 + 2
            new_date = new_date.replace(month=q_month, day=15)
    elif intv == "week":
        new_date = d + timedelta(weeks=increment)
        if align == "b":
            new_date = new_date - timedelta(days=new_date.weekday())
        elif align == "e":
            new_date = new_date + timedelta(days=6 - new_date.weekday())
        elif align == "m":
            new_date = new_date - timedelta(days=new_date.weekday()) + timedelta(days=3)
    elif intv == "day":
        new_date = d + timedelta(days=increment)
    else:
        new_date = d + timedelta(days=increment)

    return _to_sas_date(new_date)


def mdy(month: int, day: int, year: int) -> Union[int, float]:
    """SAS MDY: create a SAS date from month/day/year."""
    try:
        d = date(int(year), int(month), int(day))
        return _to_sas_date(d)
    except (TypeError, ValueError):
        return float("nan")


def weekday(value: Any) -> Union[int, float]:
    """SAS WEEKDAY: day of week (1=Sunday, 2=Monday, ..., 7=Saturday)."""
    d = _python_date(value)
    if d is None:
        return float("nan")
    # Python: Monday=0..Sunday=6 → SAS: Sunday=1..Saturday=7
    return (d.weekday() + 2) % 7 or 7


def day(value: Any) -> Union[int, float]:
    """SAS DAY: day of month."""
    d = _python_date(value)
    if d is None:
        return float("nan")
    return d.day


def month(value: Any) -> Union[int, float]:
    """SAS MONTH: month number."""
    d = _python_date(value)
    if d is None:
        return float("nan")
    return d.month


def year(value: Any) -> Union[int, float]:
    """SAS YEAR: four-digit year."""
    d = _python_date(value)
    if d is None:
        return float("nan")
    return d.year


def today() -> int:
    """SAS TODAY: current date as SAS date number."""
    return _to_sas_date(date.today())


def datepart(value: Any) -> Union[int, float]:
    """SAS DATEPART: extract date portion from a datetime."""
    if isinstance(value, datetime):
        return _to_sas_date(value.date())
    if isinstance(value, date):
        return _to_sas_date(value)
    if _is_missing(value):
        return float("nan")
    # If it's already a SAS date number, return as-is
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return float("nan")


def sas_date_literal(date_str: str) -> int:
    """Convert a SAS date literal (e.g. '01jan2002'd) to a SAS date number."""
    s = date_str.strip().strip("'\"").rstrip("d").rstrip("D")
    try:
        dt = datetime.strptime(s, "%d%b%Y")
        return _to_sas_date(dt.date())
    except ValueError:
        try:
            dt = datetime.strptime(s, "%d%B%Y")
            return _to_sas_date(dt.date())
        except ValueError:
            return float("nan")


# ===================================================================
# TYPE CONVERSION
# ===================================================================

def sas_input(value: str, informat_name: str) -> Any:
    """SAS INPUT: convert string to value using an informat.

    Handles both custom informats (from registry) and built-in
    SAS numeric/date informats.
    """
    if _is_missing(value):
        return float("nan")

    s = str(value).strip()
    name_lower = informat_name.lower().rstrip(".")
    # Strip width specifier (e.g., 'mmddyy10' -> 'mmddyy')
    base_name = re.sub(r"\d+$", "", name_lower)
    base_name = re.sub(r"\.\d*$", "", base_name)

    # Check registry first
    ifmt = _registry.get_informat(name_lower)
    if ifmt is None:
        ifmt = _registry.get_informat(base_name)
    if ifmt is not None:
        return ifmt.convert(s)

    # Built-in date informats
    date_patterns = {
        "mmddyy": ["%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y"],
        "ddmmyy": ["%d/%m/%Y", "%d/%m/%y"],
        "yymmdd": ["%Y-%m-%d", "%y-%m-%d", "%Y/%m/%d"],
        "date": ["%d%b%Y", "%d%B%Y", "%d%b%y"],
        "anydtdte": ["%m/%d/%Y", "%d%b%Y", "%Y-%m-%d", "%m-%d-%Y"],
    }

    if base_name in date_patterns:
        for fmt in date_patterns[base_name]:
            try:
                dt = datetime.strptime(s, fmt)
                return _to_sas_date(dt.date())
            except ValueError:
                continue
        return float("nan")

    # Built-in numeric informats
    if base_name in ("best", "comma", "dollar", "percent", ""):
        cleaned = s.replace("$", "").replace(",", "").replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return float("nan")

    # Plain numeric
    try:
        return float(s)
    except ValueError:
        return float("nan")


def sas_put(value: Any, format_name: str) -> str:
    """SAS PUT: convert a value to a string using a format."""
    if _is_missing(value):
        return ""

    name_lower = format_name.lower().rstrip(".")
    base_name = re.sub(r"\d+(\.\d*)?$", "", name_lower)

    # Check registry first
    fmt = _registry.get_format(name_lower)
    if fmt is None:
        fmt = _registry.get_format(base_name)
    if fmt is not None:
        return fmt.format(value)

    # Built-in date formats
    if base_name in ("mmddyy",):
        d = _python_date(value)
        if d is not None:
            return d.strftime("%m/%d/%Y")
        return str(value)
    if base_name in ("date",):
        d = _python_date(value)
        if d is not None:
            return d.strftime("%d%b%Y").upper()
        return str(value)
    if base_name in ("mmddyy",):
        d = _python_date(value)
        if d is not None:
            return d.strftime("%m/%d/%y")

    # Built-in numeric formats
    if base_name in ("dollar",):
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)
    if base_name in ("comma",):
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            return str(value)
    if base_name in ("z",):
        m = re.search(r"(\d+)", format_name)
        width = int(m.group(1)) if m else 5
        try:
            return str(int(float(value))).zfill(width)
        except (TypeError, ValueError):
            return str(value)

    return str(value)


def sas_inputn(value: str, informat_name: str) -> float:
    """SAS INPUTN: dynamic informat lookup – same as sas_input for our purposes."""
    return sas_input(value, informat_name)


# ===================================================================
# RANDOM FUNCTIONS
# ===================================================================

_rng = np.random.RandomState()


def streaminit(seed: int) -> None:
    """SAS CALL STREAMINIT: seed the random number generator."""
    global _rng
    _rng = np.random.RandomState(seed)


def rand(distribution: str, *args: float) -> float:
    """SAS RAND: generate random number from a distribution."""
    dist = distribution.lower().strip().strip("'\"")
    if dist == "normal" or dist == "gaussian":
        mu = args[0] if len(args) > 0 else 0.0
        sigma = args[1] if len(args) > 1 else 1.0
        return float(_rng.normal(mu, sigma))
    elif dist == "uniform":
        low = args[0] if len(args) > 0 else 0.0
        high = args[1] if len(args) > 1 else 1.0
        return float(_rng.uniform(low, high))
    elif dist == "bernoulli":
        p = args[0] if len(args) > 0 else 0.5
        return float(_rng.binomial(1, p))
    elif dist == "exponential":
        scale = args[0] if len(args) > 0 else 1.0
        return float(_rng.exponential(scale))
    elif dist == "poisson":
        lam = args[0] if len(args) > 0 else 1.0
        return float(_rng.poisson(lam))
    else:
        return float(_rng.random())


def ranuni(seed: int) -> float:
    """SAS RANUNI: uniform random number in [0, 1).

    NOTE: SAS RANUNI uses a different internal RNG from RAND.
    We use a dedicated seed-based generator for reproducibility.
    """
    rng = np.random.RandomState(abs(seed) if seed != 0 else None)
    return float(rng.random())


def rannor(seed: int) -> float:
    """SAS RANNOR: normal(0,1) random number."""
    rng = np.random.RandomState(abs(seed) if seed != 0 else None)
    return float(rng.randn())


# ===================================================================
# REGEX (PRX) FUNCTIONS
# ===================================================================

_prx_cache: dict = {}


def prxparse(pattern: str) -> int:
    """SAS PRXPARSE: compile regex, return an integer handle."""
    pat = str(pattern).strip()
    # SAS patterns are like /pattern/modifiers
    m = re.match(r"^/(.+)/([imsx]*)$", pat)
    if m:
        raw_pat = m.group(1)
        flags_str = m.group(2)
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL
        if "x" in flags_str:
            flags |= re.VERBOSE
        compiled = re.compile(raw_pat, flags)
    else:
        compiled = re.compile(pat)

    handle = id(compiled) % (10**9)
    _prx_cache[handle] = compiled
    return handle


def prxmatch(pattern_or_handle: Any, source: str) -> int:
    """SAS PRXMATCH: return 1-based position of first regex match, 0 if none."""
    if _is_missing(source):
        return 0

    s = str(source)

    if isinstance(pattern_or_handle, int) and pattern_or_handle in _prx_cache:
        compiled = _prx_cache[pattern_or_handle]
    else:
        # Treat as inline pattern
        pat = str(pattern_or_handle).strip()
        m_pat = re.match(r"^/(.+)/([imsx]*)$", pat)
        if m_pat:
            raw_pat = m_pat.group(1)
            flags_str = m_pat.group(2)
            flags = 0
            if "i" in flags_str:
                flags |= re.IGNORECASE
            if "m" in flags_str:
                flags |= re.MULTILINE
            if "s" in flags_str:
                flags |= re.DOTALL
            if "x" in flags_str:
                flags |= re.VERBOSE
            compiled = re.compile(raw_pat, flags)
        else:
            compiled = re.compile(pat)

    match = compiled.search(s)
    if match:
        return match.start() + 1
    return 0
