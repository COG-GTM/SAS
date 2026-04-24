"""
Chapter 7 — Performing Conditional Processing
==============================================
IF-THEN/ELSE, WHERE, Boolean logic — Python equivalents using
pandas boolean indexing and np.where / np.select.

SAS Programs: 7-1 through 7-8
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 7-1: IF-THEN to create a new variable
def example_7_1(blood: pd.DataFrame) -> pd.DataFrame:
    """Create a Chol_Level variable based on Cholesterol value."""
    df = blood.copy()
    conditions = [
        (df["Chol"] < 200) & df["Chol"].notna(),
        (df["Chol"] >= 200) & (df["Chol"] < 240),
        df["Chol"] >= 240,
    ]
    choices = ["Desirable", "Borderline", "High"]
    df["Chol_Level"] = np.select(conditions, choices, default="")
    return df


# 7-2: Subsetting IF (filtering rows)
def example_7_2(blood: pd.DataFrame) -> pd.DataFrame:
    """Keep only Female subjects (SAS: if Gender = 'F')."""
    return blood[blood["Gender"] == "F"].copy()


# 7-3: Multiple conditions with AND
def example_7_3(blood: pd.DataFrame) -> pd.DataFrame:
    """Female subjects with Cholesterol >= 200."""
    mask = (blood["Gender"] == "F") & (blood["Chol"] >= 200)
    return blood[mask].copy()


# 7-4: Multiple conditions with OR
def example_7_4(blood: pd.DataFrame) -> pd.DataFrame:
    """Subjects whose BloodType is A or O."""
    return blood[blood["BloodType"].isin(["A", "O"])].copy()


# 7-5: WHERE clause equivalent
def example_7_5(sales: pd.DataFrame) -> pd.DataFrame:
    """Sales with Quantity > 400 (SAS WHERE statement)."""
    return sales.query("Quantity > 400").copy()


# 7-6: IN operator
def example_7_6(sales: pd.DataFrame) -> pd.DataFrame:
    """Sales for EmpID in ('1843', '0177')."""
    return sales[sales["EmpID"].isin(["1843", "0177"])].copy()


# 7-7: IF-THEN-ELSE chain with assignment
def example_7_7() -> pd.DataFrame:
    """Classify ages into groups using conditional assignment."""
    text = """\
M 50 68 155
F 23 60 101
M 65 72 220
F 35 65 133
M 15 71 166"""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )
    conditions = [
        df["Age"] < 20,
        (df["Age"] >= 20) & (df["Age"] < 40),
        (df["Age"] >= 40) & (df["Age"] < 60),
        df["Age"] >= 60,
    ]
    choices = ["Child", "Young Adult", "Middle Age", "Senior"]
    df["AgeGroup"] = np.select(conditions, choices)
    return df


# 7-8: SELECT/WHEN equivalent (match-case style)
def example_7_8() -> pd.DataFrame:
    """Use a mapping dictionary for SELECT/WHEN style logic."""
    df = pd.DataFrame({"Color": [1, 2, 3, 4, 5]})
    color_map = {1: "Red", 2: "Blue", 3: "Green", 4: "Yellow"}
    df["ColorName"] = df["Color"].map(color_map).fillna("Other")
    return df


def run_all() -> None:
    datasets = load_all_datasets()
    blood = datasets["blood"]
    sales = datasets["sales"]

    print_dataset(example_7_1(blood).head(10), "7-1: Cholesterol Levels")
    print_dataset(example_7_2(blood).head(10), "7-2: Female Subjects Only")
    print_dataset(example_7_3(blood).head(10), "7-3: Female with High Chol")
    print_dataset(example_7_4(blood).head(10), "7-4: Blood Type A or O")
    print_dataset(example_7_5(sales), "7-5: Sales Quantity > 400")
    print_dataset(example_7_6(sales), "7-6: Sales for Specific EmpIDs")
    print_dataset(example_7_7(), "7-7: Age Groups")
    print_dataset(example_7_8(), "7-8: Color Lookup")


if __name__ == "__main__":
    run_all()
