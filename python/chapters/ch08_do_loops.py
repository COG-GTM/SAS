"""
Chapter 8 — Performing Iterative Processing (DO Loops)
======================================================
FOR loops, WHILE loops, UNTIL loops, LEAVE, CONTINUE — Python
equivalents using for/while/break/continue and pandas vectorized ops.

SAS Programs: 8-1 through 8-19
"""
from __future__ import annotations


import numpy as np
import pandas as pd

from utils.data_helpers import print_dataset


# 8-1: Simple DO loop generating a sequence
def example_8_1() -> pd.DataFrame:
    """Generate integers 1-10 (DO i = 1 TO 10)."""
    return pd.DataFrame({"i": range(1, 11)})


# 8-2: DO loop with BY (step)
def example_8_2() -> pd.DataFrame:
    """Odd numbers 1-9 (DO i = 1 TO 9 BY 2)."""
    return pd.DataFrame({"i": range(1, 10, 2)})


# 8-3: Compound interest calculation with RETAIN
def example_8_3() -> pd.DataFrame:
    """Compound interest: $100 at 3.75% until it doubles."""
    interest = 0.0375
    total = 100.0
    rows = []
    year = 0
    while total < 200:
        year += 1
        total += interest * total
        rows.append({"Year": year, "Total": round(total, 2)})
    return pd.DataFrame(rows)


# 8-4: Sum of 1-100 using a loop
def example_8_4() -> int:
    """Sum of 1 to 100 (Gauss: n*(n+1)/2 = 5050)."""
    return sum(range(1, 101))


# 8-5: Accumulating with RETAIN (running total)
def example_8_5() -> pd.DataFrame:
    """Running total of monthly values."""
    months = [100, 150, 200, 125, 300, 175, 225, 190, 210, 180, 160, 250]
    df = pd.DataFrame({"Month": range(1, 13), "Amount": months})
    df["RunningTotal"] = df["Amount"].cumsum()
    return df


# 8-6: Fibonacci sequence
def example_8_6(n: int = 20) -> pd.DataFrame:
    """Generate first n Fibonacci numbers."""
    fibs = [1, 1]
    for _ in range(n - 2):
        fibs.append(fibs[-1] + fibs[-2])
    return pd.DataFrame({"N": range(1, n + 1), "Fibonacci": fibs})


# 8-7: Table of squares and square roots
def example_8_7() -> pd.DataFrame:
    """Table of N, N^2, sqrt(N) for 1 to 10."""
    ns = list(range(1, 11))
    return pd.DataFrame({
        "N": ns,
        "Square": [n ** 2 for n in ns],
        "SquareRoot": [round(n ** 0.5, 5) for n in ns],
    })


# 8-8: DO loop with OUTPUT (equation plot data)
def example_8_8() -> pd.DataFrame:
    """Generate data for Y = 2X^3 - 5X^2 + 15X - 8."""
    x = np.arange(-10, 10.01, 0.01)
    y = 2 * x ** 3 - 5 * x ** 2 + 15 * x - 8
    return pd.DataFrame({"X": x, "Y": y})


# 8-9: Nested DO loops (group × subject)
def example_8_9() -> pd.DataFrame:
    """Nested loops: Placebo/Active × 5 subjects with scores."""
    scores = [250, 222, 230, 210, 199, 166, 183, 123, 129, 234]
    rows = []
    idx = 0
    for group in ["Placebo", "Active"]:
        for subj in range(1, 6):
            rows.append({"Group": group, "Subj": subj,
                         "Score": scores[idx]})
            idx += 1
    return pd.DataFrame(rows)


# 8-10: DO UNTIL (post-test loop)
def example_8_10() -> pd.DataFrame:
    """Compound interest with DO UNTIL (Total >= 200)."""
    interest = 0.0375
    total = 100.0
    rows = []
    year = 0
    while True:
        year += 1
        total += interest * total
        rows.append({"Interest": interest, "Year": year,
                      "Total": round(total, 2)})
        if total >= 200:
            break
    return pd.DataFrame(rows)


# 8-11: DO WHILE (pre-test loop)
def example_8_11() -> pd.DataFrame:
    """Compound interest with DO WHILE (Total <= 200)."""
    interest = 0.0375
    total = 100.0
    rows = []
    year = 0
    while total <= 200:
        year += 1
        total += interest * total
        rows.append({"Year": year, "Total": round(total, 2)})
    return pd.DataFrame(rows)


# 8-12: DO with LEAVE (break)
def example_8_12() -> pd.DataFrame:
    """Loop with early exit (SAS LEAVE statement)."""
    interest = 0.0375
    total = 100.0
    rows = []
    for year in range(1, 101):
        total += interest * total
        rows.append({"Year": year, "Total": round(total, 2)})
        if total >= 200:
            break
    return pd.DataFrame(rows)


# 8-13: DO with CONTINUE (skip)
def example_8_13() -> pd.DataFrame:
    """Loop with CONTINUE — only output when Total > 150."""
    interest = 0.0375
    total = 100.0
    rows = []
    for year in range(1, 101):
        total += interest * total
        if total <= 150:
            continue
        rows.append({"Year": year, "Total": round(total, 2)})
        if total >= 200:
            break
    return pd.DataFrame(rows)


def run_all() -> None:
    print_dataset(example_8_1(), "8-1: Simple Sequence")
    print_dataset(example_8_3(), "8-3: Compound Interest")
    print(f"8-4: Sum of 1-100 = {example_8_4()}\n")
    print_dataset(example_8_7(), "8-7: Squares and Roots")
    print_dataset(example_8_9(), "8-9: Nested Loops (Easyway)")
    print_dataset(example_8_10(), "8-10: DO UNTIL")
    print_dataset(example_8_12(), "8-12: DO with LEAVE")
    print_dataset(example_8_13(), "8-13: DO with CONTINUE")


if __name__ == "__main__":
    run_all()
