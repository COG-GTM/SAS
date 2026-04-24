"""
Chapter 12 — Character Functions
=================================
UPCASE, LOWCASE, PROPCASE, COMPRESS, FIND, SCAN, SUBSTR, TRANSLATE,
TRANWRD, SPEDIS, CAT/CATS/CATX — Python string method equivalents.

SAS Programs: 12-1 through 12-17
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from create_datasets import load_all_datasets
from utils.data_helpers import print_dataset


# 12-1: LENGTHN — string length
def example_12_1(sales: pd.DataFrame) -> pd.DataFrame:
    """Names longer than 12 characters (SAS LENGTHN > 12)."""
    return sales[sales["Name"].str.len() > 12].copy()


# 12-2: UPCASE for case-insensitive merging
def example_12_2() -> pd.DataFrame:
    """Standardize case before merge (SAS UPCASE)."""
    mixed = pd.DataFrame({"Name": ["ron cody", "ALAN WILSON", "Jason Tran"]})
    upper = pd.DataFrame({"Name": ["ALAN WILSON", "JASON TRAN", "RON CODY"]})
    mixed["Name"] = mixed["Name"].str.upper()
    return mixed.merge(upper, on="Name")


# 12-3: PROPCASE, COMPBL, UPCASE (address standardisation)
def example_12_3(address: pd.DataFrame) -> pd.DataFrame:
    """Standardize address data (SAS COMPBL + PROPCASE + UPCASE)."""
    df = address.copy()
    for col in ["Name", "Street", "City"]:
        df[col] = df[col].str.strip().str.title()
        df[col] = df[col].str.replace(r"\s+", " ", regex=True)
    df["State"] = df["State"].str.upper()
    return df


# 12-4: Concatenation functions (SAS CAT, CATS, CATX)
def example_12_4() -> dict[str, str]:
    """Demonstrate concatenation equivalents."""
    first = "Ron  "
    last = "Cody  "
    return {
        "cat": first + last,                          # SAS CAT
        "cats": first.strip() + last.strip(),         # SAS CATS
        "catx": " ".join([first.strip(), last.strip()]),  # SAS CATX
    }


# 12-5: STRIP, LEFT, TRIM (whitespace handling)
def example_12_5() -> dict[str, str]:
    """Whitespace functions (SAS LEFT, TRIMN, STRIP)."""
    s = "  ABC  "
    return {
        "left": s.lstrip(),
        "trim": s.rstrip(),
        "strip": s.strip(),
    }


# 12-6 / 12-7: COMPRESS — keep/remove characters
def example_12_6() -> pd.DataFrame:
    """Standardize phone numbers by keeping only digits (SAS COMPRESS)."""
    df = pd.DataFrame({
        "Phone": ["(908)235-4490", "800.555.1234",
                  "908 456-1111", "(210) 444.5050"],
    })
    df["PhoneNumber"] = df["Phone"].str.replace(r"[^0-9]", "", regex=True)
    return df


# 12-8: Mixed units conversion using FIND and COMPRESS
def example_12_8() -> pd.DataFrame:
    """Convert mixed weight/height units (SAS FIND + COMPRESS)."""
    df = pd.DataFrame({
        "Name": ["Ron", "Jan", "Peter"],
        "Weight": ["180lbs", "95Kg", "210 lb"],
        "Height": ["72in", "168cm", "74 In"],
    })
    wt_num = df["Weight"].str.replace(r"[^0-9.]", "", regex=True).astype(float)
    is_lb = df["Weight"].str.contains("lb", case=False)
    df["Wt_Kg"] = np.where(is_lb, wt_num / 2.2, wt_num).round(1)

    ht_num = df["Height"].str.replace(r"[^0-9.]", "", regex=True).astype(float)
    is_in = df["Height"].str.contains("in", case=False)
    df["Ht_Cm"] = np.where(is_in, ht_num * 2.54, ht_num).round(1)
    return df


# 12-9: FINDW — find whole word
def example_12_9() -> pd.DataFrame:
    """Find whole-word 'Roger' (SAS FINDW, case-insensitive)."""
    strings = ["Will Rogers", "Roger Cody",
               "Was roger here?", "Was Roger here?"]
    df = pd.DataFrame({"String": strings})
    df["Match"] = df["String"].str.contains(
        r"\bRoger\b", case=False, regex=True
    ).map({True: "Yes", False: "No"})
    return df


# 12-10: ANYDIGIT — find first digit position
def example_12_10() -> pd.DataFrame:
    """Find first digit in ID strings (SAS ANYDIGIT)."""
    ids = ["ABC123", "XY99ZZ", "NOPE", "7Start"]
    df = pd.DataFrame({"ID": ids})
    df["Position"] = df["ID"].apply(
        lambda x: m.start() if (m := re.search(r"\d", x)) else None
    )
    df["HasDigit"] = df["Position"].notna()
    return df


# 12-12: SUBSTR — extract substrings
def example_12_12() -> pd.DataFrame:
    """Extract state, number, gender from coded ID (SAS SUBSTR)."""
    ids = ["NJ12M99", "NY76F4512", "TX91M5"]
    df = pd.DataFrame({"ID": ids})
    df["State"] = df["ID"].str[:2]
    df["Number"] = df["ID"].str[2:4].astype(int)
    df["Gender"] = df["ID"].str[4]
    df["Last"] = df["ID"].str[5:]
    return df


# 12-13: SCAN — extract word tokens
def example_12_13() -> pd.DataFrame:
    """Extract first and last names (SAS SCAN)."""
    names = ["Jeffrey Smith", "Ron Cody", "Alan Wilson", "Alfred E. Newman"]
    df = pd.DataFrame({"Name": names})
    df["First"] = df["Name"].str.split().str[0]
    df["Last"] = df["Name"].str.split().str[-1]
    return df


# 12-15: SPEDIS — fuzzy match score
def example_12_15() -> pd.DataFrame:
    """Fuzzy match scoring (SAS SPEDIS approximation using edit distance)."""
    try:
        from difflib import SequenceMatcher
    except ImportError:
        return pd.DataFrame()

    target = "Friedman"
    candidates = ["Friedman", "Freedman", "Xriedman", "Freidman",
                  "Friedmann", "Alfred", "FRIEDMAN"]
    df = pd.DataFrame({"Name": candidates})
    df["Similarity"] = df["Name"].apply(
        lambda n: round(
            (1 - SequenceMatcher(None, n.upper(), target.upper()).ratio()) * 100
        )
    )
    return df


# 12-16: TRANSLATE (character-by-character replacement)
def example_12_16() -> pd.DataFrame:
    """Translate digits to letters (SAS TRANSLATE)."""
    answers = ["14325", "AB123", "51492"]
    tr = str.maketrans("12345", "ABCDE")
    df = pd.DataFrame({"Answer": answers})
    df["Translated"] = df["Answer"].apply(lambda s: s.translate(tr))
    return df


# 12-17: TRANWRD (word-level replacement)
def example_12_17() -> pd.DataFrame:
    """Replace abbreviations in address (SAS TRANWRD)."""
    records = [
        {"Name": "Dr. Peter Benchley", "Line1": "123 River Road",
         "City": "Oceanside", "State": "NY", "Zip": "11518"},
        {"Name": "Mr. Robert Merrill", "Line1": "878 Ocean Avenue",
         "City": "Long Beach", "State": "CA", "Zip": "90818"},
    ]
    df = pd.DataFrame(records)
    for title in ["Mr.", "Mrs.", "Dr.", "Ms."]:
        df["Name"] = df["Name"].str.replace(title, "", regex=False).str.strip()
    replacements = {"Street": "St.", "Road": "Rd.", "Avenue": "Ave."}
    for old, new in replacements.items():
        df["Line1"] = df["Line1"].str.replace(old, new, regex=False)
    return df


def run_all() -> None:
    datasets = load_all_datasets()
    sales = datasets["sales"]
    address = datasets["address"]

    print_dataset(example_12_1(sales), "12-1: Long Names")
    print_dataset(example_12_2(), "12-2: Case-insensitive Merge")
    print_dataset(example_12_3(address), "12-3: Standardized Addresses")
    print(f"12-4: Concatenation = {example_12_4()}\n")
    print_dataset(example_12_6(), "12-6: Phone Numbers (digits only)")
    print_dataset(example_12_8(), "12-8: Mixed Units Conversion")
    print_dataset(example_12_9(), "12-9: Find Whole Word 'Roger'")
    print_dataset(example_12_12(), "12-12: Extract from Coded ID")
    print_dataset(example_12_13(), "12-13: First and Last Names")
    print_dataset(example_12_15(), "12-15: Fuzzy Match")
    print_dataset(example_12_16(), "12-16: Translate")
    print_dataset(example_12_17(), "12-17: Address Cleanup")


if __name__ == "__main__":
    run_all()
