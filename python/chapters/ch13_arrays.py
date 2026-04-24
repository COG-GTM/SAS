"""
Chapter 13 — Working with Arrays
=================================
SAS ARRAY → pandas column-wise / row-wise vectorized operations.

SAS Programs: 13-1 through 13-9
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from utils.data_helpers import print_dataset


# 13-1 / 13-2: Replace sentinel values with NaN (SAS: ARRAY + loop)
def example_13_1() -> pd.DataFrame:
    """Replace 999 sentinel with NaN (SAS: array Myvars{3}; if = 999 then .)."""
    df = pd.DataFrame({
        "Height": [58, 63, 999, 61],
        "Weight": [155, 200, 150, 999],
        "Age": [40, 55, 999, 32],
    })
    cols = ["Height", "Weight", "Age"]
    df[cols] = df[cols].replace(999, np.nan)
    return df


# 13-3: Replace character sentinels across all character columns
def example_13_3() -> pd.DataFrame:
    """Replace 'NA' and '?' with NaN across all character columns."""
    df = pd.DataFrame({
        "Height": ["58", "NA", "45"],
        "Weight": ["155", "200", "?"],
        "Date": ["10/21/1950", "NA", "11/12/2004"],
    })
    df = df.replace(["NA", "?"], np.nan)
    return df


# 13-4: PROPCASE across all character columns (SAS _CHARACTER_ array)
def example_13_4() -> pd.DataFrame:
    """Apply title case to all character columns (SAS PROPCASE + _CHARACTER_)."""
    df = pd.DataFrame({
        "Score": [100, 65, 95],
        "Last_Name": ["COdY", "sMITH", "scerbo"],
        "Ans1": ["A", "C", "D"],
        "Ans2": ["b", "C", "e"],
    })
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda s: s.str.title())
    return df


# 13-5: Fahrenheit to Celsius (SAS paired arrays)
def example_13_5() -> pd.DataFrame:
    """Convert 24 hourly Fahrenheit to Celsius (SAS paired arrays)."""
    temps = [35, 37, 40, 42, 44, 48, 55, 59, 62, 62, 64, 66,
             68, 70, 72, 75, 75, 72, 66, 55, 53, 52, 50, 45]
    df = pd.DataFrame({f"Fahren{i+1}": [t] for i, t in enumerate(temps)})
    for i in range(1, 25):
        df[f"Celsius{i}"] = ((df[f"Fahren{i}"] - 32) / 1.8).round(1)
    return df


# 13-6: Year-indexed arrays (SAS array Income{2010:2017})
def example_13_6() -> pd.DataFrame:
    """Compute 25% tax for each year 2010-2017 (SAS year-indexed array)."""
    text = """\
001 45000 47000 47500 48000 48000 52000 53000 55000
002 67130 68000 72000 70000 65000 52000 49000 40100"""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["ID"] + [f"Income{y}" for y in range(2010, 2018)],
    )
    for year in range(2010, 2018):
        df[f"Taxes{year}"] = (0.25 * df[f"Income{year}"]).round(2)
    return df


# 13-7: Scoring a test using an answer key (SAS _TEMPORARY_ array)
def example_13_7() -> pd.DataFrame:
    """Score a test against an answer key (SAS temporary array)."""
    key = list("ABCDEEDCBA")
    text = """\
123 ABCDEDDDCA
126 ABCDEEDCBA
129 DBCBCEDDEB"""
    rows = []
    for line in text.strip().splitlines():
        parts = line.split()
        sid = parts[0]
        answers = list(parts[1])
        raw = sum(a == k for a, k in zip(answers, key))
        rows.append({"ID": sid, "RawScore": raw,
                     "Percent": 100 * raw / len(key)})
    return pd.DataFrame(rows)


# 13-9: Two-dimensional lookup table (SAS 2D _TEMPORARY_ array)
def example_13_9() -> pd.DataFrame:
    """Benzene exposure lookup (SAS 2D temporary array indexed by Year × JobCode)."""
    levels = {
        (1944, "A"): 220, (1944, "B"): 180, (1944, "C"): 210,
        (1944, "D"): 110, (1944, "E"): 90,
        (1945, "A"): 202, (1945, "B"): 170, (1945, "C"): 208,
        (1945, "D"): 100, (1945, "E"): 85,
        (1946, "A"): 150, (1946, "B"): 110, (1946, "C"): 150,
        (1946, "D"): 60,  (1946, "E"): 50,
        (1947, "A"): 105, (1947, "B"): 56,  (1947, "C"): 88,
        (1947, "D"): 40,  (1947, "E"): 30,
        (1948, "A"): 60,  (1948, "B"): 30,  (1948, "C"): 40,
        (1948, "D"): 20,  (1948, "E"): 10,
        (1949, "A"): 45,  (1949, "B"): 22,  (1949, "C"): 22,
        (1949, "D"): 10,  (1949, "E"): 8,
    }
    workers = pd.DataFrame({
        "Year": [1944, 1945, 1946, 1947, 1948, 1949],
        "JobCode": ["A", "B", "C", "D", "E", "A"],
    })
    workers["Benzene"] = workers.apply(
        lambda r: levels.get((r["Year"], r["JobCode"]), np.nan), axis=1
    )
    return workers


def run_all() -> None:
    print_dataset(example_13_1(), "13-1: Replace 999 Sentinel")
    print_dataset(example_13_3(), "13-3: Replace Character Sentinels")
    print_dataset(example_13_4(), "13-4: PROPCASE All Chars")
    print_dataset(example_13_6(), "13-6: Yearly Taxes")
    print_dataset(example_13_7(), "13-7: Test Scoring")
    print_dataset(example_13_9(), "13-9: Benzene Lookup")


if __name__ == "__main__":
    run_all()
