"""
Chapter 14 — PROC PRINT
========================
Listing, filtering, sorting, labelling, totals — Python equivalents
using pandas display, sort_values, and groupby.

SAS Programs: 14-1 through 14-17
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 14-1: Basic listing (all defaults)
def example_14_1(sales: pd.DataFrame) -> None:
    """PROC PRINT with all defaults."""
    print_dataset(sales, "Listing of Sales")


# 14-2: Select variables
def example_14_2(sales: pd.DataFrame) -> None:
    """VAR statement (select columns)."""
    print_dataset(sales[["EmpID", "Customer", "TotalSales"]],
                  "Selected Variables")


# 14-3: Use ID variable instead of Obs
def example_14_3(sales: pd.DataFrame) -> None:
    """ID statement (use EmpID as row identifier)."""
    df = sales[["EmpID", "Customer", "TotalSales"]].copy()
    df = df.set_index("EmpID")
    print_dataset(df, "Sales with EmpID as ID")


# 14-4: Formatting columns
def example_14_4(sales: pd.DataFrame) -> None:
    """FORMAT statement (display formatting)."""
    df = sales[["EmpID", "Customer", "Quantity", "TotalSales"]].copy()
    df["TotalSales"] = df["TotalSales"].apply(lambda x: f"${x:,.2f}")
    df["Quantity"] = df["Quantity"].apply(lambda x: f"{x:,}")
    print_dataset(df, "Formatted Sales Listing")


# 14-5: WHERE filtering
def example_14_5(sales: pd.DataFrame) -> None:
    """WHERE Quantity > 400."""
    df = sales[sales["Quantity"] > 400].copy()
    print_dataset(df[["EmpID", "Customer", "Quantity", "TotalSales"]],
                  "Sales with Quantity > 400")


# 14-6: IN filtering
def example_14_6(sales: pd.DataFrame) -> None:
    """WHERE EmpID IN ('1843', '0177')."""
    df = sales[sales["EmpID"].isin(["1843", "0177"])].copy()
    print_dataset(df[["EmpID", "Customer", "Quantity", "TotalSales"]],
                  "Sales for EmpID 1843 and 0177")


# 14-8: Sort by TotalSales
def example_14_8(sales: pd.DataFrame) -> None:
    """PROC SORT by TotalSales."""
    df = sales.sort_values("TotalSales")[["EmpID", "Customer",
                                          "Quantity", "TotalSales"]]
    print_dataset(df, "Sorted by TotalSales (ascending)")


# 14-9: Descending sort
def example_14_9(sales: pd.DataFrame) -> None:
    """PROC SORT DESCENDING TotalSales."""
    df = sales.sort_values("TotalSales", ascending=False)
    print_dataset(df[["EmpID", "Customer", "TotalSales"]],
                  "Sorted by TotalSales (descending)")


# 14-11: Multi-key sort
def example_14_11(sales: pd.DataFrame) -> None:
    """Sort by EmpID (asc), then TotalSales (desc)."""
    df = sales.sort_values(["EmpID", "TotalSales"],
                           ascending=[True, False])
    print_dataset(df[["EmpID", "TotalSales", "Quantity"]],
                  "Sorted by EmpID, then TotalSales desc")


# 14-12: Labels as column headers
def example_14_12(sales: pd.DataFrame) -> None:
    """LABEL statement (rename columns for display)."""
    df = sales[["EmpID", "TotalSales", "Quantity"]].copy()
    df = df.rename(columns={
        "EmpID": "Employee ID",
        "TotalSales": "Total Sales",
        "Quantity": "Number Sold",
    })
    print_dataset(df, "Using Labels as Column Headings")


# 14-13: BY-group printing
def example_14_13(sales: pd.DataFrame) -> None:
    """BY Region (group-wise listing)."""
    for region, group in sales.sort_values("Region").groupby("Region"):
        print_dataset(
            group[["EmpID", "TotalSales", "Quantity"]],
            f"Region: {region}",
        )


# 14-14: Subtotals and grand total (SAS SUM statement)
def example_14_14(sales: pd.DataFrame) -> None:
    """BY Region with subtotals (SAS SUM statement)."""
    df = sales.sort_values("Region")
    for region, group in df.groupby("Region"):
        sub = group[["EmpID", "TotalSales", "Quantity"]].copy()
        print_dataset(sub, f"Region: {region}")
        print(f"  Subtotal: Quantity={group['Quantity'].sum():,}  "
              f"TotalSales=${group['TotalSales'].sum():,.2f}\n")
    print(f"Grand Total: Quantity={df['Quantity'].sum():,}  "
          f"TotalSales=${df['TotalSales'].sum():,.2f}")


# 14-17: First N observations
def example_14_17(sales: pd.DataFrame) -> None:
    """OBS=5 (first 5 rows)."""
    print_dataset(sales.head(5), "First 5 Observations")


def run_all() -> None:
    datasets = load_all_datasets()
    sales = datasets["sales"]
    example_14_1(sales)
    example_14_4(sales)
    example_14_5(sales)
    example_14_8(sales)
    example_14_11(sales)
    example_14_14(sales)
    example_14_17(sales)


if __name__ == "__main__":
    run_all()
