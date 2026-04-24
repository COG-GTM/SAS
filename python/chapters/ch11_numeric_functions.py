"""
Chapter 11 — Numeric Functions
==============================
INT, ROUND, CEIL, MISSING, N, MEAN, MIN, MAX, LARGEST,
ABS, SQRT, EXP, LOG, RAND, LAG, DIF — Python equivalents.

SAS Programs: 11-1 through 11-20
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from utils.data_helpers import print_dataset


# 11-1: INT, ROUND, CEIL
def example_11_1() -> pd.DataFrame:
    """Truncation, rounding, ceiling (SAS INT, ROUND, CEIL)."""
    text = """\
18.8 100.7 98.25
25.12 122.4 5.99
64.99 188 0.0001"""
    df = pd.read_csv(StringIO(text), sep=r"\s+", names=["Age", "Weight", "Cost"])
    df["Age_Int"] = df["Age"].apply(int)
    df["WtKg"] = (df["Weight"] / 2.2).round(1)
    df["Weight_Round"] = df["Weight"].round(0)
    df["Next_Dollar"] = np.ceil(df["Cost"])
    return df


# 11-2 / 11-3: Detecting missing values
def example_11_2(blood: pd.DataFrame) -> pd.DataFrame:
    """Count missing values and classify Cholesterol (SAS MISSING function)."""
    df = blood.copy()
    df["MissGender"] = df["Gender"].isna().cumsum()
    df["MissWBC"] = df["WBC"].isna().cumsum()
    df["MissRBC"] = df["RBC"].isna().cumsum()
    df["Level"] = np.where(
        df["Chol"].isna(), "",
        np.where(df["Chol"] < 200, "Low", "High"),
    )
    return df


# 11-4: N, MEAN, MIN, MAX across row variables
def example_11_4() -> pd.DataFrame:
    """Row-wise N, MEAN, MIN, MAX (SAS N(), MEAN(), MIN(), MAX() of Q1-Q10)."""
    text = """\
001 4 1 3 9 1 2 3 5 . 3
002 3 5 4 2 . . . 2 4 .
003 9 8 7 6 5 4 3 2 1 5"""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["ID"] + [f"Q{i}" for i in range(1, 11)],
        na_values=["."],
    )
    q_cols = [f"Q{i}" for i in range(1, 11)]
    df["N_Valid"] = df[q_cols].notna().sum(axis=1)
    df["Score"] = np.where(
        df["N_Valid"] >= 7,
        df[q_cols].mean(axis=1).round(2),
        np.nan,
    )
    df["MaxScore"] = df[q_cols].max(axis=1)
    df["MinScore"] = df[q_cols].min(axis=1)
    return df


# 11-5: LARGEST function (top-N values per row)
def example_11_5() -> pd.DataFrame:
    """Sum of 3 largest values per row (SAS LARGEST function)."""
    text = """\
001 4 1 3 9 1 2 3 5 . 3
002 3 5 4 2 . . . 2 4 .
003 9 8 7 6 5 4 3 2 1 5"""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["ID"] + [f"Q{i}" for i in range(1, 11)],
        na_values=["."],
    )
    q_cols = [f"Q{i}" for i in range(1, 11)]

    def sum_top_n(row: pd.Series, n: int = 3) -> float:
        vals = row.dropna().nlargest(n)
        return vals.sum() if len(vals) == n else np.nan

    df["SumThree"] = df[q_cols].apply(sum_top_n, axis=1)
    return df


# 11-7: ABS, SQRT, EXP, LOG
def example_11_7() -> pd.DataFrame:
    """Math functions (SAS ABS, SQRT, EXP, LOG)."""
    x = pd.Series([2, -2, 10, 100], name="X")
    return pd.DataFrame({
        "X": x,
        "Absolute": x.abs(),
        "Square": np.sqrt(x.abs()),
        "Exponent": np.exp(x),
        "Natural": np.log(x.where(x > 0)),
    })


# 11-8: Constants (SAS CONSTANT function)
def example_11_8() -> dict[str, float]:
    """Mathematical constants."""
    return {
        "Pi": np.pi,
        "e": np.e,
        "MaxInt_float64": float(np.finfo(np.float64).max),
    }


# 11-9 / 11-10: Random numbers
def example_11_9(seed: int | None = None) -> pd.DataFrame:
    """Generate 10 uniform random numbers (SAS RAND('uniform'))."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"i": range(1, 11), "X": rng.random(10)})


