"""
Chapter 25 — Introduction to the SAS Macro Language
====================================================
%LET, %MACRO/%MEND, SYMPUTX, macro parameters — Python equivalents
using functions, f-strings, and module-level variables.

SAS Programs: 25-1 through 25-11
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 25-1: Automatic macro variables (&SYSDATE9, &SYSTIME)
def example_25_1(test_scores: pd.DataFrame) -> None:
    """SAS &SYSDATE9 / &SYSTIME → Python datetime.now()."""
    now = datetime.now()
    title = f"The Date is {now.strftime('%d%b%Y').upper()} - the Time is {now.strftime('%H:%M')}"
    print_dataset(test_scores, title)


# 25-2: %LET — define a variable list
def example_25_2(blood: pd.DataFrame) -> None:
    """%LET Var_List = RBC WBC Chol → Python list."""
    var_list = ["RBC", "WBC", "Chol"]
    stats = (
        blood[var_list]
        .agg(["count", "mean", "min", "max"])
        .round(1)
    )
    print_dataset(stats.T, "Using a Macro Variable List")


# 25-3: %LET n — parameterized data generation
def example_25_3(n: int = 3) -> pd.DataFrame:
    """%LET n=3; DO Subj=1 TO &n; → function parameter."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "Subj": range(1, n + 1),
        "X": np.ceil(100 * rng.random(n)).astype(int),
    })


# 25-4: %MACRO Gen(n, Start, End)
def gen(n: int, start: int, end: int,
        seed: int | None = None) -> pd.DataFrame:
    """Generate n random integers in [start, end].

    SAS: %macro Gen(n, Start, End); → Python function.
    """
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "Subj": range(1, n + 1),
        "X": rng.integers(start, end + 1, size=n),
    })


# 25-5: %MACRO with keyword parameters and defaults
def gen_kw(n: int = 10, start: int = 1, end: int = 100,
           seed: int | None = None) -> pd.DataFrame:
    """SAS %macro Gen(n=, Start=, End=); → keyword arguments."""
    return gen(n, start, end, seed)


# 25-6: %MACRO Print(Dsn=, n=10)
def print_first_n(df: pd.DataFrame, name: str = "Dataset",
                  n: int = 10) -> None:
    """SAS %macro Print(Dsn=, n=10); → function with defaults."""
    print_dataset(df.head(n), f"Listing of {name} (First {n} Observations)")


# 25-8: Macro variable concatenation (SAS &prefix.123)
def example_25_8() -> pd.DataFrame:
    """SAS %let Prefix=abc; data &prefix.123; → f-string."""
    prefix = "abc"
    name = f"{prefix}123"
    df = pd.DataFrame({"x": [3]})
    print(f"Dataset name: {name}")
    return df


# 25-11: CALL SYMPUTX — store computed values as macro variables
def example_25_11(blood: pd.DataFrame) -> pd.DataFrame:
    """SAS CALL SYMPUTX → store means in Python variables, then use them."""
    ave_rbc = blood["RBC"].mean()
    ave_wbc = blood["WBC"].mean()

    df = blood[["Subject", "RBC", "WBC"]].head(5).copy()
    df["Per_RBC"] = df["RBC"] / ave_rbc
    df["Per_WBC"] = df["WBC"] / ave_wbc
    df["Per_RBC"] = df["Per_RBC"].apply(lambda x: f"{x:.1%}")
    df["Per_WBC"] = df["Per_WBC"].apply(lambda x: f"{x:.1%}")
    return df


def run_all() -> None:
    datasets = load_all_datasets()
    blood = datasets["blood"]
    test_scores = datasets["test_scores"]

    example_25_1(test_scores)
    example_25_2(blood)

    print_dataset(example_25_3(5), "25-3: Generate 5 Random Numbers")
    print_dataset(gen(4, 1, 100, seed=99), "25-4: Gen(4, 1, 100)")
    print_dataset(gen_kw(n=3, start=50, end=200, seed=42),
                  "25-5: Gen(n=3, Start=50, End=200)")
    print_first_n(blood, name="Blood", n=5)
    example_25_8()
    print_dataset(example_25_11(blood), "25-11: Percent of Mean")


if __name__ == "__main__":
    run_all()
