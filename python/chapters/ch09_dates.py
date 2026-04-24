"""
Chapter 9 — Working with Dates
===============================
Date parsing, arithmetic, extraction, intervals — Python equivalents
using ``pandas.Timestamp`` and ``datetime``.

SAS Programs: 9-1 through 9-11
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from utils.data_helpers import data_dir, print_dataset


# 9-1 / 9-2: Read Dates.txt with multiple date formats
def example_9_1() -> pd.DataFrame:
    """Read dates in several formats (SAS informats: mmddyy, date9)."""
    path = data_dir() / "Dates.txt"
    if path.exists():
        return pd.read_fwf(
            path,
            colspecs=[(0, 3), (4, 14), (15, 23), (25, 33), (33, 42)],
            names=["Subject", "DOB", "VisitDate", "TwoDigit", "LastDate"],
        )
    text = """\
001 10/21/1946 06/15/06 10/1/08 21OCT2016
002 11/11/1956 06/01/06 07/5/07 15JUL2017
003 05/07/1968 09/22/06 10/3/06 31DEC2017"""
    df = pd.read_csv(
        StringIO(text), sep=r"\s+",
        names=["Subject", "DOB", "VisitDate", "TwoDigit", "LastDate"],
    )
    for col in ["DOB", "VisitDate", "TwoDigit", "LastDate"]:
        df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
    return df


# 9-3: Computing age (SAS yrdif)
def example_9_3(dates_df: pd.DataFrame) -> pd.DataFrame:
    """Compute age from DOB to VisitDate (SAS YRDIF equivalent)."""
    df = dates_df.copy()
    for col in ["DOB", "VisitDate"]:
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
    df["Age"] = (df["VisitDate"] - df["DOB"]).dt.days / 365.25
    df["Age"] = df["Age"].round(1)
    return df


# 9-4: Age as of a fixed date
def example_9_4(dates_df: pd.DataFrame) -> pd.DataFrame:
    """Age as of 01Jan2017 (SAS: yrdif(DOB, '01Jan2017'd))."""
    df = dates_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["DOB"]):
        df["DOB"] = pd.to_datetime(df["DOB"], format="mixed", dayfirst=False)
    ref_date = pd.Timestamp("2017-01-01")
    df["Age"] = ((ref_date - df["DOB"]).dt.days / 365.25).round(1)
    return df


# 9-5: Age as of today
def example_9_5(dates_df: pd.DataFrame) -> pd.DataFrame:
    """Age as of today (SAS: yrdif(DOB, today()))."""
    df = dates_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["DOB"]):
        df["DOB"] = pd.to_datetime(df["DOB"], format="mixed", dayfirst=False)
    today = pd.Timestamp.today().normalize()
    df["Age"] = ((today - df["DOB"]).dt.days / 365.25).round(1)
    return df


# 9-6: Extracting date components (SAS weekday, day, month, year)
def example_9_6(dates_df: pd.DataFrame) -> pd.DataFrame:
    """Extract weekday, day, month, year from DOB."""
    df = dates_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["DOB"]):
        df["DOB"] = pd.to_datetime(df["DOB"], format="mixed", dayfirst=False)
    df["Weekday"] = df["DOB"].dt.dayofweek + 1  # SAS: 1=Sun; Python: +1 for Mon=1
    df["DayOfMonth"] = df["DOB"].dt.day
    df["Month"] = df["DOB"].dt.month
    df["Year"] = df["DOB"].dt.year
    return df


# 9-7: Creating a date from components (SAS MDY)
def example_9_7() -> pd.DataFrame:
    """SAS mdy(Month, Day, Year) equivalent."""
    df = pd.DataFrame({
        "Month": [10, 3, 5],
        "Day": [21.0, np.nan, 7.0],
        "Year": [1950, 2005, 2000],
    })
    df["Date"] = pd.to_datetime(
        df.assign(Day=df["Day"].fillna(15))
        [["Year", "Month", "Day"]].rename(columns={"Day": "day", "Month": "month", "Year": "year"})
    )
    return df


# 9-8: Substituting missing day with 15 (SAS: if missing(Day) then mdy(Month,15,Year))
def example_9_8() -> pd.DataFrame:
    """Replace missing Day with 15 before constructing date."""
    df = pd.DataFrame({
        "Month": [10, 3, 5],
        "Day": [21.0, np.nan, 7.0],
        "Year": [1950, 2005, 2000],
    })
    df["Day_filled"] = df["Day"].fillna(15).astype(int)
    df["Date"] = pd.to_datetime(
        df[["Year", "Month", "Day_filled"]]
        .rename(columns={"Day_filled": "day", "Month": "month", "Year": "year"})
    )
    return df


# 9-9: Date intervals — quarter counting (SAS INTCK)
def example_9_9() -> pd.DataFrame:
    """Quarterly admissions count (SAS INTCK('qtr',...) equivalent)."""
    dates = pd.date_range("2003-01-15", periods=20, freq="3ME")
    df = pd.DataFrame({"AdmitDate": dates})
    ref = pd.Timestamp("2002-12-31")
    df["Quarter"] = ((df["AdmitDate"].dt.year - ref.year) * 4
                     + df["AdmitDate"].dt.quarter - ref.quarter)
    return df


# 9-10 / 9-11: Adding intervals (SAS INTNX)
def example_9_10() -> pd.DataFrame:
    """Add 6 months to discharge date (SAS INTNX('month',Discharge,6))."""
    df = pd.DataFrame({
        "Patient": ["A", "B", "C"],
        "Discharge": pd.to_datetime(["2006-10-01", "2006-11-15", "2007-01-20"]),
    })
    df["FollowDate_begin"] = df["Discharge"] + pd.offsets.MonthBegin(6)
    df["FollowDate_same"] = df["Discharge"].apply(
        lambda d: d + relativedelta(months=6)
    )
    return df


def run_all() -> None:
    dates_df = example_9_1()
    print_dataset(dates_df, "9-1: Dates")
    print_dataset(example_9_3(dates_df), "9-3: Age from DOB to VisitDate")
    print_dataset(example_9_4(dates_df), "9-4: Age as of 01Jan2017")
    print_dataset(example_9_6(dates_df), "9-6: Date Components")
    print_dataset(example_9_7(), "9-7: MDY construction")
    print_dataset(example_9_9(), "9-9: Quarter counting")
    print_dataset(example_9_10(), "9-10: Add 6 months")


if __name__ == "__main__":
    run_all()
