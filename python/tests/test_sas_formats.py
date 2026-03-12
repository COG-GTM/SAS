"""Unit tests for python.utils.sas_formats."""

from __future__ import annotations

import datetime
import math
import sys
import os

import numpy as np
import pandas as pd
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.utils.sas_formats import (
    SASFormat,
    SASInformat,
    FormatRegistry,
    create_format_from_dataframe,
    create_exposure_formats,
    default_registry,
)


# ---------------------------------------------------------------------------
# Exact match formatting
# ---------------------------------------------------------------------------

class TestExactMatchFormatting:
    """Tests for exact-match SAS formats ($gender, $likert, $dx)."""

    def test_gender_male(self):
        fmt = default_registry.get("$gender")
        assert fmt.format("M") == "Male"

    def test_gender_female(self):
        fmt = default_registry.get("$gender")
        assert fmt.format("F") == "Female"

    def test_likert_all_values(self):
        fmt = default_registry.get("$likert")
        expected = {
            "1": "Strongly disagree",
            "2": "Disagree",
            "3": "No opinion",
            "4": "Agree",
            "5": "Strongly agree",
        }
        for k, v in expected.items():
            assert fmt.format(k) == v

    def test_dx_all_values(self):
        fmt = default_registry.get("$dx")
        assert fmt.format("1") == "Routine Visit"
        assert fmt.format("2") == "Cold"
        assert fmt.format("3") == "Heart Problems"
        assert fmt.format("4") == "GI Problems"
        assert fmt.format("5") == "Psychiatric"
        assert fmt.format("6") == "Injury"
        assert fmt.format("7") == "Infection"

    def test_colors_exact_int(self):
        fmt = default_registry.get("Colors")
        assert fmt.format(1) == "Yellow"
        assert fmt.format(2) == "Blue"
        assert fmt.format(3) == "Red"
        assert fmt.format(4) == "Green"

    def test_groupfmt(self):
        fmt = default_registry.get("groupfmt")
        assert fmt.format(0) == "A"
        assert fmt.format(1) == "B"
        assert fmt.format(2) == "C"

    def test_name_lookup(self):
        fmt = default_registry.get("NameLookup")
        assert fmt.format(122) == "Salt"
        assert fmt.format(188) == "Sugar"
        assert fmt.format(101) == "Cereal"
        assert fmt.format(755) == "Eggs"
        assert fmt.format(999) == ""  # other


# ---------------------------------------------------------------------------
# Range formatting
# ---------------------------------------------------------------------------

class TestRangeFormatting:
    """Tests for range-based SAS formats (age, Agefmt, Chol_Group, AgeGroup)."""

    def test_age_ranges(self):
        fmt = default_registry.get("age")
        assert fmt.format(20) == "Less than 30"
        assert fmt.format(29) == "Less than 30"
        assert fmt.format(30) == "30 to 50"
        assert fmt.format(40) == "30 to 50"
        assert fmt.format(50) == "30 to 50"
        assert fmt.format(51) == "51+"
        assert fmt.format(80) == "51+"

    def test_agefmt_exclusive_upper(self):
        fmt = default_registry.get("Agefmt")
        assert fmt.format(10) == "Group One"
        assert fmt.format(19) == "Group One"
        assert fmt.format(20) == "Group Two"  # inclusive lower
        assert fmt.format(39) == "Group Two"
        assert fmt.format(40) == "Group Three"  # inclusive lower
        assert fmt.format(100) == "Group Three"

    def test_chol_group(self):
        fmt = default_registry.get("Chol_Group")
        assert fmt.format(150) == "Low"
        assert fmt.format(199) == "Low"
        assert fmt.format(200) == "High"  # inclusive lower
        assert fmt.format(250) == "High"

    def test_age_group(self):
        fmt = default_registry.get("AgeGroup")
        assert fmt.format(25) == "Less than 30"
        assert fmt.format(30) == "30 to 59"
        assert fmt.format(59) == "30 to 59"
        assert fmt.format(60) == "60 and higher"
        assert fmt.format(90) == "60 and higher"

    def test_two_ranges(self):
        fmt = default_registry.get("two")
        assert fmt.format(2) == "Group 1"
        assert fmt.format(3) == "Group 1"
        assert fmt.format(4) == "Group 2"
        assert fmt.format(5) == "Group 2"
        assert fmt.format(6) == "Other values"


