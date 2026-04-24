"""
Chapter 3 — Reading Raw Data
=============================
Column input, formatted input, list input, mixed input styles.
Demonstrates reading fixed-width and various delimited formats.

SAS Programs: 3-1 through 3-9
"""
from __future__ import annotations

from io import StringIO

import pandas as pd

from utils.data_helpers import data_dir, print_dataset, read_fixed_width


# 3-1: Column input (fixed-width positions)
def example_3_1() -> pd.DataFrame:
    """Fixed-width reading of bank.txt: Subj(1-3), DOB(4-13), Gender(14), Balance(15-21)."""
    return read_fixed_width(
        "bank.txt",
        colspecs=[(0, 3), (3, 13), (13, 14), (14, 21)],
        names=["Subj", "DOB", "Gender", "Balance"],
    )


# 3-2: Formatted input with dates
def example_3_2() -> pd.DataFrame:
    """Read bank.txt and parse DOB as a date."""
    df = example_3_1()
    df["DOB"] = pd.to_datetime(df["DOB"], format="mixed", dayfirst=False)
    return df


# 3-3: Mixed input — combining column and list input
def example_3_3() -> pd.DataFrame:
    """Read grades.txt (space-delimited, missing values as '.')."""
    df = pd.read_csv(
        data_dir() / "grades.txt",
        sep=r"\s+",
        names=["Age", "Gender", "Score", "Grade", "FinalScore"],
        na_values=["."],
    )
    return df


# 3-4: Reading from an Excel file
def example_3_4() -> pd.DataFrame:
    """Read Soccer.csv."""
    return pd.read_csv(data_dir() / "Soccer.csv")


# 3-5: Reading with specific informats (SAS : modifier equivalent)
def example_3_5() -> pd.DataFrame:
    """Demonstrate reading data with modified list input."""
    text = """\
001 M 23 28000 1 2 1 2 3
002 F 55 76123 4 5 2 1 1
003 M 38 36500 2 2 2 2 1"""
    return pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["ID", "Gender", "Age", "Salary",
               "Ques1", "Ques2", "Ques3", "Ques4", "Ques5"],
    )


# 3-6: Multiple lines per observation (SAS #n line pointers)
def example_3_6() -> pd.DataFrame:
    """Multi-line records — build address data."""
    records = [
        {"Name": "Ron Cody", "Street": "1178 Highway 480",
         "City": "Camp Verde", "State": "TX", "Zip": "78010"},
        {"Name": "Jason Tran", "Street": "123 Lake View Drive",
         "City": "East Rockaway", "State": "NY", "Zip": "11518"},
    ]
    return pd.DataFrame(records)


# 3-7: Reading Excel files with openpyxl
def example_3_7() -> pd.DataFrame:
    """Read Sales.xls with xlrd (old .xls format)."""
    path = data_dir() / "Sales.xls"
    if path.exists():
        return pd.read_excel(path, engine="xlrd")
    return pd.DataFrame()


# 3-8: Reading comma-delimited data with embedded commas
def example_3_8() -> pd.DataFrame:
    """Demonstrate reading CSV with quoted fields."""
    text = '''"001","Christopher Mullens",11/12/1955,"$45,200"
"002","Michelle Kwo",9/12/1955,"$78,123"
"003","Roger W. McDonald",1/1/1960,"$107,200"'''
    df = pd.read_csv(
        StringIO(text),
        names=["ID", "Name", "DOB", "Salary"],
    )
    df["DOB"] = pd.to_datetime(df["DOB"])
    df["Salary"] = (
        df["Salary"].str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False).astype(float)
    )
    return df


def run_all() -> None:
    for label, func in [
        ("3-1: Bank (fixed-width)", example_3_1),
        ("3-2: Bank with dates", example_3_2),
        ("3-3: Grades", example_3_3),
        ("3-5: Survey inline", example_3_5),
        ("3-6: Multi-line address", example_3_6),
        ("3-8: CSV with quoted fields", example_3_8),
    ]:
        print_dataset(func(), label)


if __name__ == "__main__":
    run_all()
