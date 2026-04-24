"""
Create Datasets — Python equivalent of Create_Datasets.sas

Generates all in-memory DataFrames used across the book's chapters.
External data files are read from the ``Data/`` directory; inline data
is embedded directly (matching SAS ``datalines`` blocks).

Usage
-----
    from python.create_datasets import load_all_datasets
    datasets = load_all_datasets()
    sales = datasets["sales"]
"""
from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from utils.data_helpers import data_dir


def _build_address() -> pd.DataFrame:
    """SAS data set ADDRESS — multi-line address records."""
    records = [
        {"Name": "ron   coDY", "Street": "1178  HIGHWAY 480",
         "City": "camp   verde", "State": "tx", "Zip": "78010"},
        {"Name": "jason Tran", "Street": "123 lake  view drive",
         "City": "East  Rockaway", "State": "ny", "Zip": "11518"},
    ]
    return pd.DataFrame(records)


def _build_chars() -> pd.DataFrame:
    """SAS data set CHARS (chapter 11 version)."""
    return pd.DataFrame({
        "Height": ["58", "63", "45"],
        "Weight": ["155", "200", "79"],
        "Date": ["10/21/1950", "5/6/2005", "11/12/2004"],
    })


def _build_careless() -> pd.DataFrame:
    return pd.DataFrame({
        "Score": [100, 65, 95],
        "Last_Name": ["COdY", "sMITH", "scerbo"],
        "Ans1": ["A", "C", "D"],
        "Ans2": ["b", "C", "e"],
        "Ans3": ["c", "d", "D"],
    })


def _build_cleaning() -> pd.DataFrame:
    return pd.DataFrame({
        "Subject": [1, 2, 3],
        "Letters": ["Apple", "Ice9", "Help!"],
        "Digits": ["12345", "123X", "999"],
        "Both": ["XYZ123", "Abc.123", "X1Y2Z3"],
    })


def _build_oneper() -> pd.DataFrame:
    return pd.DataFrame({
        "Subj": ["001", "002", "003", "004"],
        "Dx1": [450, 250, 410, 240],
        "Dx2": [430, 240, 250, np.nan],
        "Dx3": [410, np.nan, 500, np.nan],
    })


