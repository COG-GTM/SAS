"""
Chapter 23 — Restructuring SAS Data Sets
=========================================
Wide ↔ long transformations — Python equivalents using
``pd.melt`` and ``pd.pivot_table`` (SAS PROC TRANSPOSE).

SAS Programs: 23-1 through 23-5
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 23-1: One-per-subject → many-per-subject (wide → long)
def example_23_1(oneper: pd.DataFrame) -> pd.DataFrame:
    """Reshape wide (Dx1-Dx3) to long (Visit, Diagnosis).

    SAS: DATA ManyPer; SET OnePer; ARRAY Dx{3}; DO Visit=1 TO 3; ...
    """
    dx_cols = [c for c in oneper.columns if c.startswith("Dx")]
    df = oneper.melt(
        id_vars="Subj",
        value_vars=dx_cols,
        var_name="Visit",
        value_name="Diagnosis",
    )
    df["Visit"] = df["Visit"].str.extract(r"(\d+)").astype(int)
    df = df.dropna(subset=["Diagnosis"]).sort_values(["Subj", "Visit"])
    df["Diagnosis"] = df["Diagnosis"].astype(int)
    return df.reset_index(drop=True)


# 23-2: Many-per-subject → one-per-subject (long → wide)
def example_23_2(manyper: pd.DataFrame) -> pd.DataFrame:
    """Reshape long to wide using RETAIN-style accumulation.

    SAS: DATA OnePer; SET ManyPer; BY Subj; ARRAY Dx{3}; RETAIN Dx1-Dx3; ...
    """
    return manyper.pivot(
        index="Subj", columns="Visit", values="Diagnosis",
    ).rename(columns=lambda v: f"Dx{v}").reset_index()


# 23-3: PROC TRANSPOSE (wide → long, default)
def example_23_3(oneper: pd.DataFrame) -> pd.DataFrame:
    """PROC TRANSPOSE DATA=OnePer OUT=ManyPer; BY Subj; VAR Dx1-Dx3."""
    dx_cols = [c for c in oneper.columns if c.startswith("Dx")]
    return oneper.melt(
        id_vars="Subj",
        value_vars=dx_cols,
        var_name="_NAME_",
        value_name="COL1",
    )


# 23-4: PROC TRANSPOSE with rename, drop, and where
def example_23_4(oneper: pd.DataFrame) -> pd.DataFrame:
    """Transpose + rename COL1→Diagnosis, drop _NAME_, filter out null."""
    dx_cols = [c for c in oneper.columns if c.startswith("Dx")]
    df = oneper.melt(
        id_vars="Subj",
        value_vars=dx_cols,
        var_name="_NAME_",
        value_name="Diagnosis",
    )
    df = df.dropna(subset=["Diagnosis"]).drop(columns="_NAME_")
    df["Diagnosis"] = df["Diagnosis"].astype(int)
    return df.reset_index(drop=True)


# 23-5: PROC TRANSPOSE (long → wide with ID and PREFIX)
def example_23_5(manyper: pd.DataFrame) -> pd.DataFrame:
    """PROC TRANSPOSE PREFIX=Dx; BY Subj; ID Visit; VAR Diagnosis."""
    return manyper.pivot(
        index="Subj", columns="Visit", values="Diagnosis",
    ).rename(columns=lambda v: f"Dx{v}").reset_index()


def run_all() -> None:
    datasets = load_all_datasets()
    oneper = datasets["oneper"]
    manyper = datasets["manyper"]

    print_dataset(oneper, "Original: One-Per-Subject")
    long = example_23_1(oneper)
    print_dataset(long, "23-1: Wide → Long (melt)")

    wide = example_23_2(manyper)
    print_dataset(wide, "23-2: Long → Wide (pivot)")

    print_dataset(example_23_3(oneper), "23-3: PROC TRANSPOSE default")
    print_dataset(example_23_4(oneper), "23-4: Transposed, filtered")
    print_dataset(example_23_5(manyper), "23-5: Long → Wide with prefix")


if __name__ == "__main__":
    run_all()
