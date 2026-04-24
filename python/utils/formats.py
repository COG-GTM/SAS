"""
SAS Format Mappings → Python dictionaries/functions.

Replicates PROC FORMAT value/invalue definitions used throughout
the book "Learning SAS by Example, 2nd Edition."
"""
from __future__ import annotations

import math
from typing import Any


# ---------- Chapter 5 formats ----------

GENDER_FMT: dict[str, str] = {
    "M": "Male",
    "F": "Female",
    "": "Not entered",
}

LIKERT_FMT: dict[str, str] = {
    "1": "Strongly disagree",
    "2": "Disagree",
    "3": "No opinion",
    "4": "Agree",
    "5": "Strongly agree",
}

THREE_FMT: dict[str, str] = {
    "1": "Disagreement",
    "2": "Disagreement",
    "3": "No opinion",
    "4": "Agreement",
    "5": "Agreement",
}

DX_FMT: dict[str, str] = {
    "1": "Routine Visit",
    "2": "Cold",
    "3": "Heart Problems",
    "4": "GI Problems",
    "5": "Psychiatric",
    "6": "Injury",
    "7": "Infection",
}


def age_group_fmt(age: float | None) -> str:
    """SAS value Age low-29='Less than 30' 30-50='30 to 50' 51-high='51+'."""
    if age is None or math.isnan(age):
        return ""
    if age <= 29:
        return "Less than 30"
    if age <= 50:
        return "30 to 50"
    return "51+"


def age_group_20(age: float | None) -> str:
    """SAS value Agefmt 0-<20 / 20-<40 / 40-<60 / 60-high."""
    if age is None or math.isnan(age):
        return ""
    if age < 20:
        return "< 20"
    if age < 40:
        return "20 to 39"
    if age < 60:
        return "40 to 59"
    return "60+"


# ---------- Chapter 16 formats ----------

def chol_group_fmt(chol: float | None) -> str:
    if chol is None or math.isnan(chol):
        return ""
    return "Low" if chol < 200 else "High"


# ---------- Chapter 17 formats ----------

AGREE_DISAGREE_FMT: dict[str, str] = {
    "1": "Generally disagree",
    "2": "Generally disagree",
    "3": "No opinion",
    "4": "Generally agree",
    "5": "Generally agree",
}

COLORS_FMT: dict[int, str] = {
    1: "Yellow",
    2: "Blue",
    3: "Red",
    4: "Green",
}


# ---------- Chapter 22 formats ----------

GRADE_CONVERT: dict[str, float] = {
    "A+": 100, "A": 96, "A-": 92,
    "B+": 88, "B": 84, "B-": 80,
    "C+": 76, "C": 72, "F": 65,
}

ICD_FMT: dict[str, str] = {
    "020": "Plague",
    "022": "Anthrax",
    "390": "Rheumatic fever",
    "410": "Myocardial infarction",
    "493": "Asthma",
    "540": "Appendicitis",
}

NAME_LOOKUP: dict[int, str] = {
    122: "Salt",
    188: "Sugar",
    101: "Cereal",
    755: "Eggs",
}

PRICE_LOOKUP: dict[str, float] = {
    "Salt": 3.76,
    "Sugar": 4.99,
    "Cereal": 5.97,
    "Eggs": 2.65,
}


def apply_format(value: Any, fmt: dict) -> Any:
    """Look up *value* in *fmt* dict; return the mapped label or the
    original value if no mapping exists (like SAS ``other`` handling)."""
    return fmt.get(value, value)