def _build_manyper(oneper: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in oneper.iterrows():
        for v in range(1, 4):
            dx = r[f"Dx{v}"]
            if pd.isna(dx):
                break
            rows.append({"Subj": r["Subj"], "Diagnosis": int(dx), "Visit": v})
    return pd.DataFrame(rows)


def _build_school() -> pd.DataFrame:
    return pd.read_fwf(
        data_dir() / "school.txt",
        colspecs=[(0, 5), (5, 20), (20, 23), (23, 26), (26, 29)],
        names=["StudID", "Name", "Quiz1", "Quiz2", "Quiz3"],
        header=None,
        skiprows=2,
    )


def _build_month_day_year() -> pd.DataFrame:
    return pd.DataFrame({
        "Month": [10, 3, 5],
        "Day": [21.0, np.nan, 7.0],
        "Year": [1950, 2005, 2000],
    })


def _build_sales() -> pd.DataFrame:
    raw = """\
1843,George Smith,North,Barco Corporation,10/10/2006,144L,50,8.99
1843,George Smith,South,Cost Cutter's,10/11/2006,122,100,5.99
1843,George Smith,North,Minimart Inc.,10/11/2006,188S,3,5199
1843,George Smith,North,Barco Corporation,10/15/2006,908X,1,5129
1843,George Smith,South,Ely Corp.,10/15/2006,122L,10,29.95
0177,Glenda Johnson,East,Food Unlimited,9/1/2006,188X,100,6.99
0177,Glenda Johnson,East,Shop and Drop,9/2/2006,144L,100,8.99
1843,George Smith,South,Cost Cutter's,10/18/2006,855W,1,9109
9888,Sharon Lu,West,Cost Cutter's,11/14/2006,122,50,5.99
9888,Sharon Lu,West,Pet's are Us,11/15/2006,100W,1000,1.99
0017,Jason Nguyen,East,Roger's Spirits,11/15/2006,122L,500,39.99
0017,Jason Nguyen,South,Spirited Spirits,12/22/2006,407XX,100,19.95
0177,Glenda Johnson,North,Minimart Inc.,12/21/2006,777,5,10500
0177,Glenda Johnson,East,Barco Corporation,12/20/2006,733,2,10000
1843,George Smith,North,Minimart Inc.,11/19/2006,188S,3,5199"""
    df = pd.read_csv(
        StringIO(raw),
        names=["EmpID", "Name", "Region", "Customer", "Date",
               "Item", "Quantity", "UnitCost"],
    )
    df["EmpID"] = df["EmpID"].astype(str).str.zfill(4)
    df["Date"] = pd.to_datetime(df["Date"])
    df["TotalSales"] = df["Quantity"] * df["UnitCost"]
    return df


def _build_medical() -> pd.DataFrame:
    records = [
        ("001", "Mayo Clinic", "10/21/2006", 120, 78, "7",
         "Patient has had a persistent cough for 3 weeks."),
        ("003", "HMC", "9/1/2006", 166, 58, "8",
         "Patient placed on beta-blockers on 7/1/2006"),
        ("002", "Mayo Clinic", "10/01/2006", 210, 68, "9",
         "Patient has been on antibiotics for 10 days"),
        ("004", "HMC", "11/11/2006", 288, 88, "9",
         "Patient advised to lose some weight"),
        ("007", "Mayo Clinic", "5/1/2006", 180, 54, "7",
         "This patient is always under high stress"),
        ("050", "HMC", "7/6/2006", 199, 60, "123",
         "Refer this patient to mental health for evaluation"),
    ]
    df = pd.DataFrame(records, columns=[
        "Patno", "Clinic", "VisitDate", "Weight", "HR", "DX", "Comment"])
    df["VisitDate"] = pd.to_datetime(df["VisitDate"])
    return df


def _build_bicycles() -> pd.DataFrame:
    raw = """\
USA,Road Bike,Trek,5000,2200
USA,Road Bike,Cannondale,2000,2100
USA,Mountain Bike,Trek,6000,1200
USA,Mountain Bike,Cannondale,4000,2700
USA,Hybrid,Trek,4500,650
France,Road Bike,Trek,3400,2500
France,Road Bike,Cannondale,900,3700
France,Mountain Bike,Trek,5600,1300
France,Mountain Bike,Cannondale,800,1899
France,Hybrid,Trek,1100,540
United Kingdom,Road Bike,Trek,2444,2100
United Kingdom,Road Bike,Cannondale,1200,2123
United Kingdom,Hybrid,Trek,800,490
United Kingdom,Hybrid,Cannondale,500,880
United Kingdom,Mountain Bike,Trek,1211,1121
Italy,Hybrid,Trek,700,690
Italy,Road Bike,Trek,4500,2890
Italy,Mountain Bike,Trek,3400,1877"""
    df = pd.read_csv(
        StringIO(raw),
        names=["Country", "Model", "Manuf", "Units", "UnitCost"],
    )
    df["TotalSales"] = (df["Units"] * df["UnitCost"]) / 1000
    return df


def _build_survey() -> pd.DataFrame:
    df = pd.read_csv(
        data_dir() / "survey.txt",
        sep=r"\s+",
        names=["ID", "Gender", "Age", "Salary",
               "Ques1", "Ques2", "Ques3", "Ques4", "Ques5"],
    )
    df["ID"] = df["ID"].astype(str).str.zfill(3)
    df[["Ques1", "Ques2", "Ques3", "Ques4", "Ques5"]] = (
        df[["Ques1", "Ques2", "Ques3", "Ques4", "Ques5"]].astype(str)
    )
    return df


def _build_clinic() -> pd.DataFrame:
    raw = """\
101,10/21/2005,4,68,120,80
255,9/1/2005,1,76,188,100
255,12/18/2005,1,74,180,95
255,2/1/2006,3,79,210,110
255,4/1/2006,3,72,180,88
101,2/25/2006,2,68,122,84
303,10/10/2006,1,72,138,84
409,9/1/2005,6,88,142,92
409,10/2/2005,1,72,136,90
409,12/15/2006,1,68,130,84
712,4/6/2006,7,58,118,70
712,4/15/2006,7,56,118,72"""
    df = pd.read_csv(
        StringIO(raw),
        names=["ID", "VisitDate", "Dx", "HR", "SBP", "DBP"],
    )
    df["ID"] = df["ID"].astype(str)
    df["Dx"] = df["Dx"].astype(str)
    df["VisitDate"] = pd.to_datetime(df["VisitDate"])
    df = df.sort_values(["ID", "VisitDate"]).reset_index(drop=True)
    return df


def _build_health() -> pd.DataFrame:
    return pd.DataFrame({
        "Subj": ["001", "003", "004", "005"],
        "Height": [68, 74, 63, 60],
        "Weight": [155, 250, 110, 95],
    })


def _build_demographic() -> pd.DataFrame:
    return pd.DataFrame({
        "Subj": ["001", "002", "003", "005"],
        "DOB": pd.to_datetime(["10/15/1960", "8/1/1955",
                               "12/25/1988", "5/28/1949"]),
        "Gender": ["M", "F", "F", "F"],
        "Name": ["Friedman", "Stern", "McGoldrick", "Chien"],
    })


def _build_new_members() -> pd.DataFrame:
    return pd.DataFrame({
        "Subj": ["010", "013"],
        "Gender": ["F", "M"],
        "Name": ["Ostermeier", "Brown"],
        "DOB": pd.to_datetime(["3/5/1977", "6/7/1999"]),
    })


def _build_test_scores() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["1", "2", "3"],
        "Score1": [90, 78, 88],
        "Score2": [95, 77, 91],
        "Score3": [98, 99, 92],
        "Name": ["Jan", "Preston", "Russell"],
    })