# ---------------------------------------------------------------------------
# Missing value handling
# ---------------------------------------------------------------------------

class TestMissingValues:
    """Tests for missing-value handling in formats."""

    def test_two_missing(self):
        fmt = default_registry.get("two")
        assert fmt.format(float("nan")) == "Missing"

    def test_colors_missing(self):
        fmt = default_registry.get("Colors")
        assert fmt.format(float("nan")) == "Missing"

    def test_gender_missing_blank(self):
        fmt = default_registry.get("$gender")
        assert fmt.format(" ") == "Not entered"
        assert fmt.format("") == "Not entered"

    def test_size_missing(self):
        fmt = default_registry.get("$size")
        assert fmt.format(" ") == "Missing"

    def test_yesno_missing(self):
        fmt = default_registry.get("$yesno")
        assert fmt.format(" ") == "Not Given"


# ---------------------------------------------------------------------------
# Other / fallback handling
# ---------------------------------------------------------------------------

class TestOtherFallback:
    """Tests for 'other' fallback in formats."""

    def test_gender_other(self):
        fmt = default_registry.get("$gender")
        assert fmt.format("X") == "Miscoded"
        assert fmt.format("Z") == "Miscoded"

    def test_two_other(self):
        fmt = default_registry.get("two")
        assert fmt.format(6) == "Other values"
        assert fmt.format(100) == "Other values"


# ---------------------------------------------------------------------------
# Multi-value keys
# ---------------------------------------------------------------------------

class TestMultiValueKeys:
    """Tests for formats with multiple keys mapping to same label ($yesno)."""

    def test_yesno_yes(self):
        fmt = default_registry.get("$yesno")
        assert fmt.format("Y") == "Yes"
        assert fmt.format("1") == "Yes"

    def test_yesno_no(self):
        fmt = default_registry.get("$yesno")
        assert fmt.format("N") == "No"
        assert fmt.format("0") == "No"

    def test_three_disagreement(self):
        fmt = default_registry.get("$Three")
        assert fmt.format("1") == "Disagreement"
        assert fmt.format("2") == "Disagreement"

    def test_three_agreement(self):
        fmt = default_registry.get("$Three")
        assert fmt.format("4") == "Agreement"
        assert fmt.format("5") == "Agreement"

    def test_agree_disagree(self):
        fmt = default_registry.get("$Agree_Disagree")
        assert fmt.format("1") == "Generally disagree"
        assert fmt.format("2") == "Generally disagree"
        assert fmt.format("3") == "No opinion"
        assert fmt.format("4") == "Generally agree"
        assert fmt.format("5") == "Generally agree"


# ---------------------------------------------------------------------------
# Multilabel format
# ---------------------------------------------------------------------------

class TestMultilabelFormat:
    """Tests for AgeGroup_multilabel."""

    def test_age_10(self):
        fmt = default_registry.get("AgeGroup_multilabel")
        result = fmt.format(10)
        assert "0 to <20" in result
        assert "Less than 50" in result

    def test_age_25(self):
        fmt = default_registry.get("AgeGroup_multilabel")
        result = fmt.format(25)
        assert "20 to <40" in result
        assert "Less than 50" in result

    def test_age_55(self):
        fmt = default_registry.get("AgeGroup_multilabel")
        result = fmt.format(55)
        assert "40 to <60" in result
        assert "> or = to 50" in result
        assert "Less than 50" not in result

    def test_age_70(self):
        fmt = default_registry.get("AgeGroup_multilabel")
        result = fmt.format(70)
        assert "60 to <80" in result
        assert "> or = to 50" in result

    def test_age_85(self):
        fmt = default_registry.get("AgeGroup_multilabel")
        result = fmt.format(85)
        assert "80 +" in result
        assert "> or = to 50" in result


