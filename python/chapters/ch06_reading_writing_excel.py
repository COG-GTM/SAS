"""
Chapter 6 — Reading and Writing Data from Other Sources
=======================================================
Excel files, CSV, and other external formats.

SAS Programs: 6-1 through 6-5
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.data_helpers import data_dir, output_dir, print_dataset


# 6-1: PROC IMPORT CSV equivalent
def example_6_1() -> pd.DataFrame:
    """Read a CSV file (PROC IMPORT DATAFILE= ... DBMS=CSV)."""
    return pd.read_csv(data_dir() / "Soccer.csv")


# 6-2: PROC IMPORT XLS equivalent
def example_6_2() -> pd.DataFrame:
    """Read an Excel .xls file."""
    path = data_dir() / "Sales.xls"
    if path.exists():
        return pd.read_excel(path, engine="xlrd")
    return pd.DataFrame(columns=["Note"], data=[["Sales.xls not found"]])


# 6-3: PROC IMPORT XLSX equivalent
def example_6_3() -> pd.DataFrame:
    """Read an Excel .xlsx file."""
    path = data_dir() / "Wages.xlsx"
    if path.exists():
        return pd.read_excel(path, engine="openpyxl")
    return pd.DataFrame(columns=["Note"], data=[["Wages.xlsx not found"]])


# 6-4: PROC EXPORT CSV equivalent
def example_6_4(df: pd.DataFrame) -> Path:
    """Export a DataFrame to CSV (PROC EXPORT DBMS=CSV)."""
    out = output_dir() / "exported_data.csv"
    df.to_csv(out, index=False)
    return out


# 6-5: PROC EXPORT XLSX equivalent
def example_6_5(df: pd.DataFrame) -> Path:
    """Export a DataFrame to Excel."""
    out = output_dir() / "exported_data.xlsx"
    df.to_excel(out, index=False, engine="openpyxl")
    return out


def run_all() -> None:
    csv_df = example_6_1()
    print_dataset(csv_df.head(), "Soccer CSV data")

    xls_df = example_6_2()
    print_dataset(xls_df.head(), "Sales XLS data")

    xlsx_df = example_6_3()
    print_dataset(xlsx_df.head(), "Wages XLSX data")

    sample = csv_df.head()
    csv_out = example_6_4(sample)
    xlsx_out = example_6_5(sample)
    print(f"Exported CSV to: {csv_out}")
    print(f"Exported XLSX to: {xlsx_out}")


if __name__ == "__main__":
    run_all()
