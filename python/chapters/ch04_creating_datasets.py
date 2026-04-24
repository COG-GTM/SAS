"""
Chapter 4 — Creating Permanent SAS Data Sets
=============================================
Demonstrates saving and loading DataFrames — Python equivalents
of LIBNAME / permanent SAS data sets.

SAS Programs: 4-1 through 4-6
"""
from __future__ import annotations


import pandas as pd

from utils.data_helpers import data_dir, output_dir, print_dataset


# 4-1: Create a permanent data set (save DataFrame to file)
def example_4_1() -> None:
    """Save a DataFrame to CSV (equivalent of writing to LIBNAME)."""
    df = pd.read_csv(
        data_dir() / "Mydata.txt",
        sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )
    out = output_dir() / "mydata.csv"
    df.to_csv(out, index=False)
    print(f"Data set saved to {out}")


# 4-2: Read the permanent data set back
def example_4_2() -> pd.DataFrame:
    """Read the saved CSV back (equivalent of SET LIBNAME.dataset)."""
    return pd.read_csv(output_dir() / "mydata.csv")


# 4-3: Create a data set with computed variables
def example_4_3() -> pd.DataFrame:
    """Add computed columns (BMI, Weight in Kg)."""
    df = pd.read_csv(
        data_dir() / "Mydata.txt",
        sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )
    df["BMI"] = (df["Weight"] / df["Height"] ** 2) * 703
    df["WtKg"] = round(df["Weight"] / 2.2, 1)
    return df


# 4-4: Save multiple formats
def example_4_4(df: pd.DataFrame) -> None:
    """Save to both CSV and Parquet (portable formats)."""
    df.to_csv(output_dir() / "computed.csv", index=False)
    df.to_parquet(output_dir() / "computed.parquet", index=False)
    print("Saved computed.csv and computed.parquet")


# 4-5: Using PROC CONTENTS equivalent
def example_4_5(df: pd.DataFrame) -> None:
    """Display dataset metadata (PROC CONTENTS equivalent)."""
    print(f"Number of observations: {len(df)}")
    print(f"Number of variables: {len(df.columns)}")
    print("\nVariable Information:")
    print(df.dtypes.to_string())
    print("\nMemory usage:")
    print(df.memory_usage(deep=True).to_string())


def run_all() -> None:
    example_4_1()
    df = example_4_2()
    print_dataset(df, "Read back from CSV")

    computed = example_4_3()
    print_dataset(computed, "Data with Computed Variables")
    example_4_4(computed)
    example_4_5(computed)


if __name__ == "__main__":
    run_all()
