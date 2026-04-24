"""
Chapter 1 — What Is SAS? (Introduction)
========================================
Demonstrates loading data and basic reporting — the Python equivalents
of DATA step input and PROC PRINT.

SAS Programs: 1-1 through 1-4
"""
from __future__ import annotations


import pandas as pd

from utils.data_helpers import data_dir, print_dataset


# 1-1 / 1-2: Read Mydata.txt (space-delimited) and compute BMI
def example_1_1() -> pd.DataFrame:
    """Read Mydata.txt → compute BMI (kg/m^2)."""
    df = pd.read_csv(
        data_dir() / "Mydata.txt",
        sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )
    df["BMI"] = (df["Weight"] / df["Height"] ** 2) * 703
    return df


# 1-3: Read data from Veggies.txt
def example_1_3() -> pd.DataFrame:
    """Read Veggies.txt (space-delimited)."""
    return pd.read_csv(
        data_dir() / "Veggies.txt",
        sep=r"\s+",
        names=["VeggieID", "Name", "Code", "Price"],
    )


# 1-4: Print listing with selected variables
def example_1_4(df: pd.DataFrame) -> None:
    """Print listing (PROC PRINT equivalent)."""
    print_dataset(df[["Name", "Code", "Price"]],
                  title="Selected Variables from Veggies")


def run_all() -> None:
    mydata = example_1_1()
    print_dataset(mydata, "Listing of Mydata with BMI")

    veggies = example_1_3()
    print_dataset(veggies, "Listing of Veggies")
    example_1_4(veggies)


if __name__ == "__main__":
    run_all()
