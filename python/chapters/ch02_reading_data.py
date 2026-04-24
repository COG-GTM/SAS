"""
Chapter 2 — Reading Data from External Files
=============================================
Demonstrates reading CSV, delimited, and inline data — Python equivalents
of SAS INPUT and INFILE statements.

SAS Programs: 2-1 through 2-6
"""
from __future__ import annotations

from io import StringIO

import pandas as pd

from utils.data_helpers import data_dir, print_dataset


# 2-1: Read space-delimited data
def example_2_1() -> pd.DataFrame:
    """Reading Employee.txt (space-delimited)."""
    return pd.read_csv(
        data_dir() / "employee.txt",
        sep=r"\s+",
        names=["ID", "Name", "Department", "Salary"],
    )


# 2-2: Read CSV data
def example_2_2() -> pd.DataFrame:
    """Reading List.csv."""
    df = pd.read_csv(
        data_dir() / "List.csv",
        names=["ID", "Name", "DOB", "Salary"],
        quotechar='"',
    )
    df["DOB"] = pd.to_datetime(df["DOB"])
    df["Salary"] = (
        df["Salary"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )
    return df


# 2-3: Inline data (datalines equivalent)
def example_2_3() -> pd.DataFrame:
    """Inline data creation (SAS datalines)."""
    text = """\
M 50 68 155
F 23 60 101
M 65 72 220
F 35 65 133
M 15 71 166"""
    return pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )


# 2-4: Reading delimited data with a specific delimiter
def example_2_4() -> pd.DataFrame:
    """Reading data with tab delimiter."""
    return pd.read_csv(
        data_dir() / "Mydata.txt",
        sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )


def run_all() -> None:
    for name, func in [("Employee", example_2_1),
                        ("List.csv", example_2_2),
                        ("Inline data", example_2_3),
                        ("Mydata", example_2_4)]:
        df = func()
        print_dataset(df, f"Example: {name}")


if __name__ == "__main__":
    run_all()
