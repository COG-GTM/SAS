"""
Chapter 16 — PROC MEANS
========================
Descriptive statistics, BY/CLASS grouping, OUTPUT datasets — Python
equivalents using ``describe``, ``agg``, ``groupby``.

SAS Programs: 16-1 through 16-17
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset
from utils.formats import chol_group_fmt


# 16-1: All defaults
def example_16_1(blood: pd.DataFrame) -> pd.DataFrame:
    """PROC MEANS with all defaults (N, Mean, Std, Min, Max)."""
    numeric_cols = blood.select_dtypes(include="number").columns
    return blood[numeric_cols].describe().T[["count", "mean", "std", "min", "max"]]


# 16-2: Selected statistics on specific variables
def example_16_2(blood: pd.DataFrame) -> pd.DataFrame:
    """N, NMISS, MEAN, MEDIAN, MIN, MAX for RBC and WBC."""
    stats = {}
    for col in ["RBC", "WBC"]:
        s = blood[col]
        stats[col] = {
            "N": s.count(),
            "NMiss": s.isna().sum(),
            "Mean": round(s.mean(), 1),
            "Median": round(s.median(), 1),
            "Min": round(s.min(), 1),
            "Max": round(s.max(), 1),
        }
    return pd.DataFrame(stats).T


# 16-3 / 16-4: BY/CLASS — statistics by group
def example_16_4(blood: pd.DataFrame) -> pd.DataFrame:
    """Statistics by Gender (CLASS statement equivalent)."""
    return (
        blood.groupby("Gender")[["RBC", "WBC"]]
        .agg(["count", lambda x: x.isna().sum(), "mean", "median", "min", "max"])
        .round(1)
    )


# 16-5: Using a format as a CLASS variable
def example_16_5(blood: pd.DataFrame) -> pd.DataFrame:
    """Group by formatted Cholesterol (Low/High)."""
    df = blood.copy()
    df["Chol_Group"] = df["Chol"].apply(chol_group_fmt)
    return (
        df.groupby("Chol_Group")[["RBC", "WBC"]]
        .agg(["count", lambda x: x.isna().sum(), "mean", "median"])
        .round(1)
    )


# 16-6: OUTPUT dataset with means
def example_16_6(blood: pd.DataFrame) -> pd.DataFrame:
    """Create summary dataset with means (SAS OUTPUT OUT=)."""
    return pd.DataFrame({
        "MeanRBC": [blood["RBC"].mean()],
        "MeanWBC": [blood["WBC"].mean()],
    }).round(2)


# 16-7: Multiple output statistics
def example_16_7(blood: pd.DataFrame) -> pd.DataFrame:
    """Multiple statistics in output dataset."""
    result = {}
    for col in ["RBC", "WBC"]:
        s = blood[col]
        result[f"M_{col}"] = [round(s.mean(), 2)]
        result[f"N_{col}"] = [s.count()]
        result[f"Miss_{col}"] = [s.isna().sum()]
        result[f"Med_{col}"] = [round(s.median(), 2)]
    return pd.DataFrame(result)


# 16-9: BY-group output statistics
def example_16_9(blood: pd.DataFrame) -> pd.DataFrame:
    """Output means and N by Gender (SAS BY + OUTPUT)."""
    return (
        blood.groupby("Gender")[["RBC", "WBC"]]
        .agg(["mean", "count"])
        .round(2)
        .reset_index()
    )


# 16-11: CLASS with NWAY (suppress overall/subtotals)
def example_16_11(blood: pd.DataFrame) -> pd.DataFrame:
    """CLASS Gender with NWAY — only per-group rows."""
    return (
        blood.groupby("Gender")[["RBC", "WBC"]]
        .agg(["mean", "count"])
        .round(2)
        .reset_index()
    )


# 16-12: Two CLASS variables
def example_16_12(blood: pd.DataFrame) -> pd.DataFrame:
    """CLASS Gender AgeGroup (two-way summary)."""
    return (
        blood.groupby(["Gender", "AgeGroup"])[["RBC", "WBC"]]
        .agg(["mean", "count"])
        .round(2)
        .reset_index()
    )


# 16-16: NWAY with mixed statistics
def example_16_16(blood: pd.DataFrame) -> pd.DataFrame:
    """Cell means with NWAY on Gender × AgeGroup, mixed stats."""
    return (
        blood.groupby(["Gender", "AgeGroup"])
        .agg(
            RBC_Mean=("RBC", "mean"),
            WBC_Mean=("WBC", "mean"),
            RBC_N=("RBC", "count"),
            WBC_N=("WBC", "count"),
            Chol_N=("Chol", "count"),
            Chol_Median=("Chol", "median"),
        )
        .round(2)
        .reset_index()
    )


# 16-17: PRINTALLTYPES
def example_16_17(blood: pd.DataFrame) -> None:
    """Print all type combinations (Grand, By Gender, By AgeGroup, Cell)."""
    print("--- Grand Mean ---")
    print_dataset(blood[["RBC", "WBC"]].agg(["mean", "count"]).T.round(1),
                  "Overall")
    print("--- By Gender ---")
    print_dataset(
        blood.groupby("Gender")[["RBC", "WBC"]].agg(["mean", "count"]).round(1),
        "By Gender",
    )
    print("--- By AgeGroup ---")
    print_dataset(
        blood.groupby("AgeGroup")[["RBC", "WBC"]].agg(["mean", "count"]).round(1),
        "By AgeGroup",
    )
    print("--- Cell Means ---")
    print_dataset(
        blood.groupby(["Gender", "AgeGroup"])[["RBC", "WBC"]]
        .agg(["mean", "count"]).round(1),
        "Gender × AgeGroup",
    )


def run_all() -> None:
    datasets = load_all_datasets()
    blood = datasets["blood"]

    print_dataset(example_16_1(blood), "16-1: All Defaults")
    print_dataset(example_16_2(blood), "16-2: Selected Stats (RBC, WBC)")
    print_dataset(example_16_6(blood), "16-6: Output Means")
    print_dataset(example_16_7(blood), "16-7: Multiple Stats")
    print_dataset(example_16_12(blood), "16-12: Two CLASS Variables")
    example_16_17(blood)


if __name__ == "__main__":
    run_all()
