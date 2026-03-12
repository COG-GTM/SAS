"""Targeted unit tests for known tricky SAS behaviors.

Tests cover: sas_round half-rounding, weekday Sunday=1,
spedis algorithm, compress modifiers.
"""

import math
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.sas_functions import (
    sas_round, weekday, spedis, compress,
    sas_int, sas_mean, sas_sum, sas_n, sas_nmiss,
    sas_date_literal, intck, mdy, day, month, year,
    find, scan, substr, catx, propcase, upcase, lowcase,
    lengthn, countw, reverse, verify,
    largest, smallest, missing, prxparse, prxmatch, sas_input, sas_put,
)
from utils.sas_formats import registry


# ===================================================================
# sas_round: round-half-away-from-zero
# ===================================================================

class TestSasRound:
    def test_half_rounds_up(self):
        """0.5 should round to 1, not 0 (Python default is banker's rounding)."""
        assert sas_round(0.5, 1) == 1.0

    def test_half_rounds_up_negative(self):
        """-0.5 should round to -1 (away from zero)."""
        assert sas_round(-0.5, 1) == -1.0

    def test_2_5_rounds_to_3(self):
        assert sas_round(2.5, 1) == 3.0

    def test_1_5_rounds_to_2(self):
        assert sas_round(1.5, 1) == 2.0

    def test_round_to_tenths(self):
        assert sas_round(2.25, 0.1) == 2.3

    def test_round_to_hundredths(self):
        assert sas_round(2.345, 0.01) == 2.35

    def test_nan_propagation(self):
        assert math.isnan(sas_round(float("nan"), 1))

    def test_round_zero(self):
        assert sas_round(0, 1) == 0.0

    def test_round_large_number(self):
        assert sas_round(1234.5, 1) == 1235.0

    def test_round_negative_half_away(self):
        assert sas_round(-1.5, 1) == -2.0


# ===================================================================
# weekday: Sunday = 1
# ===================================================================

class TestWeekday:
    def test_sunday_is_1(self):
        """SAS WEEKDAY returns 1 for Sunday."""
        # 2024-01-07 is a Sunday
        sas_date = (
            __import__("datetime").date(2024, 1, 7)
            - __import__("datetime").date(1960, 1, 1)
        ).days
        assert weekday(sas_date) == 1

    def test_monday_is_2(self):
        sas_date = (
            __import__("datetime").date(2024, 1, 8)
            - __import__("datetime").date(1960, 1, 1)
        ).days
        assert weekday(sas_date) == 2

    def test_saturday_is_7(self):
        sas_date = (
            __import__("datetime").date(2024, 1, 6)
            - __import__("datetime").date(1960, 1, 1)
        ).days
        assert weekday(sas_date) == 7

    def test_wednesday_is_4(self):
        sas_date = (
            __import__("datetime").date(2024, 1, 10)
            - __import__("datetime").date(1960, 1, 1)
        ).days
        assert weekday(sas_date) == 4

    def test_missing_returns_nan(self):
        assert math.isnan(weekday(float("nan")))


# ===================================================================
# spedis: generalized edit distance
# ===================================================================

class TestSpedis:
    def test_identical_strings(self):
        assert spedis("SMITH", "SMITH") == 0

    def test_case_insensitive(self):
        assert spedis("smith", "SMITH") == 0

    def test_single_replacement(self):
        result = spedis("SMYTH", "SMITH")
        assert result > 0
        assert result <= 100

    def test_first_char_change_penalized_more(self):
        """Changing the first character should cost more than middle."""
        first_change = spedis("XMITH", "SMITH")
        mid_change = spedis("SMXTH", "SMITH")
        assert first_change > mid_change

    def test_missing_returns_zero(self):
        assert spedis("", "SMITH") == 0
        assert spedis("SMITH", "") == 0

    def test_swap(self):
        result = spedis("SIMTH", "SMITH")
        assert result > 0


# ===================================================================
# compress: modifiers
# ===================================================================

class TestCompress:
    def test_default_removes_spaces(self):
        assert compress("A B C") == "ABC"

    def test_keep_digits(self):
        """'kd' modifier keeps only digits."""
        assert compress("abc123def456", "", "kd") == "123456"

    def test_remove_alpha(self):
        """'a' modifier removes alphabetic characters."""
        assert compress("abc123def456", "", "a") == "123456"

    def test_keep_alpha(self):
        """'ka' modifier keeps only alphabetic characters."""
        assert compress("abc123def456", "", "ka") == "abcdef"

    def test_remove_digits(self):
        assert compress("abc123", "", "d") == "abc"

    def test_remove_specific_chars(self):
        assert compress("hello world", "lo") == "he wrd"

    def test_remove_punctuation(self):
        assert compress("hello, world!", "", "p") == "hello world"

    def test_empty_string(self):
        assert compress("") == ""

    def test_missing_returns_empty(self):
        assert compress(None) == ""


# ===================================================================
# Numeric functions: NaN propagation and aggregation
# ===================================================================

