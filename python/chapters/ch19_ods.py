"""
Chapter 19 — ODS (Output Delivery System)
==========================================
HTML output, styled tables, selective output, ODS OUTPUT — Python
equivalents using pandas Styler, HTML export, and selective display.

SAS Programs: 19-1 through 19-7
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

from create_datasets import load_all_datasets
from utils.data_helpers import output_dir, print_dataset


# 19-1: ODS HTML output
def example_19_1(test_scores: pd.DataFrame) -> Path:
    """Export to HTML (SAS ODS HTML)."""
    out = output_dir() / "sample.html"
    html = "<html><head><title>Test Scores</title></head><body>"
    html += "<h2>Listing of Test Scores</h2>"
    html += test_scores.to_html(index=False)

    stats_df = test_scores[["Score1", "Score2", "Score3"]].describe().round(2)
    html += "<h2>Descriptive Statistics</h2>"
    html += stats_df.to_html()
    html += "</body></html>"

    out.write_text(html)
    return out


# 19-4: ODS SELECT — extreme observations (PROC UNIVARIATE)
def example_19_4(blood: pd.DataFrame) -> pd.DataFrame:
    """Extreme values of RBC (SAS ODS SELECT ExtremeObs → nsmallest/nlargest)."""
    rbc = blood[["Subject", "RBC"]].dropna(subset=["RBC"])
    smallest = rbc.nsmallest(5, "RBC").reset_index(drop=True)
    largest = rbc.nlargest(5, "RBC").reset_index(drop=True)
    smallest.columns = ["Subject_Low", "RBC_Low"]
    largest.columns = ["Subject_High", "RBC_High"]
    return pd.concat([smallest, largest], axis=1)


# 19-6: ODS OUTPUT — capture T-test results
def example_19_6(blood: pd.DataFrame) -> pd.DataFrame:
    """T-test by Gender for RBC, WBC, Chol (SAS ODS OUTPUT ttests)."""
    results = []
    for var in ["RBC", "WBC", "Chol"]:
        male = blood.loc[blood["Gender"] == "M", var].dropna()
        female = blood.loc[blood["Gender"] == "F", var].dropna()
        t_stat, p_val = stats.ttest_ind(male, female, equal_var=True)
        results.append({
            "Variable": var,
            "tValue": round(t_stat, 2),
            "ProbT": round(p_val, 5),
        })
    return pd.DataFrame(results)


# 19-7: Filtered T-test results (SAS WHERE Variances = "Equal")
def example_19_7(blood: pd.DataFrame) -> pd.DataFrame:
    """Display T-test results with equal variance assumption."""
    ttest_df = example_19_6(blood)
    return ttest_df.rename(columns={"tValue": "T-Value", "ProbT": "P-Value"})


def run_all() -> None:
    datasets = load_all_datasets()
    test_scores = datasets["test_scores"]
    blood = datasets["blood"]

    html_path = example_19_1(test_scores)
    print(f"HTML output saved to: {html_path}\n")

    print_dataset(example_19_4(blood), "19-4: Extreme RBC Values")
    print_dataset(example_19_6(blood), "19-6: T-Test Results")
    print_dataset(example_19_7(blood), "19-7: Equal Variance T-Tests")


if __name__ == "__main__":
    run_all()
