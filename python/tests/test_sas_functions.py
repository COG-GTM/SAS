"""Unit tests for python.utils.sas_functions."""

from __future__ import annotations

import datetime
import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.utils.sas_functions import (
    # String functions
    compress,
    scan,
    substr,
    find,
    findw,
    tranwrd,
    translate,
    propcase,
    upcase,
    lowcase,
    catx,
    cats,
    cat,
    left,
    trimn,
    strip,
    compbl,
    lengthn,
    anydigit,
    anyalpha,
    notalpha,
    notdigit,
    notalnum,
    spedis,
    countw,
    count,
    reverse,
    verify,
    # Numeric functions
    sas_mean,
    sas_sum,
    sas_n,
    sas_nmiss,
    largest,
    smallest,
    sas_round,
    sas_int,
    sas_ceil,
    sas_floor,
    sas_abs,
    sas_sqrt,
    sas_log,
    sas_exp,
    sas_mod,
    sas_constant,
    lag,
    lag2,
    dif,
    call_sortn,
    missing,
    call_missing,
    # Random
    rand,
    ranuni,
    rannor,
    streaminit,
    # Date
    yrdif,
    intck,
    intnx,
    mdy,
    weekday,
    day,
    month,
    year,
    today,
    datepart,
    sas_date_literal,
    # Type conversion
    sas_input,
    sas_put,
    sas_inputn,
    # Regex
    prxparse,
    prxmatch,
)


# ===================================================================
# String functions – scalar and Series
# ===================================================================

class TestCompress:
    def test_default_removes_spaces(self):
        assert compress("A B C D") == "ABCD"

    def test_remove_specific_chars(self):
        assert compress("ABC123", "ABC") == "123"

    def test_keep_digits(self):
        assert compress("(800) 555-1234", "", "kd") == "8005551234"

    def test_keep_alpha(self):
        assert compress("abc 123 def", "", "ka") == "abcdef"

    def test_keep_whitespace(self):
        assert compress("abc 123 def", "", "ks") == "  "

    def test_series_input(self):
        s = pd.Series(["A B", "C D"])
        result = compress(s)
        assert list(result) == ["AB", "CD"]

    def test_modifier_d_removes_digits(self):
        assert compress("abc123", "", "d") == "abc"

    def test_modifier_a_removes_alpha(self):
        assert compress("abc123", "", "a") == "123"


class TestScan:
    def test_first_word(self):
        assert scan("Hello World Foo", 1) == "Hello"

    def test_second_word(self):
        assert scan("Hello World Foo", 2) == "World"

    def test_negative_index(self):
        assert scan("Hello World Foo", -1) == "Foo"

    def test_custom_delimiters(self):
        assert scan("a,b,c", 2, ",") == "b"

    def test_series(self):
        s = pd.Series(["Hello World", "Foo Bar"])
        result = scan(s, 1)
        assert list(result) == ["Hello", "Foo"]

    def test_out_of_range(self):
        assert scan("Hello", 5) == ""


class TestSubstr:
    def test_basic(self):
        assert substr("ABCDEF", 3, 2) == "CD"

    def test_no_length(self):
        assert substr("ABCDEF", 3) == "CDEF"

    def test_series(self):
        s = pd.Series(["ABCDEF", "GHIJKL"])
        result = substr(s, 1, 3)
        assert list(result) == ["ABC", "GHI"]


class TestFind:
    def test_found(self):
        assert find("Hello World", "World") == 7

    def test_not_found(self):
        assert find("Hello World", "xyz") == 0

    def test_case_insensitive(self):
        assert find("Hello World", "world", "i") == 7

    def test_series(self):
        s = pd.Series(["Hello World", "Foo Bar"])
        result = find(s, "World")
        assert list(result) == [7, 0]


class TestFindw:
    def test_found(self):
        assert findw("The quick brown fox", "quick") > 0

    def test_not_found(self):
        assert findw("The quick brown fox", "xyz") == 0

    def test_case_insensitive(self):
        assert findw("The Quick brown", "quick", modifier="i") > 0


