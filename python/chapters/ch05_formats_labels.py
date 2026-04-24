"""
Chapter 5 — Creating Formats and Labels
========================================
Demonstrates mapping raw values to display labels — Python equivalents
of PROC FORMAT and LABEL statements.

SAS Programs: 5-1 through 5-7
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset
from utils.formats import (
    GENDER_FMT, LIKERT_FMT, THREE_FMT, DX_FMT,
    age_group_fmt, apply_format,
)


def example_5_1(survey: pd.DataFrame) -> None:
    """Apply $Gender format and $Likert format (PROC FREQ with formats)."""
    df = survey.copy()
    df["Gender_Label"] = df["Gender"].map(GENDER_FMT)
    df["Ques1_Label"] = df["Ques1"].map(LIKERT_FMT)
    print_dataset(df[["ID", "Gender", "Gender_Label", "Ques1", "Ques1_Label"]],
                  "Survey with Format Labels")


def example_5_2(survey: pd.DataFrame) -> None:
    """Apply Three_FMT to collapse Likert categories."""
    df = survey.copy()
    for col in ["Ques1", "Ques2", "Ques3"]:
        df[f"{col}_Three"] = df[col].map(THREE_FMT)
    print_dataset(
        df[["ID", "Ques1", "Ques1_Three", "Ques2", "Ques2_Three"]],
        "Collapsed Likert Categories",
    )


def example_5_3(survey: pd.DataFrame) -> None:
    """Apply AgeGroup format using a function."""
    df = survey.copy()
    df["AgeGroup"] = df["Age"].apply(age_group_fmt)
    print_dataset(df[["ID", "Age", "AgeGroup"]], "Age Groups")


def example_5_4() -> None:
    """Apply DX format to diagnosis codes."""
    diagnoses = pd.DataFrame({"DX": ["1", "3", "5", "7"]})
    diagnoses["Description"] = diagnoses["DX"].apply(
        lambda x: apply_format(x, DX_FMT)
    )
    print_dataset(diagnoses, "Diagnosis Code Lookup")


def example_5_5(survey: pd.DataFrame) -> None:
    """PROC PRINT with formatted variables and labels."""
    df = survey.copy()
    df["Gender_Label"] = df["Gender"].map(GENDER_FMT)
    df["AgeGroup"] = df["Age"].apply(age_group_fmt)
    labeled = df.rename(columns={
        "ID": "Subject ID",
        "Gender_Label": "Gender",
        "AgeGroup": "Age Group",
        "Salary": "Annual Salary",
    })
    print_dataset(
        labeled[["Subject ID", "Gender", "Age Group", "Annual Salary"]],
        "Survey Listing with Labels and Formats",
    )


def run_all() -> None:
    datasets = load_all_datasets()
    survey = datasets["survey"]
    example_5_1(survey)
    example_5_2(survey)
    example_5_3(survey)
    example_5_4()
    example_5_5(survey)


if __name__ == "__main__":
    run_all()
