"""
Chapter 26 — An Introduction to PROC SQL
=========================================
SELECT, WHERE, JOIN, CREATE TABLE, ORDER BY, UNION, subqueries — Python
equivalents using ``pandas`` and optional ``sqlite3``.

SAS Programs: 26-1 through 26-13
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 26-1: Simple SELECT with WHERE
def example_26_1(health: pd.DataFrame) -> pd.DataFrame:
    """SELECT Subj, Height, Weight FROM Health WHERE Height > 65."""
    return health.loc[
        health["Height"] > 65, ["Subj", "Height", "Weight"]
    ].copy()


# 26-2: SELECT *
def example_26_2(health: pd.DataFrame) -> pd.DataFrame:
    """SELECT * FROM Health WHERE Height > 65."""
    return health[health["Height"] > 65].copy()


# 26-3: CREATE TABLE AS SELECT
def example_26_3(health: pd.DataFrame) -> pd.DataFrame:
    """CREATE TABLE Height65 AS SELECT * ... WHERE Height > 65."""
    height65 = health[health["Height"] > 65].copy()
    return height65


# 26-4: Cartesian product (CROSS JOIN)
def example_26_4(health: pd.DataFrame,
                 demographic: pd.DataFrame) -> pd.DataFrame:
    """Cartesian product (SAS FROM Health, Demographic without WHERE)."""
    health_cp = health.assign(_key=1)
    demo_cp = demographic.assign(_key=1)
    return health_cp.merge(demo_cp, on="_key").drop(columns="_key")


# 26-6: Inner join with WHERE clause
def example_26_6(health: pd.DataFrame,
                 demographic: pd.DataFrame) -> pd.DataFrame:
    """Inner join on Subj (SAS WHERE H.Subj eq D.Subj)."""
    return health.merge(
        demographic, on="Subj", how="inner", suffixes=("_Health", "_Demog"),
    )


# 26-7: Inner join via DATA step MERGE equivalent
def example_26_7(health: pd.DataFrame,
                 demographic: pd.DataFrame) -> pd.DataFrame:
    """Same inner join using merge (SAS MERGE with IN= flags)."""
    return health.merge(demographic, on="Subj", how="inner")


# 26-8: Explicit INNER JOIN syntax
def example_26_8(health: pd.DataFrame,
                 demographic: pd.DataFrame) -> pd.DataFrame:
    """INNER JOIN equivalent."""
    return health.merge(demographic, on="Subj", how="inner")


# 26-9: LEFT, RIGHT, FULL joins
def example_26_9(health: pd.DataFrame,
                 demographic: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Left, Right, and Full joins."""
    return {
        "left": health.merge(demographic, on="Subj", how="left"),
        "right": health.merge(demographic, on="Subj", how="right"),
        "full": health.merge(demographic, on="Subj", how="outer"),
    }


# 26-11: Computed column using aggregate (SAS CALCULATED + MEAN)
def example_26_11(health: pd.DataFrame) -> pd.DataFrame:
    """Add Ave_Height and Percent_Height computed columns."""
    df = health.copy()
    ave = df["Height"].mean()
    df["Ave_Height"] = round(ave, 2)
    df["Percent_Height"] = (100 * df["Height"] / ave).round(2)
    return df


# 26-12: ORDER BY
def example_26_12(health: pd.DataFrame) -> pd.DataFrame:
    """ORDER BY Height."""
    return health.sort_values("Height")[["Subj", "Height", "Weight"]]


# 26-13: Fuzzy match using SPEDIS equivalent
def example_26_13(demographic: pd.DataFrame,
                  insurance: pd.DataFrame) -> pd.DataFrame:
    """Fuzzy match on Name (SAS SPEDIS ≤ 25)."""
    from difflib import SequenceMatcher

    rows = []
    for _, d in demographic.iterrows():
        for _, ins in insurance.iterrows():
            ratio = SequenceMatcher(
                None, d["Name"].upper(), ins["Name"].upper()
            ).ratio()
            score = round((1 - ratio) * 100)
            if score <= 25:
                rows.append({
                    "Subj": d["Subj"],
                    "Demo_Name": d["Name"],
                    "Insurance_Name": ins["Name"],
                    "SpedisScore": score,
                })
    return pd.DataFrame(rows)


# Bonus: Using actual SQL via sqlite3 (SAS PROC SQL equivalent)
def example_sql_via_sqlite(health: pd.DataFrame) -> pd.DataFrame:
    """Demonstrate actual SQL execution using sqlite3."""
    conn = sqlite3.connect(":memory:")
    health.to_sql("health", conn, index=False)
    result = pd.read_sql_query(
        "SELECT Subj, Height, Weight FROM health WHERE Height > 65 ORDER BY Height",
        conn,
    )
    conn.close()
    return result


def run_all() -> None:
    datasets = load_all_datasets()
    health = datasets["health"]
    demographic = datasets["demographic"]
    insurance = datasets["insurance"]

    print_dataset(example_26_1(health), "26-1: Height > 65")
    print_dataset(example_26_6(health, demographic),
                  "26-6: Inner Join on Subj")

    joins = example_26_9(health, demographic)
    for jtype, df in joins.items():
        print_dataset(df, f"26-9: {jtype.upper()} JOIN")

    print_dataset(example_26_11(health), "26-11: Computed Columns")
    print_dataset(example_26_12(health), "26-12: ORDER BY Height")
    print_dataset(example_26_13(demographic, insurance),
                  "26-13: Fuzzy Match (SPEDIS)")
    print_dataset(example_sql_via_sqlite(health),
                  "Bonus: SQL via sqlite3")


if __name__ == "__main__":
    run_all()
