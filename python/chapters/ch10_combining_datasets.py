"""
Chapter 10 — Subsetting and Combining SAS Data Sets
====================================================
SET, MERGE, concatenation, interleaving, one-to-many joins — Python
equivalents using ``pd.concat``, ``pd.merge``, ``DataFrame.update``.

SAS Programs: 10-1 through 10-16
"""
from __future__ import annotations


import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# Helper datasets used in chapter 10
def _build_one() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["7", "1", "2", "4"],
        "Name": ["Adams", "Smith", "Schneider", "Gregory"],
        "Weight": [210, 190, 110, 90],
    })


def _build_two() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["9", "3", "5"],
        "Name": ["Shea", "O'Brien", "Bessler"],
        "Weight": [120, 180, 207],
    })


def _build_three() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["10", "15", "20"],
        "Gender": ["M", "F", "M"],
        "Name": ["Horvath", "Stevens", "Brown"],
    })


def _build_employee() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["7", "1", "2", "4", "5"],
        "Name": ["Adams", "Smith", "Schneider", "Gregory", "Washington"],
    })


def _build_hours() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["1", "4", "9", "5"],
        "JobClass": ["A", "B", "B", "A"],
        "Hours": [39, 44, 57, 35],
    })


# 10-1: Subsetting with WHERE (filter)
def example_10_1(survey: pd.DataFrame) -> pd.DataFrame:
    """Keep only females (SAS: SET + WHERE Gender='F')."""
    return survey[survey["Gender"] == "F"].copy()


# 10-2: Subsetting + keeping selected columns
def example_10_2(survey: pd.DataFrame) -> pd.DataFrame:
    """Females, selected columns only (SAS KEEP= option)."""
    cols = ["ID", "Gender", "Age", "Ques1", "Ques2", "Ques3", "Ques4", "Ques5"]
    available = [c for c in cols if c in survey.columns]
    return survey.loc[survey["Gender"] == "F", available].copy()