class TestTranwrd:
    def test_replace(self):
        assert tranwrd("Hello World", "World", "Python") == "Hello Python"

    def test_series(self):
        s = pd.Series(["Hello World", "World Cup"])
        result = tranwrd(s, "World", "Earth")
        assert list(result) == ["Hello Earth", "Earth Cup"]


class TestTranslate:
    def test_basic(self):
        assert translate("12345", "ABCDE", "12345") == "ABCDE"


class TestPropcase:
    def test_basic(self):
        assert propcase("hello world") == "Hello World"

    def test_series(self):
        s = pd.Series(["hello world", "foo bar"])
        result = propcase(s)
        assert list(result) == ["Hello World", "Foo Bar"]


class TestUpcase:
    def test_basic(self):
        assert upcase("hello") == "HELLO"

    def test_series(self):
        s = pd.Series(["hello", "world"])
        result = upcase(s)
        assert list(result) == ["HELLO", "WORLD"]


class TestLowcase:
    def test_basic(self):
        assert lowcase("HELLO") == "hello"


class TestCatx:
    def test_basic(self):
        assert catx(", ", "A", "B", "C") == "A, B, C"

    def test_skip_missing(self):
        assert catx("-", "A", None, "B", float("nan"), "C") == "A-B-C"

    def test_strip_blanks(self):
        assert catx(",", " A ", " B ") == "A,B"


class TestCats:
    def test_basic(self):
        assert cats(" A ", " B ") == "AB"


class TestCat:
    def test_basic(self):
        assert cat("A", "B", "C") == "ABC"

    def test_with_missing(self):
        assert cat("A", None, "C") == "AC"


class TestLeft:
    def test_basic(self):
        assert left("  hello  ") == "hello  "


class TestTrimn:
    def test_basic(self):
        assert trimn("  hello  ") == "  hello"

    def test_blank(self):
        assert trimn("   ") == ""


class TestStrip:
    def test_basic(self):
        assert strip("  hello  ") == "hello"


class TestCompbl:
    def test_basic(self):
        assert compbl("Hello   World    Test") == "Hello World Test"


class TestLengthn:
    def test_basic(self):
        assert lengthn("Hello  ") == 5

    def test_blank(self):
        assert lengthn("   ") == 0

    def test_missing(self):
        assert lengthn(None) == 0


class TestAnydigit:
    def test_found(self):
        assert anydigit("abc123") == 4

    def test_not_found(self):
        assert anydigit("abcdef") == 0


class TestAnyalpha:
    def test_found(self):
        assert anyalpha("123abc") == 4

    def test_not_found(self):
        assert anyalpha("12345") == 0


class TestNotalpha:
    def test_found(self):
        assert notalpha("abc1def") == 4

    def test_all_alpha(self):
        assert notalpha("abcdef") == 0


class TestNotdigit:
    def test_found(self):
        assert notdigit("123a456") == 4

    def test_all_digits(self):
        assert notdigit("12345") == 0


class TestNotalnum:
    def test_found(self):
        assert notalnum("abc123!") == 7

    def test_all_alnum(self):
        assert notalnum("abc123") == 0


class TestSpedis:
    def test_identical(self):
        assert spedis("SMITH", "SMITH") == 0

    def test_replacement(self):
        # Single char replacement in non-first position
        result = spedis("SMITH", "SMYTH")
        assert result > 0

    def test_different_length(self):
        result = spedis("AB", "ABC")
        assert result > 0

    def test_first_char_replacement(self):
        # First char replacement costs more (50 vs 25)
        result1 = spedis("ABC", "XBC")
        result2 = spedis("ABC", "AXC")
        assert result1 > result2


class TestCountw:
    def test_basic(self):
        assert countw("Hello World Foo") == 3

    def test_custom_delimiters(self):
        assert countw("a,b,c", ",") == 3


class TestCount:
    def test_basic(self):
        assert count("banana", "an") == 2

    def test_series(self):
        s = pd.Series(["banana", "apple"])
        result = count(s, "a")
        assert list(result) == [3, 1]


