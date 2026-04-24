"""
Solutions to Odd-Numbered Problems
===================================
Python equivalents of ``Solutions_to_Odd_Numbered_problems.sas``.
Each function corresponds to one exercise from the textbook.
"""
from __future__ import annotations


import numpy as np
import pandas as pd

from utils.data_helpers import data_dir, print_dataset


def prob_2_1() -> pd.DataFrame:
    """Chapter 2, Problem 1: Read Mydata.txt and compute BMI."""
    df = pd.read_csv(
        data_dir() / "Mydata.txt",
        sep=r"\s+",
        names=["Gender", "Age", "Height", "Weight"],
    )
    df["BMI"] = (df["Weight"] / df["Height"] ** 2) * 703
    return df


def prob_3_1() -> pd.DataFrame:
    """Chapter 3, Problem 1: Read bank.txt as fixed-width."""
    return pd.read_fwf(
        data_dir() / "bank.txt",
        colspecs=[(0, 3), (3, 13), (13, 14), (14, 21)],
        names=["Subj", "DOB", "Gender", "Balance"],
        header=None,
    )


def prob_7_1() -> pd.DataFrame:
    """Chapter 7, Problem 1: Classify grades."""
    df = pd.read_csv(
        data_dir() / "grades.txt",
        sep=r"\s+",
        names=["Age", "Gender", "Score", "Grade", "FinalScore"],
        na_values=["."],
    )
    df["PassFail"] = np.where(df["FinalScore"] >= 65, "Pass", "Fail")
    return df


def prob_8_1() -> pd.DataFrame:
    """Chapter 8, Problem 1: Generate multiplication table 1-10."""
    rows = []
    for i in range(1, 11):
        for j in range(1, 11):
            rows.append({"I": i, "J": j, "Product": i * j})
    return pd.DataFrame(rows)


def prob_9_1() -> pd.DataFrame:
    """Chapter 9, Problem 1: Compute age from two dates."""
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Carol"],
        "DOB": pd.to_datetime(["1980-03-15", "1975-07-22", "1990-11-01"]),
        "VisitDate": pd.to_datetime(["2017-01-15", "2017-06-01", "2017-12-10"]),
    })
    df["Age"] = ((df["VisitDate"] - df["DOB"]).dt.days / 365.25).round(1)
    return df


def prob_10_1() -> pd.DataFrame:
    """Chapter 10, Problem 1: Merge two datasets."""
    a = pd.DataFrame({"ID": [1, 2, 3], "Name": ["A", "B", "C"]})
    b = pd.DataFrame({"ID": [2, 3, 4], "Score": [80, 90, 70]})
    return a.merge(b, on="ID", how="inner")


def prob_11_1() -> pd.DataFrame:
    """Chapter 11, Problem 1: Row-wise statistics."""
    df = pd.DataFrame({
        "ID": [1, 2, 3],
        "X1": [10, 20, np.nan],
        "X2": [15, np.nan, 25],
        "X3": [20, 30, 35],
    })
    cols = ["X1", "X2", "X3"]
    df["Mean"] = df[cols].mean(axis=1).round(1)
    df["N"] = df[cols].count(axis=1)
    df["Max"] = df[cols].max(axis=1)
    return df


def prob_12_1() -> pd.DataFrame:
    """Chapter 12, Problem 1: Extract first and last name."""
    names = ["John Smith", "Mary Jane Watson", "Bob"]
    df = pd.DataFrame({"FullName": names})
    df["First"] = df["FullName"].str.split().str[0]
    df["Last"] = df["FullName"].str.split().str[-1]
    return df


def prob_13_1() -> pd.DataFrame:
    """Chapter 13, Problem 1: Replace 999 with NaN using array logic."""
    df = pd.DataFrame({
        "A": [10, 999, 30],
        "B": [999, 20, 40],
        "C": [50, 60, 999],
    })
    return df.replace(999, np.nan)


def prob_17_1() -> pd.DataFrame:
    """Chapter 17, Problem 1: Frequency table."""
    data = ["A", "B", "A", "C", "B", "A", "A", "C", "B", "B"]
    s = pd.Series(data, name="Category")
    counts = s.value_counts().sort_index()
    pct = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"Frequency": counts, "Percent": pct})


def prob_23_1() -> pd.DataFrame:
    """Chapter 23, Problem 1: Wide to long."""
    df = pd.DataFrame({
        "ID": [1, 2],
        "Score1": [80, 90],
        "Score2": [85, 95],
        "Score3": [88, 92],
    })
    return df.melt(id_vars="ID", var_name="Test", value_name="Score")


def prob_26_1() -> pd.DataFrame:
    """Chapter 26, Problem 1: SQL-style query."""
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Carol", "Dave"],
        "Score": [92, 78, 85, 95],
        "Grade": ["A", "C", "B", "A"],
    })
    return df.query("Score >= 85").sort_values("Score", ascending=False)


def prob_27_1() -> pd.DataFrame:
    """Chapter 27, Problem 1: Regex validation."""
    import re
    emails = ["user@site.com", "bad", "a@b.org", "no-at-sign"]
    pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
    df = pd.DataFrame({"Email": emails})
    df["Valid"] = df["Email"].apply(lambda e: bool(pattern.match(e)))
    return df


def run_all() -> None:
    problems = [
        ("2-1", prob_2_1), ("3-1", prob_3_1), ("7-1", prob_7_1),
        ("8-1", prob_8_1), ("9-1", prob_9_1), ("10-1", prob_10_1),
        ("11-1", prob_11_1), ("12-1", prob_12_1), ("13-1", prob_13_1),
        ("17-1", prob_17_1), ("23-1", prob_23_1), ("26-1", prob_26_1),
        ("27-1", prob_27_1),
    ]
    for label, func in problems:
        df = func()
        print_dataset(df if isinstance(df, pd.DataFrame) else pd.DataFrame(),
                      f"Problem {label}")


if __name__ == "__main__":
    run_all()