# ---------------------------------------------------------------------------
# Informat conversion
# ---------------------------------------------------------------------------

class TestInformatConversion:
    """Tests for SASInformat (Convert, ReadTemp, ReadGrade, PriceLookup)."""

    def test_convert_grades(self):
        fmt = default_registry.get("Convert")
        assert fmt.convert("A+") == 100
        assert fmt.convert("A") == 96
        assert fmt.convert("A-") == 92
        assert fmt.convert("B+") == 88
        assert fmt.convert("B") == 84
        assert fmt.convert("B-") == 80
        assert fmt.convert("C+") == 76
        assert fmt.convert("C") == 72
        assert fmt.convert("F") == 65

    def test_readtemp_same_range(self):
        fmt = default_registry.get("ReadTemp")
        assert fmt.convert("101") == 101.0
        assert fmt.convert("97.3") == 97.3
        assert fmt.convert("104.5") == 104.5

    def test_readtemp_n_value(self):
        fmt = default_registry.get("ReadTemp")
        assert fmt.convert("N") == 98.6
        assert fmt.convert("n") == 98.6  # upcase

    def test_readtemp_other(self):
        fmt = default_registry.get("ReadTemp")
        result = fmt.convert("67")
        assert math.isnan(result)

    def test_readgrade_letters(self):
        fmt = default_registry.get("ReadGrade")
        assert fmt.convert("A") == 95
        assert fmt.convert("B") == 85
        assert fmt.convert("a") == 95  # upcase
        assert fmt.convert("f") == 65

    def test_readgrade_same_passthrough(self):
        """other = _same_ means pass-through numeric value."""
        fmt = default_registry.get("ReadGrade")
        assert fmt.convert("97") == 97.0
        assert fmt.convert("72") == 72.0

    def test_pricelookup(self):
        fmt = default_registry.get("PriceLookup")
        assert fmt.convert("Salt") == 3.76
        assert fmt.convert("Sugar") == 4.99
        assert fmt.convert("Cereal") == 5.97
        assert fmt.convert("Eggs") == 2.65
        assert math.isnan(fmt.convert("Unknown"))

    def test_yearexp(self):
        fmt = default_registry.get("YearExp")
        assert fmt.convert(1946) == 250
        assert fmt.convert(1949) == 200
        assert fmt.convert(1952) == 100

    def test_convert_series(self):
        fmt = default_registry.get("Convert")
        s = pd.Series(["A+", "B", "F"])
        result = fmt.convert_series(s)
        assert list(result) == [100, 84, 65]


# ---------------------------------------------------------------------------
# _same_ pass-through
# ---------------------------------------------------------------------------

class TestSamePassThrough:
    """Tests for _same_ pass-through behaviour."""

    def test_readtemp_same(self):
        fmt = default_registry.get("ReadTemp")
        assert fmt.convert("100") == 100.0
        assert fmt.convert("98.6") == 98.6

    def test_readgrade_same(self):
        fmt = default_registry.get("ReadGrade")
        assert fmt.convert("99") == 99.0


# ---------------------------------------------------------------------------
# Data-driven format creation
# ---------------------------------------------------------------------------

