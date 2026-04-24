"""
Chapter 18 — PROC TABULATE
===========================
Multi-dimensional summary tables, nesting, percentages — Python
equivalents using ``pivot_table`` and ``crosstab``.

SAS Programs: 18-1 through 18-22
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 18-1: One-way frequency (CLASS variable only)
def example_18_1(blood: pd.DataFrame) -> pd.DataFrame:
    """TABLE Gender (one-way frequency)."""
    return blood["Gender"].value_counts().sort_index().to_frame("N")


# 18-2: Concatenation — multiple CLASS variables
def example_18_2(blood: pd.DataFrame) -> None:
    """TABLE Gender BloodType (concatenated one-way tables)."""
    for col in ["Gender", "BloodType"]:
        counts = blood[col].value_counts().sort_index()
        print_dataset(counts.to_frame("N").reset_index().rename(
            columns={"index": col}), f"Frequency: {col}")


# 18-3: Two-dimensional table (row × column)
def example_18_3(blood: pd.DataFrame) -> pd.DataFrame:
    """TABLE Gender, BloodType (2D frequency)."""
    return pd.crosstab(blood["Gender"], blood["BloodType"])


# 18-4: Nested table (SAS Gender * BloodType)
def example_18_4(blood: pd.DataFrame) -> pd.DataFrame:
    """Nested: Gender × BloodType counts."""
    return (
        blood.groupby(["Gender", "BloodType"])
        .size()
        .reset_index(name="N")
    )


# 18-5: Adding ALL margins
def example_18_5(blood: pd.DataFrame) -> pd.DataFrame:
    """Gender × BloodType with ALL (margins)."""
    return pd.crosstab(blood["Gender"], blood["BloodType"], margins=True)


# 18-6 / 18-7: Analysis variables (SAS VAR + mean)
def example_18_7(blood: pd.DataFrame) -> pd.DataFrame:
    """RBC*mean WBC*mean."""
    return pd.DataFrame({
        "RBC_Mean": [blood["RBC"].mean()],
        "WBC_Mean": [blood["WBC"].mean()],
    }).round(2)


# 18-8: Multiple statistics per variable
def example_18_8(blood: pd.DataFrame) -> pd.DataFrame:
    """(RBC WBC) × (mean min max)."""
    return (
        blood[["RBC", "WBC"]]
        .agg(["mean", "min", "max"])
        .round(2)
    )


# 18-9: CLASS + analysis — multi-dimensional
def example_18_9(blood: pd.DataFrame) -> pd.DataFrame:
    """(Gender ALL) × (AgeGroup ALL), (RBC WBC Chol) × mean."""
    grouped = (
        blood.groupby(["Gender", "AgeGroup"])[["RBC", "WBC", "Chol"]]
        .mean()
        .round(2)
    )
    grand = blood[["RBC", "WBC", "Chol"]].mean().round(2).to_frame("All").T
    by_gender = (
        blood.groupby("Gender")[["RBC", "WBC", "Chol"]].mean().round(2)
    )
    by_age = (
        blood.groupby("AgeGroup")[["RBC", "WBC", "Chol"]].mean().round(2)
    )
    return pd.concat([grouped, by_gender, by_age, grand])


# 18-11: Format keywords and labels
def example_18_11(blood: pd.DataFrame) -> pd.DataFrame:
    """Gender × (RBC WBC) with labeled statistics."""
    result = (
        blood.groupby("Gender")[["RBC", "WBC"]]
        .agg(["mean", "std"])
    )
    return result.round(2)


# 18-14: Counts and percentages
def example_18_14(blood: pd.DataFrame) -> pd.DataFrame:
    """BloodType: N and Percent."""
    counts = blood["BloodType"].value_counts().sort_index()
    pct = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"Count": counts, "Percent": pct})


# 18-16: Column percentages in a two-way table
def example_18_16(blood: pd.DataFrame) -> pd.DataFrame:
    """BloodType × Gender: count and column percentage."""
    ct = pd.crosstab(blood["BloodType"], blood["Gender"], margins=True)
    pct = pd.crosstab(blood["BloodType"], blood["Gender"],
                       normalize="columns", margins=True) * 100
    combined = ct.astype(str) + " (" + pct.round(1).astype(str) + "%)"
    return combined


# 18-18: Percentage of a numerical sum
def example_18_18(sales: pd.DataFrame) -> pd.DataFrame:
    """Region: N, Sum of TotalSales, Percent of total sales."""
    grouped = sales.groupby("Region")["TotalSales"].agg(["count", "sum"])
    grouped.columns = ["N", "Sum"]
    grouped["PctSum"] = (grouped["Sum"] / grouped["Sum"].sum() * 100).round(1)
    total = pd.DataFrame({
        "N": [grouped["N"].sum()],
        "Sum": [grouped["Sum"].sum()],
        "PctSum": [100.0],
    }, index=["All Regions"])
    return pd.concat([grouped, total])


def run_all() -> None:
    datasets = load_all_datasets()
    blood = datasets["blood"]
    sales = datasets["sales"]

    print_dataset(example_18_1(blood).reset_index(), "18-1: Gender Frequency")
    print_dataset(example_18_3(blood).reset_index(), "18-3: Gender × BloodType")
    print_dataset(example_18_5(blood).reset_index(), "18-5: With ALL Margins")
    print_dataset(example_18_8(blood), "18-8: RBC/WBC Mean, Min, Max")
    print_dataset(example_18_14(blood), "18-14: Counts & Percentages")
    print_dataset(example_18_16(blood), "18-16: Column Percentages")
    print_dataset(example_18_18(sales), "18-18: Sales Pct of Total")


if __name__ == "__main__":
    run_all()