def _build_blood() -> pd.DataFrame:
    """Read the blood.txt data file."""
    df = pd.read_csv(
        data_dir() / "blood.txt",
        sep=r"\s+",
        names=["Subject", "Gender", "BloodType", "AgeGroup",
               "WBC", "RBC", "Chol"],
        na_values=["."],
    )
    return df


def _build_insurance() -> pd.DataFrame:
    return pd.DataFrame({
        "Subj": ["001", "002", "003", "005"],
        "Name": ["Fridman", "Stern", "McGoldrich", "Chen"],
    })


def _build_inventory() -> pd.DataFrame:
    return pd.DataFrame({
        "ItemCode": ["150", "175", "200", "204", "208"],
        "Description": ["50 foot hose", "75 foot hose",
                        "greeting card", "25 lb. grass seed",
                        "40 lb. fertilizer"],
        "Price": [19.95, 29.95, 1.99, 18.88, 17.98],
    })


def _build_purchase() -> pd.DataFrame:
    return pd.DataFrame({
        "ItemCode": ["175", "204", "208"],
        "Price": [25.11, 17.87, np.nan],
    })


def _build_spss() -> pd.DataFrame:
    return pd.DataFrame({
        "Height": [58, 63, 999, 61],
        "Weight": [155, 200, 150, 999],
        "Age": [40, 55, 999, 32],
    })


def _build_expose() -> pd.DataFrame:
    return pd.DataFrame({
        "Year": [1944, 1945, 1946, 1947, 1948, 1949],
        "JobCode": ["A", "B", "C", "D", "E", "A"],
    })


def _build_mixed() -> pd.DataFrame:
    return pd.DataFrame({
        "Name": ["ron cody", "ALAN WILSON", "Jason Tran"],
    })


def _build_upper() -> pd.DataFrame:
    return pd.DataFrame({
        "Name": ["ALAN WILSON", "JASON TRAN", "RON CODY"],
    })