# 11-11: Random subsetting
def example_11_11(blood: pd.DataFrame, frac: float = 0.1,
                  seed: int = 42) -> pd.DataFrame:
    """Random 10% sample (SAS: if rand('uniform') le .1)."""
    return blood.sample(frac=frac, random_state=seed)


# 11-13: Character → numeric conversion (SAS INPUT function)
def example_11_13() -> pd.DataFrame:
    """Convert character columns to numeric (SAS INPUT)."""
    df = pd.DataFrame({
        "Char_Height": ["58", "63", "45"],
        "Char_Weight": ["155", "200", "79"],
        "Char_Date": ["10/21/1950", "5/6/2005", "11/12/2004"],
    })
    df["Height"] = pd.to_numeric(df["Char_Height"])
    df["Weight"] = pd.to_numeric(df["Char_Weight"])
    df["Date"] = pd.to_datetime(df["Char_Date"])
    return df


# 11-14: Numeric → character conversion (SAS PUT function)
def example_11_14() -> pd.DataFrame:
    """Convert numeric values to formatted strings (SAS PUT)."""
    df = pd.DataFrame({
        "Date": pd.to_datetime(["10/21/1950", "5/6/2005"]),
        "Age": [58, 25],
        "Cost": [155.50, 200.75],
    })
    df["Char_Date"] = df["Date"].dt.strftime("%d%b%Y").str.upper()
    df["AgeGroup"] = np.where(df["Age"] < 20, "Group One",
                     np.where(df["Age"] < 40, "Group Two", "Group Three"))
    df["Char_Cost"] = df["Cost"].apply(lambda x: f"${x:,.2f}")
    return df


# 11-15: LAG function
def example_11_15() -> pd.DataFrame:
    """LAG and LAG2 (SAS LAG, LAG2)."""
    df = pd.DataFrame({"Time": [1, 2, 3, 4], "Temperature": [60, 62, 65, 70]})
    df["Prev_Temp"] = df["Temperature"].shift(1)
    df["Two_Back"] = df["Temperature"].shift(2)
    return df


# 11-17 / 11-18: DIF function (difference from previous)
def example_11_17() -> pd.DataFrame:
    """Difference from previous value (SAS DIF)."""
    df = pd.DataFrame({"Time": [1, 2, 3, 4], "Temperature": [60, 62, 65, 70]})
    df["Diff_Temp"] = df["Temperature"].diff()
    return df


# 11-19 / 11-20: Quiz scoring — drop 2 lowest, mean of top 6
def example_11_19() -> pd.DataFrame:
    """Drop 2 lowest quiz scores, compute mean of remaining 6."""
    text = """\
001 80 70 90 100 88 90 90 51
002 80 70 90 100 88 90 . .
003 60 60 70 70 70 70 80 ."""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["ID"] + [f"Quiz{i}" for i in range(1, 9)],
        na_values=["."],
    )
    q_cols = [f"Quiz{i}" for i in range(1, 9)]

    def top6_mean(row: pd.Series) -> float:
        vals = row.dropna().sort_values(ascending=False)
        if len(vals) >= 3:
            top = vals.iloc[: len(vals) - 2]
            return top.mean()
        return np.nan

    df["Quiz_Score"] = df[q_cols].apply(top6_mean, axis=1).round(2)
    return df


def run_all() -> None:
    print_dataset(example_11_1(), "11-1: INT, ROUND, CEIL")
    print_dataset(example_11_4(), "11-4: Row-wise N, MEAN, MIN, MAX")
    print_dataset(example_11_5(), "11-5: Sum of 3 Largest")
    print_dataset(example_11_7(), "11-7: Math Functions")
    print(f"11-8: Constants = {example_11_8()}\n")
    print_dataset(example_11_9(seed=1234567), "11-9: Random Numbers (seeded)")
    print_dataset(example_11_15(), "11-15: LAG")
    print_dataset(example_11_17(), "11-17: DIF")
    print_dataset(example_11_19(), "11-19: Quiz Scoring (drop 2 lowest)")


if __name__ == "__main__":
    run_all()
