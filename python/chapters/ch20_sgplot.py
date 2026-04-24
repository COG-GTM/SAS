"""
Chapter 20 — PROC SGPLOT
=========================
Bar charts, scatter plots, series plots, histograms, box plots — Python
equivalents using ``matplotlib`` and ``seaborn``.

SAS Programs: 20-1 through 20-13
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from create_datasets import load_all_datasets
from utils.data_helpers import output_dir


def _save(fig: plt.Figure, name: str) -> Path:
    out = output_dir() / f"{name}.png"
    fig.savefig(out, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return out


# 20-1: Vertical bar chart
def example_20_1(blood: pd.DataFrame) -> Path:
    """VBAR BloodType."""
    fig, ax = plt.subplots()
    blood["BloodType"].value_counts().sort_index().plot.bar(ax=ax)
    ax.set_title("Vertical Bar Chart: Blood Type")
    ax.set_ylabel("Count")
    return _save(fig, "20_01_vbar")


# 20-2: Horizontal bar chart
def example_20_2(blood: pd.DataFrame) -> Path:
    """HBAR BloodType."""
    fig, ax = plt.subplots()
    blood["BloodType"].value_counts().sort_index().plot.barh(
        ax=ax, color="white", edgecolor="black", width=0.25,
    )
    ax.set_title("Horizontal Bar Chart: Blood Type")
    return _save(fig, "20_02_hbar")


# 20-3: Grouped bar chart (two variables)
def example_20_3(blood: pd.DataFrame) -> Path:
    """VBAR Gender / GROUP=BloodType."""
    fig, ax = plt.subplots()
    ct = pd.crosstab(blood["Gender"], blood["BloodType"])
    ct.plot.bar(ax=ax)
    ax.set_title("Blood Type by Gender")
    ax.legend(title="BloodType")
    return _save(fig, "20_03_grouped_bar")


# 20-4: Bar chart with response variable (mean)
def example_20_4(blood: pd.DataFrame) -> Path:
    """VBAR BloodType / RESPONSE=Chol STAT=MEAN."""
    fig, ax = plt.subplots()
    means = blood.groupby("BloodType")["Chol"].mean()
    means.plot.bar(ax=ax, color="white", edgecolor="black", width=0.5)
    ax.set_title("Mean Cholesterol by Blood Type")
    ax.set_ylabel("Mean Chol")
    return _save(fig, "20_04_response_bar")


# 20-5: Scatter plot
def example_20_5() -> Path:
    """SCATTER X=PetalWidth Y=PetalLength (Iris data)."""
    iris = sns.load_dataset("iris")
    fig, ax = plt.subplots()
    ax.scatter(iris["petal_width"], iris["petal_length"], alpha=0.6)
    ax.set_xlabel("Petal Width")
    ax.set_ylabel("Petal Length")
    ax.set_title("Scatter Plot: Iris Petal Dimensions")
    return _save(fig, "20_05_scatter")


# 20-6: Scatter with regression line and CI
def example_20_6() -> Path:
    """REG X=PetalWidth Y=PetalLength / CLM CLI."""
    iris = sns.load_dataset("iris")
    fig, ax = plt.subplots()
    sns.regplot(x="petal_width", y="petal_length", data=iris, ax=ax, ci=95)
    ax.set_title("Regression with 95% CI")
    return _save(fig, "20_06_regression")


# 20-7: Series plot (time series with moving average)
def example_20_7(stocks: pd.DataFrame) -> Path:
    """SERIES X=Date Y=Price; SERIES X=Date Y=Moving."""
    df = stocks.copy()
    df["Moving"] = df["Price"].rolling(window=3).mean()
    fig, ax = plt.subplots()
    ax.plot(df["Date"], df["Price"], label="Price", marker="o")
    ax.plot(df["Date"], df["Moving"], label="3-pt Moving Avg",
            linestyle="--")
    ax.set_title("Stock Price with Moving Average")
    ax.legend()
    fig.autofmt_xdate()
    return _save(fig, "20_07_series")


# 20-8: Smooth curve (spline)
def example_20_8() -> Path:
    """PBSPLINE X=PetalWidth Y=PetalLength."""
    iris = sns.load_dataset("iris")
    fig, ax = plt.subplots()
    sns.regplot(x="petal_width", y="petal_length", data=iris, ax=ax,
                lowess=False, order=3, scatter_kws={"alpha": 0.4})
    ax.set_title("Smooth Curve (Polynomial)")
    return _save(fig, "20_08_spline")


# 20-9: LOESS smooth
def example_20_9() -> Path:
    """LOESS X=PetalWidth Y=PetalLength."""
    iris = sns.load_dataset("iris")
    fig, ax = plt.subplots()
    sns.regplot(x="petal_width", y="petal_length", data=iris, ax=ax,
                lowess=True, scatter_kws={"alpha": 0.4})
    ax.set_title("LOESS Smooth")
    return _save(fig, "20_09_loess")


# 20-10: Histogram with density curve
def example_20_10(blood: pd.DataFrame) -> Path:
    """HISTOGRAM RBC; DENSITY RBC."""
    fig, ax = plt.subplots()
    rbc = blood["RBC"].dropna()
    ax.hist(rbc, bins=15, density=True, alpha=0.6, edgecolor="black")
    x = np.linspace(rbc.min(), rbc.max(), 100)
    from scipy.stats import norm
    mu, sigma = rbc.mean(), rbc.std()
    ax.plot(x, norm.pdf(x, mu, sigma), "r-", linewidth=2)
    ax.set_title("Histogram of RBC with Normal Curve")
    ax.set_xlabel("RBC")
    return _save(fig, "20_10_histogram")


# 20-11: Simple box plot
def example_20_11(blood: pd.DataFrame) -> Path:
    """HBOX RBC."""
    fig, ax = plt.subplots()
    ax.boxplot(blood["RBC"].dropna(), vert=False)
    ax.set_title("Box Plot of RBC")
    ax.set_xlabel("RBC")
    return _save(fig, "20_11_boxplot")


# 20-12: Grouped box plot
def example_20_12(blood: pd.DataFrame) -> Path:
    """HBOX RBC / GROUP=BloodType."""
    fig, ax = plt.subplots()
    groups = blood.dropna(subset=["RBC"]).groupby("BloodType")["RBC"]
    data = [g.values for _, g in groups]
    labels = [name for name, _ in groups]
    ax.boxplot(data, vert=False, labels=labels)
    ax.set_title("RBC by Blood Type")
    ax.set_xlabel("RBC")
    return _save(fig, "20_12_grouped_box")


# 20-13: Overlaid bar charts with transparency
def example_20_13() -> Path:
    """Overlaid bar charts (SAS transparency)."""
    iris = sns.load_dataset("iris")
    means = iris.groupby("species")[["petal_width", "petal_length"]].mean()
    fig, ax = plt.subplots()
    x = range(len(means))
    ax.bar(x, means["petal_width"], width=0.8, label="Petal Width",
           alpha=0.7)
    ax.bar(x, means["petal_length"], width=0.3, label="Petal Length",
           alpha=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(means.index)
    ax.set_title("Overlaid Bar Charts")
    ax.legend()
    return _save(fig, "20_13_overlay")


def run_all() -> None:
    datasets = load_all_datasets()
    blood = datasets["blood"]
    stocks = datasets["stocks"]

    paths = [
        example_20_1(blood),
        example_20_2(blood),
        example_20_3(blood),
        example_20_4(blood),
        example_20_5(),
        example_20_6(),
        example_20_7(stocks),
        example_20_10(blood),
        example_20_11(blood),
        example_20_12(blood),
        example_20_13(),
    ]
    for p in paths:
        print(f"Saved: {p}")


if __name__ == "__main__":
    run_all()
