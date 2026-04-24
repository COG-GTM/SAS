"""
Chapter 21 — Additional Topics in Reading Data
===============================================
MISSOVER, PAD, END=, OBS=, FIRSTOBS=, multi-line records, trailing @@,
multiple input files — Python equivalents.

SAS Programs: 21-1 through 21-18
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from utils.data_helpers import print_dataset, read_fixed_width


# 21-1 / 21-2: MISSOVER — missing values for short records
def example_21_1() -> pd.DataFrame:
    """Read data with short lines → missing values (SAS MISSOVER)."""
    text = """\
1 2 3
4 5
6"""
    return pd.read_csv(
        StringIO(text), sep=r"\s+", names=["X", "Y", "Z"],
        na_values=[""],
    )


# 21-3 / 21-4: Fixed-width with PAD for short records
def example_21_3() -> pd.DataFrame:
    """Read fixed-width with short records (SAS PAD option)."""
    text = """\
001Jeffrey Smith   80 90 95
002Ron Cody         70 85
003Alan Wilson      90"""
    return pd.read_fwf(
        StringIO(text),
        colspecs=[(0, 3), (3, 19), (19, 22), (22, 25), (25, 28)],
        names=["Subject", "Name", "Quiz1", "Quiz2", "Quiz3"],
        header=None,
    )


# 21-5: END= option — processing the last record
def example_21_5() -> float:
    """Running total with final summary (SAS END= option)."""
    months = [1200, 1500, 1300, 1100, 1400, 1600,
              1250, 1350, 1450, 1550, 1650, 1700]
    return sum(months)


# 21-6: OBS= option — read first N records
def example_21_6() -> pd.DataFrame:
    """Read first 3 records only (SAS OBS=3)."""
    months = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Total": [1200, 1500, 1300, 1100, 1400, 1600,
                  1250, 1350, 1450, 1550, 1650, 1700],
    })
    return months.head(3)


# 21-7: FIRSTOBS= option — read records 5 through 7
def example_21_7() -> pd.DataFrame:
    """Read rows 5-7 (SAS FIRSTOBS=5 OBS=7)."""
    months = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Total": [1200, 1500, 1300, 1100, 1400, 1600,
                  1250, 1350, 1450, 1550, 1650, 1700],
    })
    return months.iloc[4:7].reset_index(drop=True)


# 21-12 / 21-13: Multi-line records (SAS #n line pointer / slash /)
def example_21_12() -> pd.DataFrame:
    """Read multi-line records (2 lines per observation)."""
    text = """\
00110/21/1955155
 68120 80
00309/01/1978200
 74 88 70
00505/07/1968110
 63100 60"""
    lines = text.strip().splitlines()
    rows = []
    for i in range(0, len(lines), 2):
        line1 = lines[i].ljust(18)
        line2 = lines[i + 1].ljust(12)
        rows.append({
            "Subj": line1[0:3].strip(),
            "DOB": line1[3:13].strip(),
            "Weight": int(line1[13:16].strip()) if line1[13:16].strip() else np.nan,
            "HR": int(line2[1:4].strip()) if line2[1:4].strip() else np.nan,
            "SBP": int(line2[4:7].strip()) if line2[4:7].strip() else np.nan,
            "DBP": int(line2[7:10].strip()) if line2[7:10].strip() else np.nan,
        })
    df = pd.DataFrame(rows)
    df["DOB"] = pd.to_datetime(df["DOB"], format="mixed", dayfirst=False)
    return df


# 21-16: Conditional record deletion (SAS: read Gender, skip if not 'F')
def example_21_16() -> pd.DataFrame:
    """Read only female records from bank.txt (SAS: DELETE if not F)."""
    df = read_fixed_width(
        "bank.txt",
        colspecs=[(0, 3), (3, 13), (13, 14), (14, 21)],
        names=["Subj", "DOB", "Gender", "Balance"],
    )
    return df[df["Gender"] == "F"].reset_index(drop=True)


# 21-17 / 21-18: Trailing @@ (multiple obs per line)
def example_21_18() -> pd.DataFrame:
    """Multiple observations per line (SAS trailing @@)."""
    text = "1 2  3 4  5 7  8 9  11 14  13 18  21 27\n30 40"
    values = text.split()
    pairs = [(int(values[i]), int(values[i + 1]))
             for i in range(0, len(values), 2)]
    return pd.DataFrame(pairs, columns=["X", "Y"])


def run_all() -> None:
    print_dataset(example_21_1(), "21-1: MISSOVER (short records)")
    print_dataset(example_21_3(), "21-3: Fixed-width with PAD")
    print(f"21-5: Year Total = ${example_21_5():,}\n")
    print_dataset(example_21_6(), "21-6: First 3 Records")
    print_dataset(example_21_7(), "21-7: Records 5-7")
    print_dataset(example_21_12(), "21-12: Multi-line Records")
    print_dataset(example_21_16(), "21-16: Females Only from bank.txt")
    print_dataset(example_21_18(), "21-18: Multiple Obs Per Line (@@)")


if __name__ == "__main__":
    run_all()