class TestReverse:
    def test_basic(self):
        assert reverse("Hello") == "olleH"


class TestVerify:
    def test_all_in_set(self):
        assert verify("123", "0123456789") == 0

    def test_not_in_set(self):
        assert verify("123A", "0123456789") == 4


# ===================================================================
# Numeric functions
# ===================================================================

class TestSasMean:
    def test_basic(self):
        assert sas_mean(1, 2, 3) == 2.0

    def test_with_missing(self):
        assert sas_mean(1, float("nan"), 3) == 2.0

    def test_all_missing(self):
        assert math.isnan(sas_mean(float("nan"), float("nan")))


class TestSasSum:
    def test_basic(self):
        assert sas_sum(1, 2, 3) == 6.0

    def test_with_missing(self):
        assert sas_sum(1, float("nan"), 3) == 4.0

    def test_all_missing_returns_zero(self):
        assert sas_sum(float("nan"), float("nan")) == 0.0


class TestSasN:
    def test_basic(self):
        assert sas_n(1, 2, float("nan"), 4) == 3

    def test_all_missing(self):
        assert sas_n(float("nan")) == 0


class TestSasNmiss:
    def test_basic(self):
        assert sas_nmiss(1, float("nan"), 3, float("nan")) == 2


class TestLargest:
    def test_basic(self):
        assert largest(1, 3, 1, 4, 1, 5) == 5
        assert largest(2, 3, 1, 4, 1, 5) == 4

    def test_with_missing(self):
        assert largest(1, 3, float("nan"), 5) == 5

    def test_not_enough(self):
        assert math.isnan(largest(5, 1, 2))


class TestSmallest:
    def test_basic(self):
        assert smallest(1, 3, 1, 4, 1, 5) == 1
        assert smallest(2, 3, 1, 4, 1, 5) == 1

    def test_with_missing(self):
        assert smallest(1, float("nan"), 3, 5) == 3


class TestSasRound:
    def test_round_half_away_from_zero(self):
        assert sas_round(2.5, 1) == 3
        assert sas_round(3.5, 1) == 4

    def test_negative_half_away_from_zero(self):
        assert sas_round(-2.5, 1) == -3

    def test_round_to_fraction(self):
        result = sas_round(100.7 / 2.2, 0.1)
        assert abs(result - 45.8) < 0.01

    def test_missing(self):
        assert math.isnan(sas_round(float("nan")))


class TestSasInt:
    def test_positive(self):
        assert sas_int(3.7) == 3

    def test_negative(self):
        assert sas_int(-3.7) == -3


class TestSasCeil:
    def test_basic(self):
        assert sas_ceil(3.1) == 4
        assert sas_ceil(-3.1) == -3


class TestSasFloor:
    def test_basic(self):
        assert sas_floor(3.9) == 3
        assert sas_floor(-3.1) == -4


class TestSasAbs:
    def test_basic(self):
        assert sas_abs(-5) == 5
        assert sas_abs(5) == 5


class TestSasSqrt:
    def test_basic(self):
        assert sas_sqrt(16) == 4.0


class TestSasLog:
    def test_basic(self):
        assert abs(sas_log(math.e) - 1.0) < 1e-10


class TestSasExp:
    def test_basic(self):
        assert abs(sas_exp(1) - math.e) < 1e-10


class TestSasMod:
    def test_basic(self):
        assert sas_mod(10, 3) == 1


class TestSasConstant:
    def test_pi(self):
        assert sas_constant("pi") == math.pi

    def test_e(self):
        assert sas_constant("e") == math.e

    def test_exactint(self):
        assert sas_constant("exactint", 8) == 2**53