def _build_mixed_units() -> pd.DataFrame:
    return pd.DataFrame({
        "Name": ["Ron", "Jan", "Peter"],
        "Weight": ["180lbs", "95Kg", "210 lb"],
        "Height": ["72in", "168cm", "74 In"],
    })


def _build_phone() -> pd.DataFrame:
    return pd.DataFrame({
        "Phone": ["(908)235-4490", "800.555.1234",
                  "908 456-1111", "(210) 444.5050"],
    })


def _build_names_and_more() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": ["001", "002", "003"],
        "Name": ["Jeffrey Smith", "Ron Cody", "Alan Wilson"],
        "Weight": [200, 180, 150],
    })


def _build_stocks() -> pd.DataFrame:
    raw = """\
01/03/2006,50.25
01/10/2006,52.50
01/17/2006,49.25
01/24/2006,53.00
01/31/2006,55.00
02/07/2006,54.25
02/14/2006,58.00
02/21/2006,62.00"""
    df = pd.read_csv(
        StringIO(raw), names=["Date", "Price"],
    )
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def _build_numeric() -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.to_datetime(["10/21/1950", "5/6/2005", "11/12/2004"]),
        "Age": [58, 63, 45],
        "Cost": [155.50, 200.75, 79.25],
    })


def _build_codes() -> pd.DataFrame:
    return pd.DataFrame({
        "ICD10": ["020", "022", "390", "410", "493", "540"],
        "Description": ["Plague", "Anthrax", "Rheumatic fever",
                        "Myocardial infarction", "Asthma", "Appendicitis"],
    })


def _build_personal() -> pd.DataFrame:
    return pd.DataFrame({
        "ID": [1, 2, 3, 4, 5, 6, 7, 8],
        "Age": [23, 55, 38, 67, 22, 63, 45, 32],
        "Weight": [155, 200, 120, 180, 140, 160, 175, 145],
        "Height": [68, 72, 63, 70, 65, 71, 67, 69],
    })


def _build_grouping() -> pd.DataFrame:
    return pd.DataFrame({
        "X": [1, 2, 3, 4, 5, np.nan, 7, 3, 2, 5],
    })


def _build_missing() -> pd.DataFrame:
    return pd.DataFrame({
        "A": ["X", "Y", np.nan, "X"],
        "B": ["1", "2", "1", np.nan],
    })


def load_all_datasets() -> dict[str, pd.DataFrame]:
    """Return a dictionary of all named datasets used in the book."""
    oneper = _build_oneper()
    datasets: dict[str, pd.DataFrame] = {
        "address": _build_address(),
        "chars": _build_chars(),
        "careless": _build_careless(),
        "cleaning": _build_cleaning(),
        "oneper": oneper,
        "manyper": _build_manyper(oneper),
        "school": _build_school(),
        "month_day_year": _build_month_day_year(),
        "sales": _build_sales(),
        "medical": _build_medical(),
        "bicycles": _build_bicycles(),
        "survey": _build_survey(),
        "clinic": _build_clinic(),
        "health": _build_health(),
        "demographic": _build_demographic(),
        "new_members": _build_new_members(),
        "test_scores": _build_test_scores(),
        "blood": _build_blood(),
        "insurance": _build_insurance(),
        "inventory": _build_inventory(),
        "purchase": _build_purchase(),
        "spss": _build_spss(),
        "expose": _build_expose(),
        "mixed": _build_mixed(),
        "upper": _build_upper(),
        "mixed_units": _build_mixed_units(),
        "phone": _build_phone(),
        "names_and_more": _build_names_and_more(),
        "stocks": _build_stocks(),
        "numeric": _build_numeric(),
        "codes": _build_codes(),
        "personal": _build_personal(),
        "grouping": _build_grouping(),
        "missing": _build_missing(),
    }
    return datasets


if __name__ == "__main__":
    ds = load_all_datasets()
    for name, df in ds.items():
        print(f"--- {name} ({len(df)} rows) ---")
        print(df.head(), "\n")
