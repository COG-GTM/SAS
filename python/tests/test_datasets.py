"""Unit tests for create_datasets and chapter modules."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pandas.testing as tm
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from create_datasets import load_all_datasets  # noqa: E402
from utils.formats import (  # noqa: E402
    GENDER_FMT, LIKERT_FMT, age_group_fmt, chol_group_fmt, apply_format,
)


@pytest.fixture(scope="module")
def datasets() -> dict[str, pd.DataFrame]:
    return load_all_datasets()


class TestDatasets:
    def test_all_datasets_loaded(self, datasets: dict[str, pd.DataFrame]) -> None:
        assert len(datasets) >= 30

    def test_sales_columns(self, datasets: dict[str, pd.DataFrame]) -> None:
        sales = datasets["sales"]
        assert "EmpID" in sales.columns
        assert "TotalSales" in sales.columns
        assert len(sales) == 15

    def test_sales_total_sales_computed(self, datasets: dict[str, pd.DataFrame]) -> None:
        sales = datasets["sales"]
        expected = sales["Quantity"] * sales["UnitCost"]
        tm.assert_series_equal(sales["TotalSales"], expected, check_names=False)

    def test_blood_columns(self, datasets: dict[str, pd.DataFrame]) -> None:
        blood = datasets["blood"]
        for col in ["Subject", "Gender", "BloodType", "WBC", "RBC", "Chol"]:
            assert col in blood.columns

    def test_survey_ids_zero_padded(self, datasets: dict[str, pd.DataFrame]) -> None:
        survey = datasets["survey"]
        assert all(len(sid) == 3 for sid in survey["ID"])

    def test_clinic_sorted(self, datasets: dict[str, pd.DataFrame]) -> None:
        clinic = datasets["clinic"]
        ids = clinic["ID"].tolist()
        assert ids == sorted(ids)

    def test_medical_dates_parsed(self, datasets: dict[str, pd.DataFrame]) -> None:
        medical = datasets["medical"]
        assert pd.api.types.is_datetime64_any_dtype(medical["VisitDate"])

    def test_bicycles_total_sales(self, datasets: dict[str, pd.DataFrame]) -> None:
        bicycles = datasets["bicycles"]
        expected = (bicycles["Units"] * bicycles["UnitCost"]) / 1000
        tm.assert_series_equal(bicycles["TotalSales"], expected, check_names=False)

    def test_oneper_manyper_consistency(self, datasets: dict[str, pd.DataFrame]) -> None:
        oneper = datasets["oneper"]
        manyper = datasets["manyper"]
        assert set(manyper["Subj"]).issubset(set(oneper["Subj"]))

    def test_health_shape(self, datasets: dict[str, pd.DataFrame]) -> None:
        health = datasets["health"]
        assert health.shape == (4, 3)

    def test_demographic_dates(self, datasets: dict[str, pd.DataFrame]) -> None:
        demo = datasets["demographic"]
        assert pd.api.types.is_datetime64_any_dtype(demo["DOB"])

    def test_stocks_dates(self, datasets: dict[str, pd.DataFrame]) -> None:
        stocks = datasets["stocks"]
        assert pd.api.types.is_datetime64_any_dtype(stocks["Date"])


class TestFormats:
    def test_gender_fmt(self) -> None:
        assert GENDER_FMT["M"] == "Male"
        assert GENDER_FMT["F"] == "Female"

    def test_likert_fmt(self) -> None:
        assert LIKERT_FMT["1"] == "Strongly disagree"
        assert LIKERT_FMT["5"] == "Strongly agree"

    def test_age_group_fmt(self) -> None:
        assert age_group_fmt(25) == "Less than 30"
        assert age_group_fmt(40) == "30 to 50"
        assert age_group_fmt(55) == "51+"
        assert age_group_fmt(None) == ""

    def test_chol_group_fmt(self) -> None:
        assert chol_group_fmt(150) == "Low"
        assert chol_group_fmt(250) == "High"
        assert chol_group_fmt(None) == ""

    def test_apply_format_found(self) -> None:
        assert apply_format("M", GENDER_FMT) == "Male"

    def test_apply_format_not_found(self) -> None:
        assert apply_format("X", GENDER_FMT) == "X"


class TestChapterImports:
    """Verify every chapter module can be imported without error."""

    @pytest.mark.parametrize("module_name", [
        "chapters.ch01_introduction",
        "chapters.ch02_reading_data",
        "chapters.ch03_reading_raw_data",
        "chapters.ch04_creating_datasets",
        "chapters.ch05_formats_labels",
        "chapters.ch06_reading_writing_excel",
        "chapters.ch07_conditional_logic",
        "chapters.ch08_do_loops",
        "chapters.ch09_dates",
        "chapters.ch10_combining_datasets",
        "chapters.ch11_numeric_functions",
        "chapters.ch12_character_functions",
        "chapters.ch13_arrays",
        "chapters.ch14_proc_print",
        "chapters.ch15_proc_report",
        "chapters.ch16_proc_means",
        "chapters.ch17_proc_freq",
        "chapters.ch18_proc_tabulate",
        "chapters.ch19_ods",
        "chapters.ch20_sgplot",
        "chapters.ch21_advanced_input",
        "chapters.ch22_advanced_formats",
        "chapters.ch23_restructuring",
        "chapters.ch24_multiple_obs",
        "chapters.ch25_macros",
        "chapters.ch26_proc_sql",
        "chapters.ch27_regex",
    ])
    def test_import(self, module_name: str) -> None:
        __import__(module_name)