class TestLag:
    def test_basic(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = lag(s, 1)
        assert math.isnan(result.iloc[0])
        assert result.iloc[1] == 1
        assert result.iloc[4] == 4


class TestLag2:
    def test_basic(self):
        s = pd.Series([10, 20, 30, 40])
        result = lag2(s)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == 10


class TestDif:
    def test_basic(self):
        s = pd.Series([10, 20, 30, 40])
        result = dif(s)
        assert math.isnan(result.iloc[0])
        assert result.iloc[1] == 10
        assert result.iloc[2] == 10


class TestCallSortn:
    def test_basic(self):
        vals = [3, 1, float("nan"), 2]
        result = call_sortn(vals)
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3
        assert math.isnan(result[3])


class TestMissing:
    def test_nan(self):
        assert missing(float("nan")) is True

    def test_none(self):
        assert missing(None) is True

    def test_blank(self):
        assert missing("  ") is True

    def test_value(self):
        assert missing(5) is False


class TestCallMissing:
    def test_basic(self):
        result = call_missing(1, 2, 3)
        assert len(result) == 3
        assert all(math.isnan(v) for v in result)


# ===================================================================
# Random number functions
# ===================================================================

class TestRand:
    def test_uniform(self):
        streaminit(42)
        val = rand("uniform")
        assert 0 <= val < 1

    def test_normal(self):
        streaminit(42)
        val = rand("normal", 100, 10)
        assert isinstance(val, float)

    def test_bernoulli(self):
        val = rand("bernoulli", 0.5)
        assert val in (0.0, 1.0)

    def test_integer(self):
        val = rand("integer", 1, 10)
        assert 1 <= val <= 10


class TestRanuni:
    def test_basic(self):
        val = ranuni(12345)
        assert 0 <= val < 1


class TestRannor:
    def test_basic(self):
        val = rannor(12345)
        assert isinstance(val, float)


# ===================================================================
# Date functions
# ===================================================================

class TestYrdif:
    def test_one_year(self):
        result = yrdif(datetime.date(2000, 1, 1), datetime.date(2001, 1, 1))
        assert abs(result - 1.0) < 0.01

    def test_half_year(self):
        result = yrdif(datetime.date(2000, 1, 1), datetime.date(2000, 7, 1))
        assert 0.49 < result < 0.51


class TestIntck:
    def test_day(self):
        assert intck("day", datetime.date(2020, 1, 1), datetime.date(2020, 1, 31)) == 30

    def test_month(self):
        assert intck("month", datetime.date(2020, 1, 15), datetime.date(2020, 4, 15)) == 3

    def test_year(self):
        assert intck("year", datetime.date(2018, 6, 1), datetime.date(2020, 3, 1)) == 2

    def test_qtr(self):
        assert intck("qtr", datetime.date(2020, 1, 1), datetime.date(2020, 10, 1)) == 3

    def test_week(self):
        assert intck("week", datetime.date(2020, 1, 1), datetime.date(2020, 1, 15)) == 2


class TestIntnx:
    def test_month_beginning(self):
        result = intnx("month", datetime.date(2020, 1, 15), 2, "beginning")
        assert result == datetime.date(2020, 3, 1)

    def test_month_end(self):
        result = intnx("month", datetime.date(2020, 1, 15), 1, "end")
        assert result == datetime.date(2020, 2, 29)  # 2020 is leap year

    def test_month_sameday(self):
        result = intnx("month", datetime.date(2020, 1, 15), 1, "sameday")
        assert result == datetime.date(2020, 2, 15)

    def test_year_beginning(self):
        result = intnx("year", datetime.date(2020, 6, 15), 1, "beginning")
        assert result == datetime.date(2021, 1, 1)

    def test_day(self):
        result = intnx("day", datetime.date(2020, 1, 1), 10)
        assert result == datetime.date(2020, 1, 11)


class TestMdy:
    def test_basic(self):
        assert mdy(3, 15, 2020) == datetime.date(2020, 3, 15)


class TestWeekday:
    """SAS convention: 1=Sunday, 2=Monday, ..., 7=Saturday."""

    def test_sunday(self):
        # 2020-01-05 was a Sunday
        assert weekday(datetime.date(2020, 1, 5)) == 1

    def test_monday(self):
        # 2020-01-06 was a Monday
        assert weekday(datetime.date(2020, 1, 6)) == 2

    def test_saturday(self):
        # 2020-01-04 was a Saturday
        assert weekday(datetime.date(2020, 1, 4)) == 7

    def test_wednesday(self):
        # 2020-01-01 was a Wednesday
        assert weekday(datetime.date(2020, 1, 1)) == 4


class TestDayMonthYear:
    def test_day(self):
        assert day(datetime.date(2020, 3, 15)) == 15

    def test_month(self):
        assert month(datetime.date(2020, 3, 15)) == 3

    def test_year(self):
        assert year(datetime.date(2020, 3, 15)) == 2020


class TestToday:
    def test_returns_date(self):
        assert isinstance(today(), datetime.date)


class TestDatepart:
    def test_from_datetime(self):
        dt = datetime.datetime(2020, 3, 15, 10, 30, 0)
        assert datepart(dt) == datetime.date(2020, 3, 15)

    def test_from_timestamp(self):
        ts = pd.Timestamp("2020-03-15 10:30:00")
        assert datepart(ts) == datetime.date(2020, 3, 15)


class TestSasDateLiteral:
    def test_basic(self):
        assert sas_date_literal("'01Jan2017'd") == datetime.date(2017, 1, 1)

    def test_no_quotes(self):
        assert sas_date_literal("15Mar2020") == datetime.date(2020, 3, 15)


# ===================================================================
# Type conversion functions
# ===================================================================

class TestSasInput:
    def test_numeric(self):
        assert sas_input("42", "8.") == 42.0

    def test_dollar(self):
        assert sas_input("$1,234.56", "dollar9.") == 1234.56

    def test_comma(self):
        assert sas_input("1,234", "comma8.") == 1234.0

    def test_mmddyy(self):
        result = sas_input("10/21/2005", "mmddyy10.")
        assert result == datetime.date(2005, 10, 21)

    def test_date9(self):
        result = sas_input("01Jan2017", "date9.")
        assert result == datetime.date(2017, 1, 1)

    def test_missing(self):
        assert math.isnan(sas_input(None, "8."))

    def test_with_informat_object(self):
        from python.utils.sas_formats import default_registry
        fmt = default_registry.get("Convert")
        assert sas_input("A+", fmt) == 100


class TestSasPut:
    def test_date9(self):
        result = sas_put(datetime.date(2017, 1, 1), "date9.")
        assert result == "01JAN2017"

    def test_mmddyy10(self):
        result = sas_put(datetime.date(2005, 10, 21), "mmddyy10.")
        assert result == "10/21/2005"

    def test_dollar(self):
        result = sas_put(1234.56, "dollar10.2")
        assert result == "$1,234.56"

    def test_comma(self):
        result = sas_put(1234, "comma8.")
        assert result == "1,234"

    def test_missing(self):
        assert sas_put(None, "8.") == "."

    def test_weekdate(self):
        result = sas_put(datetime.date(2020, 1, 1), "weekdate.")
        assert "Wednesday" in result
        assert "January" in result


class TestSasInputn:
    def test_with_registry_format(self):
        result = sas_inputn("A", "Exp1944fmt8.")
        assert result == 220

    def test_with_standard_informat(self):
        result = sas_inputn("42", "8.")
        assert result == 42.0


# ===================================================================
# Regex functions
# ===================================================================

class TestPrxparse:
    def test_basic(self):
        pat = prxparse("/\\d+/")
        assert pat.search("abc123") is not None

    def test_no_delimiters(self):
        pat = prxparse("\\d+")
        assert pat.search("abc123") is not None

    def test_case_insensitive(self):
        pat = prxparse("/hello/i")
        assert pat.search("HELLO World") is not None


class TestPrxmatch:
    def test_found(self):
        assert prxmatch("/\\d+/", "abc123") == 4

    def test_not_found(self):
        assert prxmatch("/\\d+/", "abcdef") == 0

    def test_compiled(self):
        pat = prxparse("/world/i")
        assert prxmatch(pat, "Hello World") == 7

    def test_series(self):
        pat = prxparse("/\\d+/")
        s = pd.Series(["abc123", "no digits", "45xyz"])
        result = prxmatch(pat, s)
        assert list(result) == [4, 0, 1]
