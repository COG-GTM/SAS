"""
Chapter 24 — Working with Multiple Observations per Subject
============================================================
FIRST./LAST. processing, counting visits, computing differences,
RETAIN across observations — Python groupby equivalents.

SAS Programs: 24-1 through 24-8
"""
from __future__ import annotations

import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 24-1: Keep the last visit per subject (SAS LAST.ID)
def example_24_1(clinic: pd.DataFrame) -> pd.DataFrame:
    """Keep last visit per ID (SAS: IF LAST.ID)."""
    return clinic.groupby("ID").last().reset_index()


# 24-2: Count visits per subject
def example_24_2(clinic: pd.DataFrame) -> pd.DataFrame:
    """Count visits (SAS: IF FIRST.ID THEN N_visits=0; N_visits+1; IF LAST.ID)."""
    counts = (
        clinic.groupby("ID")
        .size()
        .reset_index(name="N_visits")
    )
    return counts


# 24-3: Visit counts via PROC FREQ equivalent
def example_24_3(clinic: pd.DataFrame) -> pd.DataFrame:
    """PROC FREQ tables ID / out=Counts (same as value_counts)."""
    return (
        clinic["ID"].value_counts()
        .reset_index()
        .rename(columns={"count": "N_Visits"})
        .sort_values("ID")
        .reset_index(drop=True)
    )


# 24-4: Merge visit count back to original data
def example_24_4(clinic: pd.DataFrame) -> pd.DataFrame:
    """Add N_Visits to every row (SAS MERGE + PROC FREQ)."""
    counts = clinic.groupby("ID").size().reset_index(name="N_Visits")
    return clinic.merge(counts, on="ID")


# 24-5: Differences from previous visit (SAS LAG by group)
def example_24_5(clinic: pd.DataFrame) -> pd.DataFrame:
    """Visit-to-visit differences in HR, SBP, DBP (SAS LAG within BY group).

    Exclude patients with only one visit.
    """
    df = clinic.sort_values(["ID", "VisitDate"]).copy()
    single = df.groupby("ID").filter(lambda g: len(g) > 1)
    for col in ["HR", "SBP", "DBP"]:
        single[f"Diff_{col}"] = single.groupby("ID")[col].diff()
    return single.dropna(subset=["Diff_HR"]).reset_index(drop=True)


# 24-6: First-to-last visit difference
def example_24_6(clinic: pd.DataFrame) -> pd.DataFrame:
    """Diff between first and last visit (SAS FIRST.ID and LAST.ID)."""
    df = clinic.sort_values(["ID", "VisitDate"])
    multi = df.groupby("ID").filter(lambda g: len(g) > 1)

    first = multi.groupby("ID").first()
    last = multi.groupby("ID").last()

    result = pd.DataFrame({
        "ID": first.index,
        "Diff_HR": (last["HR"] - first["HR"]).values,
        "Diff_SBP": (last["SBP"] - first["SBP"]).values,
        "Diff_DBP": (last["DBP"] - first["DBP"]).values,
    })
    return result.reset_index(drop=True)


# 24-7: RETAIN pattern (carry forward a value)
def example_24_7(clinic: pd.DataFrame) -> pd.DataFrame:
    """First-to-last diff using RETAIN pattern (store first values)."""
    df = clinic.sort_values(["ID", "VisitDate"])
    multi = df.groupby("ID").filter(lambda g: len(g) > 1)

    def first_last_diff(group: pd.DataFrame) -> pd.Series:
        first_hr = group["HR"].iloc[0]
        first_sbp = group["SBP"].iloc[0]
        first_dbp = group["DBP"].iloc[0]
        last = group.iloc[-1]
        return pd.Series({
            "ID": group["ID"].iloc[0],
            "Diff_HR": last["HR"] - first_hr,
            "Diff_SBP": last["SBP"] - first_sbp,
            "Diff_DBP": last["DBP"] - first_dbp,
        })

    return multi.groupby("ID").apply(
        first_last_diff, include_groups=False
    ).reset_index(drop=True)


# 24-8: Flag if any visit had high BP (SAS RETAIN + conditional)
def example_24_8(clinic: pd.DataFrame) -> pd.DataFrame:
    """Flag 'Yes' if any visit had SBP > 140 (SAS RETAIN HighBP)."""
    df = clinic.sort_values(["ID", "VisitDate"])
    high_bp = df.groupby("ID")["SBP"].apply(
        lambda x: "Yes" if (x > 140).any() else "No"
    ).reset_index(name="HighBP")
    return high_bp


def run_all() -> None:
    datasets = load_all_datasets()
    clinic = datasets["clinic"]

    print_dataset(clinic, "Clinic Data (sorted)")
    print_dataset(example_24_1(clinic), "24-1: Last Visit per ID")
    print_dataset(example_24_2(clinic), "24-2: Visit Counts")
    print_dataset(example_24_5(clinic), "24-5: Visit-to-Visit Diffs")
    print_dataset(example_24_6(clinic), "24-6: First-to-Last Diff")
    print_dataset(example_24_8(clinic), "24-8: High BP Flag")


if __name__ == "__main__":
    run_all()
