"""
Chapter 15 — PROC REPORT
=========================
Grouping, ordering, computed columns, breaks — Python equivalents
using ``groupby``, ``agg``, and custom formatting.

SAS Programs: 15-1 through 15-20
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 15-1 / 15-2: Basic REPORT (same as PROC PRINT for display)
def example_15_1(medical: pd.DataFrame) -> None:
    """PROC REPORT defaults — display all columns."""
    print_dataset(medical, "Medical Data Report")


# 15-3: COLUMN statement — select and order columns
def example_15_3(medical: pd.DataFrame) -> None:
    """Select specific columns (COLUMN statement)."""
    print_dataset(medical[["Patno", "DX", "HR", "Weight"]],
                  "Report: Patno, DX, HR, Weight")


# 15-6: GROUP usage — aggregate statistics
def example_15_6(medical: pd.DataFrame) -> None:
    """GROUP by Clinic with mean HR and Weight."""
    grouped = (
        medical.groupby("Clinic")
        .agg(Avg_HR=("HR", "mean"), Avg_Weight=("Weight", "mean"))
        .round(0)
    )
    print_dataset(grouped.reset_index(), "Average HR and Weight by Clinic")


# 15-7: FLOW option (wrapping long text) — just display Comment column
def example_15_7(medical: pd.DataFrame) -> None:
    """Display with Comment column (FLOW equivalent)."""
    df = medical[["Patno", "VisitDate", "DX", "HR", "Weight", "Comment"]].copy()
    df["VisitDate"] = df["VisitDate"].dt.strftime("%d%b%Y").str.upper()
    with pd.option_context("display.max_colwidth", 35, "display.width", 120):
        print_dataset(df, "Report with Comments")


# 15-9: Multiple GROUP variables
def example_15_9(bicycles: pd.DataFrame) -> None:
    """Group by Country and Model (SAS multiple GROUP usages)."""
    grouped = (
        bicycles.groupby(["Country", "Model"])
        .agg(Units=("Units", "sum"), TotalSales=("TotalSales", "sum"))
        .reset_index()
    )
    grouped["Units"] = grouped["Units"].apply(lambda x: f"{x:,}")
    grouped["TotalSales"] = grouped["TotalSales"].apply(lambda x: f"${x:,.0f}")
    print_dataset(grouped, "Units and Sales by Country × Model")


# 15-11: ORDER usage — list in EmpID order
def example_15_11(sales: pd.DataFrame) -> None:
    """ORDER by EmpID (display each row, sorted)."""
    df = sales.sort_values("EmpID")[["EmpID", "Quantity", "TotalSales"]]
    print_dataset(df, "Sales in EmpID Order")


# 15-14: Report breaks (SAS RBREAK AFTER / SUMMARIZE)
def example_15_14(sales: pd.DataFrame) -> None:
    """Grand total break (SAS RBREAK AFTER / SUMMARIZE)."""
    df = sales[["Region", "Quantity", "TotalSales"]].sort_values("Region")
    print_dataset(df, "Sales by Region")
    print(f"  TOTAL: Quantity={sales['Quantity'].sum():,}  "
          f"TotalSales=${sales['TotalSales'].sum():,.2f}")


# 15-15: BY-group breaks (SAS BREAK AFTER region / SUMMARIZE)
def example_15_15(sales: pd.DataFrame) -> None:
    """Subtotals per region (SAS BREAK AFTER region)."""
    for region, grp in sales.sort_values("Region").groupby("Region"):
        print_dataset(
            grp[["Region", "Quantity", "TotalSales"]],
            f"Region: {region}",
        )
        print(f"  Subtotal: Qty={grp['Quantity'].sum():,} "
              f"Sales=${grp['TotalSales'].sum():,.2f}\n")


# 15-17: Computed column (SAS COMPUTE block)
def example_15_17(medical: pd.DataFrame) -> None:
    """Computed column: Weight in Kg (SAS COMPUTE WtKg)."""
    df = medical[["Patno", "Weight"]].copy()
    df["WtKg"] = (df["Weight"] / 2.2).round(1)
    print_dataset(df, "Weight in Kg (Computed)")


# 15-18: Computed character variable
def example_15_18(medical: pd.DataFrame) -> None:
    """Computed character variable Rate from HR."""
    df = medical[["Patno", "HR", "Weight"]].copy()
    df["Rate"] = np.where(
        df["HR"] > 75, "Fast",
        np.where(df["HR"] > 55, "Normal",
                 np.where(df["HR"].notna(), "Slow", "")),
    )
    print_dataset(df, "Heart Rate Classification")


# 15-19: ACROSS usage (SAS cross-tabulation in REPORT)
def example_15_19(bicycles: pd.DataFrame) -> None:
    """Cross-tabulation: Units by Country × Model (SAS ACROSS usage)."""
    pivot = bicycles.pivot_table(
        values="Units", index="Country", columns="Model",
        aggfunc="sum", fill_value=0,
    )
    print_dataset(pivot.reset_index(), "Units: Country × Model")


def run_all() -> None:
    datasets = load_all_datasets()
    medical = datasets["medical"]
    bicycles = datasets["bicycles"]
    sales = datasets["sales"]

    example_15_1(medical)
    example_15_6(medical)
    example_15_9(bicycles)
    example_15_14(sales)
    example_15_17(medical)
    example_15_18(medical)
    example_15_19(bicycles)


if __name__ == "__main__":
    run_all()
