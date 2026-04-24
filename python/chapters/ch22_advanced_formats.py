"""
Chapter 22 — Using Advanced PROC FORMAT Features
=================================================
INVALUE (input formats), nested formats, PICTURE, CNTLIN/CNTLOUT,
multilabel formats — Python equivalents using dicts and functions.

SAS Programs: 22-1 through 22-24
"""
from __future__ import annotations


import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset
from utils.formats import (
    GRADE_CONVERT, ICD_FMT, NAME_LOOKUP, PRICE_LOOKUP,
    age_group_20,
)


# 22-1: Format to recode a variable
def example_22_1(survey: pd.DataFrame) -> pd.DataFrame:
    """Use age_group_20 format in PROC FREQ."""
    df = survey.copy()
    df["AgeGroup"] = df["Age"].apply(age_group_20)
    counts = df["AgeGroup"].value_counts().sort_index()
    return counts.to_frame("Frequency")


# 22-2: Format to create a character variable
def example_22_2(survey: pd.DataFrame) -> pd.DataFrame:
    """PUT(Age, Agefmt.) — create AgeGroup character variable."""
    df = survey.copy()
    df["AgeGroup"] = df["Age"].apply(age_group_20)
    return df[["ID", "Age", "AgeGroup"]]


# 22-3: INVALUE format — convert characters to numbers
def example_22_3() -> pd.DataFrame:
    """INVALUE Convert (SAS: 'A+' = 100, 'A' = 96, ...)."""
    text = """\
001A-
002B+
003F
004C+
005A"""
    rows = []
    for line in text.strip().splitlines():
        sid = line[:3]
        grade_str = line[3:]
        rows.append({"ID": sid, "Grade": GRADE_CONVERT.get(grade_str, np.nan)})
    return pd.DataFrame(rows)


# 22-4: INVALUE with UPCASE and OTHER
def example_22_4() -> pd.DataFrame:
    """Case-insensitive INVALUE with other → missing."""
    text = """\
001A-
002b+
003F
004c+
005 A
006X"""
    convert_upper = {k.upper(): v for k, v in GRADE_CONVERT.items()}
    rows = []
    for line in text.strip().splitlines():
        sid = line[:3]
        grade_str = line[3:].strip().upper()
        rows.append({"ID": sid, "Grade": convert_upper.get(grade_str, np.nan)})
    return pd.DataFrame(rows)


# 22-5: Normal body temperature substitution
def example_22_5() -> pd.DataFrame:
    """Replace 'N' with 98.6 for body temperature."""
    values = ["101", "N", "97.3", "n", "N", "104.5"]
    temps = []
    for v in values:
        if v.upper() == "N":
            temps.append(98.6)
        else:
            temps.append(float(v))
    return pd.DataFrame({"Temp": temps})


# 22-8: Lookup table using PUT + INPUT pattern
def example_22_8() -> pd.DataFrame:
    """Two-step lookup: ItemNumber → Name → Price (SAS PUT + INPUT)."""
    items = [101, 755, 122, 188, 999, 755]
    rows = []
    for item in items:
        name = NAME_LOOKUP.get(item, "")
        price = PRICE_LOOKUP.get(name, np.nan) if name else np.nan
        rows.append({"ItemNumber": item, "Name": name, "Price": price})
    return pd.DataFrame(rows)


# 22-9 / 22-10 / 22-11: CNTLIN — build a format from a dataset
def example_22_11() -> pd.DataFrame:
    """Apply ICD format from a control dataset (SAS CNTLIN)."""
    diseases = pd.DataFrame({"ICD10": ["020", "410", "500", "493"]})
    diseases["Description"] = diseases["ICD10"].map(ICD_FMT).fillna("Not Found")
    return diseases


# 22-14: Nested format (SAS format Registration)
def example_22_14() -> pd.DataFrame:
    """Date-based registration format (SAS nested picture format)."""
    data = [
        ("Smith", "10/21/2018"),
        ("Jones", "11/13/2017"),
        ("Harris", "01/03/2018"),
        ("Arnold", "02/12/2019"),
    ]
    df = pd.DataFrame(data, columns=["Name", "Date"])
    df["Date"] = pd.to_datetime(df["Date"])
    open_start = pd.Timestamp("2018-01-01")
    open_end = pd.Timestamp("2018-12-31")

    def registration_fmt(d: pd.Timestamp) -> str:
        if d < open_start:
            return "Not Open"
        if d <= open_end:
            return d.strftime("%m/%d/%Y")
        return "Too Late"

    df["Registration"] = df["Date"].apply(registration_fmt)
    return df


# 22-17: Multilabel format (SAS multilabel option)
def example_22_17(survey: pd.DataFrame) -> pd.DataFrame:
    """Multilabel age groups (overlapping bins, SAS MLF)."""
    df = survey.copy()
    bins_primary = [(0, 20, "0 to <20"), (20, 40, "20 to <40"),
                    (40, 60, "40 to <60"), (60, 80, "60 to <80")]
    bins_secondary = [(0, 50, "Less than 50"), (50, 200, ">= 50")]

    rows = []
    for _, r in df.iterrows():
        age = r["Age"]
        for lo, hi, lbl in bins_primary + bins_secondary:
            if lo <= age < hi:
                rows.append({"AgeGroup": lbl, "Salary": r["Salary"]})
    result = pd.DataFrame(rows)
    return (
        result.groupby("AgeGroup")["Salary"]
        .agg(["count", "mean"])
        .round(0)
        .reset_index()
        .rename(columns={"count": "N", "mean": "Mean Salary"})
    )


# 22-22: Build exposure formats from data (SAS CNTLIN with dynamic format names)
def example_22_22() -> pd.DataFrame:
    """Build year-specific exposure lookup from inline data."""
    levels_data = [
        [220, 180, 210, 110, 90],
        [202, 170, 208, 100, 85],
        [150, 110, 150, 60, 50],
        [105, 56, 88, 40, 30],
        [60, 30, 40, 20, 10],
        [45, 22, 22, 10, 8],
    ]
    job_codes = ["A", "B", "C", "D", "E"]
    exposure_lookup: dict[tuple[int, str], int] = {}
    for yr_idx, year in enumerate(range(1944, 1950)):
        for jc_idx, jc in enumerate(job_codes):
            exposure_lookup[(year, jc)] = levels_data[yr_idx][jc_idx]

    workers = pd.DataFrame({
        "Worker": ["001", "002", "003", "005", "006"],
        "Year": [1944, 1948, 1947, 1945, 1948],
        "JobCode": ["B", "E", "C", "A", "D"],
    })
    workers["Exposure"] = workers.apply(
        lambda r: exposure_lookup.get(
            (r["Year"], r["JobCode"].upper()), np.nan
        ), axis=1,
    )
    return workers


def run_all() -> None:
    datasets = load_all_datasets()
    survey = datasets["survey"]

    print_dataset(example_22_1(survey).reset_index(), "22-1: Age Frequency")
    print_dataset(example_22_2(survey), "22-2: AgeGroup Variable")
    print_dataset(example_22_3(), "22-3: Grade INVALUE")
    print_dataset(example_22_4(), "22-4: Case-insensitive INVALUE")
    print_dataset(example_22_5(), "22-5: Temperature N→98.6")
    print_dataset(example_22_8(), "22-8: Item Lookup")
    print_dataset(example_22_11(), "22-11: ICD Format")
    print_dataset(example_22_14(), "22-14: Registration Format")
    print_dataset(example_22_17(survey), "22-17: Multilabel Age Groups")
    print_dataset(example_22_22(), "22-22: Exposure Formats from Data")


if __name__ == "__main__":
    run_all()