# 10-3: Output to multiple datasets (split by condition)
def example_10_3(survey: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into Males and Females (SAS OUTPUT to two datasets)."""
    males = survey[survey["Gender"] == "M"].copy()
    females = survey[survey["Gender"] == "F"].copy()
    return males, females


# 10-4: Concatenating datasets (SAS SET One Two)
def example_10_4() -> pd.DataFrame:
    """Concatenate One and Two (SAS: SET One Two)."""
    one = _build_one()
    two = _build_two()
    return pd.concat([one, two], ignore_index=True)


# 10-5: Concatenating datasets with different columns
def example_10_5() -> pd.DataFrame:
    """Concatenate One and Three (different columns → NaN fill)."""
    one = _build_one()
    three = _build_three()
    return pd.concat([one, three], ignore_index=True)


# 10-6: Interleaving (sorted concat, SAS SET + BY)
def example_10_6() -> pd.DataFrame:
    """Interleave One and Two sorted by ID."""
    one = _build_one().sort_values("ID")
    two = _build_two().sort_values("ID")
    return pd.concat([one, two]).sort_values("ID").reset_index(drop=True)


# 10-7: Using a computed overall mean (SAS IF _N_=1 THEN SET Means)
def example_10_7(blood: pd.DataFrame) -> pd.DataFrame:
    """Percent of overall mean Cholesterol (SAS PROC MEANS + merge)."""
    chol_mean = blood["Chol"].mean()
    df = blood[["Subject", "Chol"]].copy()
    df["PercentChol"] = df["Chol"] / chol_mean
    return df


# 10-8: Simple merge (SAS MERGE + BY ID)
def example_10_8() -> pd.DataFrame:
    """Merge Employee and Hours by ID (outer join by default in SAS)."""
    emp = _build_employee()
    hrs = _build_hours()
    return emp.merge(hrs, on="ID", how="outer")


# 10-9: Merge with IN= flags (tracking match sources)
def example_10_9() -> pd.DataFrame:
    """Merge with source tracking (SAS IN= variables)."""
    emp = _build_employee()
    hrs = _build_hours()
    merged = emp.merge(hrs, on="ID", how="outer", indicator=True)
    merged["In_Employee"] = merged["_merge"].isin(["left_only", "both"])
    merged["In_Hours"] = merged["_merge"].isin(["right_only", "both"])
    return merged.drop(columns=["_merge"])


# 10-10: Inner join (SAS: IF In_Employee AND In_Hours)
def example_10_10() -> pd.DataFrame:
    """Inner join — only matching IDs."""
    emp = _build_employee()
    hrs = _build_hours()
    return emp.merge(hrs, on="ID", how="inner")


# 10-11: Conditional output (SAS: multiple OUTPUT destinations)
def example_10_11() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split merged data into 'In_Both' and 'Missing_Name'."""
    emp = _build_employee()
    hrs = _build_hours()
    merged = emp.merge(hrs, on="ID", how="outer", indicator=True)
    in_both = merged[merged["_merge"] == "both"].drop(columns="_merge")
    missing_name = (
        merged[merged["_merge"] == "right_only"]
        .drop(columns=["Name", "_merge"])
    )
    return in_both, missing_name


# 10-12: Interleaved SET with two datasets of different lengths
def example_10_12() -> pd.DataFrame:
    """Alternating rows from Short and Long datasets."""
    short = pd.DataFrame({"x": [1, 2]})
    long = pd.DataFrame({"x": [3, 4, 5, 6]})
    rows = []
    for i in range(max(len(short), len(long))):
        if i < len(short):
            rows.append(short.iloc[i].to_dict())
        if i < len(long):
            rows.append(long.iloc[i].to_dict())
    return pd.DataFrame(rows)


# 10-13: Merge with RENAME (SAS rename= option)
def example_10_13() -> pd.DataFrame:
    """Merge Bert and Ernie after renaming EmpNo → ID."""
    bert = pd.DataFrame({"ID": ["123", "222", "333"], "X": [90, 95, 100]})
    ernie = pd.DataFrame({"EmpNo": ["123", "222", "333"], "Y": [200, 205, 317]})
    ernie = ernie.rename(columns={"EmpNo": "ID"})
    return bert.merge(ernie, on="ID")


# 10-16: UPDATE statement (SAS UPDATE master transaction)
def example_10_16() -> pd.DataFrame:
    """Update Prices with new prices (SAS UPDATE statement)."""
    prices = pd.DataFrame({
        "ItemCode": ["150", "175", "200", "204", "208"],
        "Description": ["50 foot hose", "75 foot hose", "greeting card",
                        "25 lb. grass seed", "40 lb. fertilizer"],
        "Price": [19.95, 29.95, 1.99, 18.88, 17.98],
    })
    new_prices = pd.DataFrame({
        "ItemCode": ["204", "175", "208"],
        "Price": [17.87, 25.11, np.nan],
    })
    prices = prices.set_index("ItemCode")
    new_prices = new_prices.set_index("ItemCode")
    prices.update(new_prices)
    return prices.reset_index()


def run_all() -> None:
    datasets = load_all_datasets()
    survey = datasets["survey"]

    print_dataset(example_10_1(survey), "10-1: Females Only")
    males, females = example_10_3(survey)
    print_dataset(males, "10-3: Males")
    print_dataset(females, "10-3: Females")
    print_dataset(example_10_4(), "10-4: Concatenate One + Two")
    print_dataset(example_10_6(), "10-6: Interleaved by ID")
    print_dataset(example_10_8(), "10-8: Merge Employee + Hours")
    print_dataset(example_10_10(), "10-10: Inner Join")
    in_both, missing = example_10_11()
    print_dataset(in_both, "10-11: In Both")
    print_dataset(missing, "10-11: Missing Name")
    print_dataset(example_10_16(), "10-16: Updated Prices")


if __name__ == "__main__":
    run_all()
