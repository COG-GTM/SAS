"""
Chapter 17 — PROC FREQ
=======================
Frequency tables, cross-tabulations, format-based grouping — Python
equivalents using ``value_counts``, ``pd.crosstab``.

SAS Programs: 17-1 through 17-11
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset
from utils.formats import (
    GENDER_FMT, LIKERT_FMT, AGREE_DISAGREE_FMT, COLORS_FMT,
    age_group_20,
)


# 17-1: All defaults — frequency for every variable
def example_17_1(survey: pd.DataFrame) -> None:
    """PROC FREQ with all defaults — one-way tables for every column."""
    for col in survey.columns:
        counts = survey[col].value_counts(dropna=False).sort_index()
        pct = (counts / len(survey) * 100).round(1)
        tbl = pd.DataFrame({"Frequency": counts, "Percent": pct})
        print_dataset(tbl.reset_index().rename(columns={"index": col}),
                      f"Frequency of {col}")


# 17-2: Selected variables with NOCUM
def example_17_2(survey: pd.DataFrame) -> None:
    """Frequency of Gender, Ques1-Ques3 without cumulative columns."""
    for col in ["Gender", "Ques1", "Ques2", "Ques3"]:
        counts = survey[col].value_counts(dropna=False).sort_index()
        pct = (counts / counts.sum() * 100).round(1)
        tbl = pd.DataFrame({"Frequency": counts, "Percent": pct})
        print_dataset(tbl.reset_index().rename(columns={"index": col}),
                      f"Frequency of {col}")


# 17-3: Adding formats to frequency tables
def example_17_3(survey: pd.DataFrame) -> None:
    """Apply $Gender and $Likert formats before counting."""
    df = survey.copy()
    df["Gender"] = df["Gender"].map(GENDER_FMT)
    for col in ["Ques1", "Ques2", "Ques3"]:
        df[col] = df[col].map(LIKERT_FMT)
    for col in ["Gender", "Ques1", "Ques2", "Ques3"]:
        counts = df[col].value_counts(dropna=False)
        pct = (counts / counts.sum() * 100).round(1)
        tbl = pd.DataFrame({"Frequency": counts, "Percent": pct})
        print_dataset(tbl.reset_index().rename(columns={"index": col}),
                      f"Formatted Frequency of {col}")


# 17-4: Formats to create groups
def example_17_4(survey: pd.DataFrame) -> None:
    """Use age_group_20 format to bin Age; Agree/Disagree for Ques5."""
    df = survey.copy()
    df["AgeGroup"] = df["Age"].apply(age_group_20)
    for col, data in [("AgeGroup", df), ("Ques5_Grouped", df)]:
        if col == "Ques5_Grouped":
            data = df.copy()
            data["Ques5_Grouped"] = data["Ques5"].map(AGREE_DISAGREE_FMT)
        counts = data[col].value_counts().sort_index()
        print_dataset(
            pd.DataFrame({"Frequency": counts}).reset_index()
            .rename(columns={"index": col}),
            f"Grouped Frequency: {col}",
        )


# 17-8 / 17-9: ORDER options (internal, formatted, data, freq)
def example_17_9() -> None:
    """Demonstrate ordering options for Color variable."""
    colors = pd.Series([3, 4, 1, 2, 3, 3, 3, 1, 2, 2], name="Color")
    df = pd.DataFrame({"Color": colors})
    df["ColorName"] = df["Color"].map(COLORS_FMT)

    print("--- ORDER=Internal (numeric value) ---")
    counts = df["Color"].value_counts().sort_index()
    print(counts, "\n")

    print("--- ORDER=Formatted (alphabetical of formatted value) ---")
    counts = df["ColorName"].value_counts().sort_index()
    print(counts, "\n")

    print("--- ORDER=Data (order of first appearance) ---")
    seen = []
    for v in df["ColorName"]:
        if v not in seen:
            seen.append(v)
    counts = df["ColorName"].value_counts()
    print(counts.reindex(seen), "\n")

    print("--- ORDER=Freq (descending frequency) ---")
    counts = df["ColorName"].value_counts()
    print(counts, "\n")


# 17-10: Two-way cross-tabulation (SAS Gender * BloodType)
def example_17_10(blood: pd.DataFrame) -> pd.DataFrame:
    """Two-way table of Gender by BloodType."""
    return pd.crosstab(blood["Gender"], blood["BloodType"], margins=True)


# 17-11: Three-way cross-tabulation
def example_17_11(blood: pd.DataFrame) -> None:
    """Three-way table: Gender × AgeGroup × BloodType."""
    for gender, grp in blood.groupby("Gender"):
        ct = pd.crosstab(grp["AgeGroup"], grp["BloodType"])
        print_dataset(ct.reset_index(), f"Gender={gender}: AgeGroup × BloodType")


def run_all() -> None:
    datasets = load_all_datasets()
    survey = datasets["survey"]
    blood = datasets["blood"]

    example_17_2(survey)
    example_17_3(survey)
    example_17_9()
    ct = example_17_10(blood)
    print_dataset(ct.reset_index(), "17-10: Gender × BloodType")
    example_17_11(blood)


if __name__ == "__main__":
    run_all()