class TestNumericFunctions:
    def test_mean_skips_nan(self):
        result = sas_mean(1, 2, float("nan"), 4)
        assert math.isclose(result, 7 / 3)

    def test_mean_all_nan(self):
        assert math.isnan(sas_mean(float("nan"), float("nan")))

    def test_sum_skips_nan(self):
        assert sas_sum(1, 2, float("nan"), 4) == 7.0

    def test_sum_all_nan_returns_zero(self):
        assert sas_sum(float("nan"), float("nan")) == 0.0

    def test_n_counts_non_missing(self):
        assert sas_n(1, 2, float("nan"), 4) == 3

    def test_nmiss_counts_missing(self):
        assert sas_nmiss(1, 2, float("nan"), 4) == 1

    def test_largest(self):
        assert largest(1, 3, 1, 4, 1, 5) == 5
        assert largest(2, 3, 1, 4, 1, 5) == 4

    def test_smallest(self):
        assert smallest(1, 3, 1, 4, 1, 5) == 1
        assert smallest(2, 3, 1, 4, 1, 5) == 1

    def test_int_truncates_toward_zero(self):
        assert sas_int(3.7) == 3.0
        assert sas_int(-3.7) == -3.0

    def test_missing_function(self):
        assert missing(float("nan")) == 1
        assert missing(None) == 1
        assert missing("") == 1
        assert missing(0) == 0
        assert missing("abc") == 0


# ===================================================================
# Date functions
# ===================================================================

class TestDateFunctions:
    def test_sas_date_literal(self):
        result = sas_date_literal("01jan1960")
        assert result == 0

    def test_mdy(self):
        result = mdy(1, 1, 1960)
        assert result == 0

    def test_day_month_year(self):
        sas_date = 0  # 01Jan1960
        assert day(sas_date) == 1
        assert month(sas_date) == 1
        assert year(sas_date) == 1960

    def test_intck_months(self):
        jan = sas_date_literal("01jan2000")
        mar = sas_date_literal("01mar2000")
        assert intck("month", jan, mar) == 2

    def test_intck_years(self):
        y2000 = sas_date_literal("01jan2000")
        y2003 = sas_date_literal("01jan2003")
        assert intck("year", y2000, y2003) == 3


# ===================================================================
# String functions
# ===================================================================

class TestStringFunctions:
    def test_find(self):
        assert find("Hello World", "World") == 7
        assert find("Hello World", "world", 1, "i") == 7
        assert find("Hello World", "xyz") == 0

    def test_scan(self):
        assert scan("one two three", 2) == "two"
        assert scan("one two three", -1) == "three"

    def test_substr(self):
        assert substr("Hello", 2, 3) == "ell"
        assert substr("Hello", 1) == "Hello"

    def test_catx(self):
        assert catx("-", "A", "B", "C") == "A-B-C"
        assert catx(",", "A", "", "C") == "A,C"

    def test_propcase(self):
        assert propcase("hello world") == "Hello World"
        assert propcase("HELLO") == "Hello"

    def test_upcase_lowcase(self):
        assert upcase("hello") == "HELLO"
        assert lowcase("HELLO") == "hello"

    def test_lengthn(self):
        assert lengthn("hello   ") == 5
        assert lengthn("") == 0

    def test_countw(self):
        assert countw("one two three") == 3
        assert countw("a,b,c", ",") == 3

    def test_reverse(self):
        assert reverse("hello") == "olleh"

    def test_verify(self):
        assert verify("ABCDE", "ABCD") == 5  # 'E' not in target
        assert verify("ABCD", "ABCD") == 0


# ===================================================================
# Format & Informat
# ===================================================================

class TestFormats:
    def test_gender_format(self):
        fmt = registry.get_format("$gender")
        assert fmt is not None
        assert fmt.format("M") == "Male"
        assert fmt.format("F") == "Female"
        assert fmt.format("X") == "Miscoded"

    def test_age_range_format(self):
        fmt = registry.get_format("age")
        assert fmt is not None
        assert fmt.format(25) == "Less than 30"
        assert fmt.format(35) == "30 to 50"
        assert fmt.format(55) == "51+"

    def test_likert_format(self):
        fmt = registry.get_format("$likert")
        assert fmt is not None
        assert fmt.format("1") == "Strongly disagree"
        assert fmt.format("5") == "Strongly agree"

    def test_convert_informat(self):
        ifmt = registry.get_informat("convert")
        assert ifmt is not None
        assert ifmt.convert("A+") == 100
        assert ifmt.convert("F") == 65

    def test_readtemp_informat_with_upcase(self):
        ifmt = registry.get_informat("readtemp")
        assert ifmt is not None
        assert ifmt.convert("N") == 98.6
        assert ifmt.convert("n") == 98.6  # upcase option
        assert ifmt.convert("100") == 100.0  # range match, _same_

    def test_sas_input_mmddyy(self):
        result = sas_input("10/21/2005", "mmddyy10.")
        assert isinstance(result, (int, float))
        assert not math.isnan(result)

    def test_sas_put_gender(self):
        result = sas_put("M", "$gender.")
        assert result == "Male"


# ===================================================================
# Regex (PRX) functions
# ===================================================================

class TestRegex:
    def test_prxparse_and_match(self):
        handle = prxparse("/\\d{3}-\\d{4}/")
        assert prxmatch(handle, "Call 555-1234 now") > 0

    def test_prxmatch_no_match(self):
        handle = prxparse("/xyz/")
        assert prxmatch(handle, "abc") == 0

    def test_prxmatch_case_insensitive(self):
        handle = prxparse("/hello/i")
        assert prxmatch(handle, "HELLO WORLD") > 0
