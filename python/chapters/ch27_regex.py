"""
Chapter 27 — Introduction to Perl Regular Expressions
=====================================================
PRXMATCH, PRXPARSE, PRXCHANGE — Python equivalents using the ``re``
module and ``pandas.str`` regex methods.

SAS Programs: 27-1 through 27-6
"""
from __future__ import annotations

import re

import pandas as pd

from utils.data_helpers import print_dataset


# 27-1: Validate Social Security Numbers
def example_27_1() -> pd.DataFrame:
    r"""Check SSN format \d{3}-\d{2}-\d{4} (SAS PRXMATCH)."""
    ssns = ["123-45-6789", "123456789", "123-ab-9876", "999-888-7777"]
    pattern = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    df = pd.DataFrame({"SS": ssns})
    df["Valid"] = df["SS"].apply(lambda s: bool(pattern.match(s)))
    return df


# 27-2: Validate US ZIP Codes
def example_27_2() -> pd.DataFrame:
    r"""Check ZIP format \d{5}(-\d{4})? (SAS PRXMATCH)."""
    zips = ["12345", "78010-5049", "12Z44", "ABCDE", "08822"]
    pattern = re.compile(r"^\d{5}(-\d{4})?$")
    df = pd.DataFrame({"Zip": zips})
    df["Valid"] = df["Zip"].apply(lambda z: bool(pattern.match(z)))
    return df


# 27-3: Validate Phone Numbers
def example_27_3() -> pd.DataFrame:
    r"""Check phone format \(\d{3}\)\d{3}-\d{4} (SAS PRXMATCH)."""
    phones = ["(908)432-1234", "800.343.1234",
              "8882324444", "(888)456-1324"]
    pattern = re.compile(r"^\(\d{3}\)\d{3}-\d{4}$")
    df = pd.DataFrame({"Phone": phones})
    df["Valid"] = df["Phone"].apply(lambda p: bool(pattern.match(p)))
    return df


# 27-4: Standardize phone numbers
def example_27_4() -> pd.DataFrame:
    """Standardize phone to (xxx)xxx-xxxx format."""
    phones = ["(908)432-1234", "800.343.1234",
              "8882324444", "(888)456-1324"]
    df = pd.DataFrame({"Phone": phones})

    def standardize(phone: str) -> str:
        digits = re.sub(r"[^0-9]", "", phone)
        if len(digits) == 10:
            return f"({digits[:3]}){digits[3:6]}-{digits[6:]}"
        return phone

    df["Standard"] = df["Phone"].apply(standardize)
    return df


# 27-5 / 27-6: PRXPARSE + PRXMATCH (compiled pattern reuse)
def example_27_5() -> pd.DataFrame:
    """Validate SSN using compiled regex (SAS PRXPARSE + PRXMATCH)."""
    ssns = ["123-45-6789", "123456789", "123-ab-9876", "999-888-7777"]
    ssn_re = re.compile(r"^\d{3}-\d{2}-\d{4}$")
    df = pd.DataFrame({"SS": ssns})
    df["Valid"] = df["SS"].apply(lambda s: bool(ssn_re.match(s)))
    df["Error"] = ~df["Valid"]
    return df


# Bonus: Using pandas .str accessor for regex operations
def bonus_pandas_regex() -> pd.DataFrame:
    """Demonstrate pandas vectorized regex operations."""
    df = pd.DataFrame({
        "Text": [
            "Order #12345 placed on 2024-01-15",
            "No order here",
            "Order #99999 placed on 2024-03-20",
        ]
    })
    df["OrderNum"] = df["Text"].str.extract(r"#(\d+)")
    df["OrderDate"] = df["Text"].str.extract(r"(\d{4}-\d{2}-\d{2})")
    df["HasOrder"] = df["Text"].str.contains(r"Order #\d+", regex=True)
    return df


# Bonus: Email validation
def bonus_email_validation() -> pd.DataFrame:
    """Validate email addresses with regex."""
    emails = ["user@example.com", "bad-email", "name@domain.org",
              "no@dots", "valid.one@sub.domain.com"]
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    df = pd.DataFrame({"Email": emails})
    df["Valid"] = df["Email"].apply(lambda e: bool(pattern.match(e)))
    return df


def run_all() -> None:
    print_dataset(example_27_1(), "27-1: SSN Validation")
    print_dataset(example_27_2(), "27-2: ZIP Code Validation")
    print_dataset(example_27_3(), "27-3: Phone Validation")
    print_dataset(example_27_4(), "27-4: Phone Standardization")
    print_dataset(example_27_5(), "27-5: Compiled SSN Validation")
    print_dataset(bonus_pandas_regex(), "Bonus: Pandas Regex")
    print_dataset(bonus_email_validation(), "Bonus: Email Validation")


if __name__ == "__main__":
    run_all()