class TestDataDrivenFormats:
    """Tests for create_format_from_dataframe and exposure formats."""

    def test_create_from_dataframe(self):
        df = pd.DataFrame({
            "ICD10": ["020", "022", "390"],
            "Description": ["Plague", "Anthrax", "Rheumatic fever"],
        })
        fmt = create_format_from_dataframe(
            df, "$ICDFMT", "ICD10", "Description", other_label="Not Found"
        )
        assert fmt.format("020") == "Plague"
        assert fmt.format("022") == "Anthrax"
        assert fmt.format("999") == "Not Found"

    def test_exposure_formats_registered(self):
        for year in range(1944, 1950):
            name = f"Exp{year}fmt"
            fmt = default_registry.get(name)
            assert fmt is not None, f"{name} not found in registry"

    def test_exp1944fmt_values(self):
        fmt = default_registry.get("Exp1944fmt")
        assert fmt.convert("A") == 220
        assert fmt.convert("B") == 180
        assert fmt.convert("C") == 210
        assert fmt.convert("D") == 110
        assert fmt.convert("E") == 90

    def test_exp1949fmt_values(self):
        fmt = default_registry.get("Exp1949fmt")
        assert fmt.convert("A") == 45
        assert fmt.convert("B") == 22
        assert fmt.convert("E") == 8


# ---------------------------------------------------------------------------
# Picture format
# ---------------------------------------------------------------------------

class TestPictureFormat:
    """Tests for the Pctfmt picture format."""

    def test_pctfmt(self):
        fmt = default_registry.get("Pctfmt")
        assert fmt.format(45.6) == "45.6%"
        assert fmt.format(100.0) == "100.0%"
        assert fmt.format(0.0) == "0.0%"


# ---------------------------------------------------------------------------
# Format Series
# ---------------------------------------------------------------------------

class TestFormatSeries:
    """Test applying formats to pandas Series."""

    def test_gender_series(self):
        fmt = default_registry.get("$gender")
        s = pd.Series(["M", "F", "X", " "])
        result = fmt.format_series(s)
        assert list(result) == ["Male", "Female", "Miscoded", "Not entered"]

    def test_age_series(self):
        fmt = default_registry.get("age")
        s = pd.Series([20, 30, 55])
        result = fmt.format_series(s)
        assert list(result) == ["Less than 30", "30 to 50", "51+"]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestFormatRegistry:
    """Tests for FormatRegistry singleton."""

    def test_singleton(self):
        r1 = FormatRegistry()
        r2 = FormatRegistry()
        assert r1 is r2

    def test_get_nonexistent(self):
        reg = FormatRegistry()
        assert reg.get("nonexistent_format_xyz") is None

    def test_apply(self):
        s = pd.Series(["M", "F"])
        result = default_registry.apply(s, "$gender")
        assert list(result) == ["Male", "Female"]

    def test_apply_missing_format_raises(self):
        with pytest.raises(KeyError):
            default_registry.apply(pd.Series([1]), "nonexistent_xyz")


# ---------------------------------------------------------------------------
# Registration (date-based format)
# ---------------------------------------------------------------------------

class TestRegistrationFormat:
    """Tests for the Registration date-based format."""

    def test_not_open(self):
        fmt = default_registry.get("Registration")
        d = datetime.date(2017, 11, 13)
        assert fmt.format(d) == "Not Open"

    def test_formatted_date(self):
        fmt = default_registry.get("Registration")
        d = datetime.date(2018, 10, 21)
        assert fmt.format(d) == "10/21/2018"

    def test_too_late(self):
        fmt = default_registry.get("Registration")
        d = datetime.date(2019, 2, 12)
        assert fmt.format(d) == "Too Late"


# ---------------------------------------------------------------------------
# Exp nested informat
# ---------------------------------------------------------------------------

class TestExpNestedInformat:
    """Tests for the Exp nested informat (delegates to YearExp)."""

    def test_low_range_passthrough(self):
        fmt = default_registry.get("Exp")
        result = fmt.convert(1940)
        assert result == 1940.0

    def test_mid_range_yearexp(self):
        fmt = default_registry.get("Exp")
        assert fmt.convert(1946) == 250
        assert fmt.convert(1949) == 200

    def test_high_range_passthrough(self):
        fmt = default_registry.get("Exp")
        result = fmt.convert(1960)
        assert result == 1960.0
