"""Recreate all ~50 datasets from Create_Datasets.sas using the Python utility layer.

Each ``create_*`` function returns a DataFrame and also persists it via
``save_dataset``.  Running this module as a script builds every dataset.
"""

import os
import sys
import math
from typing import Optional

import numpy as np
import pandas as pd

# Ensure the package is importable when running as a script
sys.path.insert(0, os.path.dirname(__file__))

from utils.io_helpers import (
    DATASETS_DIR,
    save_dataset,
    read_fwf_sas,
    read_datalines,
    read_sas_list_input,
    parse_sas_date,
)

# Path to the companion Data/ directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")

_SAS_EPOCH = pd.Timestamp("1960-01-01")


def _sas_date(date_str: str) -> int:
    """Convert a SAS date literal string like '01Jan2002' to a SAS date number."""
    from datetime import datetime, date as _date
    epoch = _date(1960, 1, 1)
    s = date_str.strip().strip("'\"").rstrip("d").rstrip("D")
    dt = datetime.strptime(s, "%d%b%Y")
    return (dt.date() - epoch).days


# ===================================================================
# Dataset creation functions
# ===================================================================

def create_address() -> pd.DataFrame:
    data = """\
ron   coDY
1178  HIGHWAY 480
camp   verde        tx 78010
jason Tran
123 lake  view drive
East  Rockaway      ny 11518"""
    lines = data.strip().split("\n")
    rows = []
    i = 0
    while i + 2 < len(lines):
        name = lines[i].strip()[:40]
        street = lines[i + 1].strip()[:40]
        city_line = lines[i + 2]
        city = city_line[0:20].strip()
        state = city_line[20:22].strip()
        zipcode = city_line[23:28].strip()
        rows.append({"Name": name, "Street": street, "City": city,
                      "State": state, "Zip": zipcode})
        i += 3
    df = pd.DataFrame(rows)
    save_dataset(df, "address")
    return df


def create_chars() -> pd.DataFrame:
    data = """\
58 155 10/21/1950
63 200 5/6/2005
45 79 11/12/2004"""
    df = read_datalines(data, [("Height", "$"), ("Weight", "$"), ("Date", "$")])
    save_dataset(df, "chars")
    return df


def create_careless() -> pd.DataFrame:
    data = """\
100 COdY Abc
65 sMITH CCd
95 scerbo DeD"""
    rows = []
    for line in data.strip().split("\n"):
        parts = line.split()
        score = int(parts[0])
        last = parts[1]
        ans_str = parts[2]
        row = {"Score": score, "Last_Name": last,
               "Ans1": ans_str[0], "Ans2": ans_str[1], "Ans3": ans_str[2]}
        rows.append(row)
    df = pd.DataFrame(rows)
    save_dataset(df, "careless")
    return df


def create_cleaning() -> pd.DataFrame:
    data = """\
Apple 12345 XYZ123
Ice9 123X Abc.123
Help! 999 X1Y2Z3"""
    rows = []
    subj = 0
    for line in data.strip().split("\n"):
        subj += 1
        parts = line.split()
        rows.append({"Subject": subj, "Letters": parts[0],
                      "Digits": parts[1], "Both": parts[2]})
    df = pd.DataFrame(rows)
    save_dataset(df, "cleaning")
    return df


def create_oneper() -> pd.DataFrame:
    data = """\
001     450    430    410
002     250    240      .
003     410    250    500
004     240      .      ."""
    df = read_datalines(data, ["Subj", "Dx1", "Dx2", "Dx3"])
    # Subj is character
    df["Subj"] = df["Subj"].astype(str)
    save_dataset(df, "oneper")
    return df


def create_manyper() -> pd.DataFrame:
    oneper = create_oneper()
    rows = []
    for _, row in oneper.iterrows():
        for visit in range(1, 4):
            dx_val = row[f"Dx{visit}"]
            if pd.isna(dx_val):
                break
            rows.append({"Subj": row["Subj"], "Diagnosis": dx_val,
                          "Visit": visit})
    df = pd.DataFrame(rows)
    save_dataset(df, "manyper")
    return df


def create_school() -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, "school.txt")
    if os.path.exists(filepath):
        colspecs = [(0, 5), (5, 20), (20, 23), (23, 26), (26, 29)]
        names = ["StudID", "Name", "Quiz1", "Quiz2", "Quiz3"]
        df = read_fwf_sas(filepath, colspecs, names, firstobs=3, truncover=True)
        for col in ["Quiz1", "Quiz2", "Quiz3"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["StudID"] = df["StudID"].astype(str)
        save_dataset(df, "school")
        return df
    return pd.DataFrame()


def create_month_day_year() -> pd.DataFrame:
    data = """\
10 21 1950
3 . 2005
5 7 2000"""
    df = read_datalines(data, ["Month", "Day", "Year"])
    save_dataset(df, "month_day_year")
    return df


def create_sales() -> pd.DataFrame:
    # Pre-parsed from SAS datalines with & modifier fields
    raw_rows = [
        ("1843", "George Smith", "North", "Barco Corporation", "144L", 50, 8.99),
        ("1843", "George Smith", "South", "Cost Cutter's", "122", 100, 5.99),
        ("1843", "George Smith", "North", "Minimart Inc.", "188S", 3, 5199.0),
        ("1843", "George Smith", "North", "Barco Corporation", "908X", 1, 5129.0),
        ("1843", "George Smith", "South", "Ely Corp.", "122L", 10, 29.95),
        ("0177", "Glenda Johnson", "East", "Food Unlimited", "188X", 100, 6.99),
        ("0177", "Glenda Johnson", "East", "Shop and Drop", "144L", 100, 8.99),
        ("1843", "George Smith", "South", "Cost Cutter's", "855W", 1, 9109.0),
        ("9888", "Sharon Lu", "West", "Cost Cutter's", "122", 50, 5.99),
        ("9888", "Sharon Lu", "West", "Pet's are Us", "100W", 1000, 1.99),
        ("0017", "Jason Nguyen", "East", "Roger's Spirits", "122L", 500, 39.99),
        ("0017", "Jason Nguyen", "South", "Spirited Spirits", "407XX", 100, 19.95),
        ("0177", "Glenda Johnson", "North", "Minimart Inc.", "777", 5, 10.500),
        ("0177", "Glenda Johnson", "East", "Barco Corporation", "733", 2, 10000.0),
        ("1843", "George Smith", "North", "Minimart Inc.", "188S", 3, 5199.0),
    ]
    rows = []
    for empid, name, region, customer, item, qty, uc in raw_rows:
        rows.append({
            "EmpID": empid, "Name": name, "Region": region,
            "Customer": customer, "Item": item,
            "Quantity": qty, "UnitCost": uc,
            "TotalSales": qty * uc,
        })
    df = pd.DataFrame(rows)
    save_dataset(df, "sales")
    return df


def create_medical() -> pd.DataFrame:
    # Pre-parsed from SAS datalines with & modifier fields
    raw_rows = [
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
    rows = []
    for patno, clinic, vdate, weight, hr, dx, comment in raw_rows:
        d = parse_sas_date(vdate, "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({
            "Patno": patno, "Clinic": clinic, "VisitDate": sas_date,
            "Weight": weight, "HR": hr, "DX": dx, "Comment": comment,
        })
    df = pd.DataFrame(rows)
    save_dataset(df, "medical")
    return df


def create_bicycles() -> pd.DataFrame:
    data = """\
USA  Road Bike  Trek 5000 $2,200
USA  Road Bike  Cannondale 2000 $2,100
USA  Mountain Bike  Trek 6000 $1,200
USA  Mountain Bike  Cannondale 4000 $2,700
USA  Hybrid  Trek 4500 $650
France  Road Bike  Trek 3400 $2,500
France  Road Bike  Cannondale 900 $3,700
France  Mountain Bike  Trek 5600 $1,300
France  Mountain Bike  Cannondale  800 $1,899
France  Hybrid  Trek 1100 $540
United Kingdom  Road Bike  Trek 2444 $2,100
United Kingdom  Road Bike  Cannondale  1200 $2,123
United Kingdom  Hybrid  Trek 800 $490
United Kingdom  Hybrid  Cannondale 500 $880
United Kingdom  Mountain Bike  Trek 1211 $1,121
Italy  Hybrid  Trek 700 $690
Italy  Road Bike  Trek 4500  $2,890
Italy  Mountain Bike  Trek 3400  $1,877"""
    import re as _re
    rows = []
    for line in data.strip().split("\n"):
        parts = _re.split(r"  +", line.strip())
        country = parts[0].strip()
        model = parts[1].strip()
        rest_str = " ".join(parts[2:])
        tokens = rest_str.split()
        manuf = tokens[0]
        units = int(tokens[1])
        unitcost = float(tokens[2].replace("$", "").replace(",", ""))
        total_sales = (units * unitcost) / 1000
        rows.append({
            "Country": country, "Model": model, "Manuf": manuf,
            "Units": units, "UnitCost": unitcost,
            "TotalSales": round(total_sales, 2),
        })
    df = pd.DataFrame(rows)
    save_dataset(df, "bicycles")
    return df


def create_assign() -> pd.DataFrame:
    """Recreates ASSIGN dataset using PROC RANK groups=3."""
    rng = np.random.RandomState(1357)
    subjects = list(range(1, 37))
    group_vals = [rng.random() for _ in subjects]
    temp = pd.DataFrame({"Subject": subjects, "Group": group_vals})
    # PROC RANK groups=3
    temp["Group"] = pd.qcut(temp["Group"], 3, labels=False)
    df = temp[["Subject", "Group"]].copy()
    save_dataset(df, "assign")
    return df


def create_survey() -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, "survey.txt")
    if os.path.exists(filepath):
        names = ["ID", "Gender", "Age", "Salary", "Ques1", "Ques2",
                 "Ques3", "Ques4", "Ques5"]
        df = read_sas_list_input(filepath, names, pad=True)
        df["ID"] = df["ID"].apply(lambda x: str(int(x)).zfill(3) if pd.notna(x) else "")
        df["Gender"] = df["Gender"].astype(str)
        for q in ["Ques1", "Ques2", "Ques3", "Ques4", "Ques5"]:
            df[q] = df[q].apply(lambda x: str(int(x)) if pd.notna(x) else "")
        save_dataset(df, "survey")
        return df
    return pd.DataFrame()


def create_clinic() -> pd.DataFrame:
    data = """\
101 10/21/2005 4 68 120 80
255 9/1/2005 1 76 188 100
255 12/18/2005 1 74 180 95
255 2/1/2006 3 79 210 110
255 4/1/2006 3 72 180 88
101 2/25/2006 2 68 122 84
303 10/10/2006 1 72 138 84
409 9/1/2005 6 88 142 92
409 10/2/2005 1 72 136 90
409 12/15/2006 1 68 130 84
712 4/6/2006 7 58 118 70
712 4/15/2006 7 56 118 72"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[1], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({
            "ID": tokens[0], "VisitDate": sas_date, "Dx": tokens[2],
            "HR": int(tokens[3]), "SBP": int(tokens[4]), "DBP": int(tokens[5]),
        })
    df = pd.DataFrame(rows)
    df.sort_values(["ID", "VisitDate"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    save_dataset(df, "clinic")
    return df


def create_hosp() -> pd.DataFrame:
    """Recreate HOSP dataset (random data with SAS-style RNG)."""
    from datetime import date as _date, timedelta
    epoch = _date(1960, 1, 1)
    rng1 = np.random.RandomState(1234)
    rng0 = np.random.RandomState(0)

    rows = []
    subject = 0
    for j in range(1, 1001):
        admit_date = int(rng1.random() * 1200 + 15500)
        # intck('qtr', '01jan2002'd, AdmitDate)
        jan2002 = _sas_date("01Jan2002")
        d_admit = epoch + timedelta(days=admit_date)
        d_jan = epoch + timedelta(days=jan2002)
        quarter = (d_admit.year * 4 + (d_admit.month - 1) // 3) - \
                  (d_jan.year * 4 + (d_jan.month - 1) // 3)

        for i in range(1, quarter + 1):
            if rng0.random() < 0.1:
                wd = (d_admit.weekday() + 2) % 7 or 7  # Sunday=1
                if wd == 1:
                    admit_date += 1
                    d_admit = epoch + timedelta(days=admit_date)
            if rng0.random() < 0.1:
                wd = (d_admit.weekday() + 2) % 7 or 7
                if wd == 7:
                    admit_date -= int(3 * rng0.random() + 1)
                    d_admit = epoch + timedelta(days=admit_date)
            dob = int(25000 * rng0.random() + _sas_date("01Jan1920"))
            dischr_date = admit_date + abs(int(10 * rng0.randn() + 1))
            subject += 1
            rows.append({
                "AdmitDate": admit_date, "DOB": dob,
                "DischrDate": dischr_date, "Subject": subject,
            })
    df = pd.DataFrame(rows)
    save_dataset(df, "hosp")
    return df


def create_hosp_discharge() -> pd.DataFrame:
    """Recreate Hosp_Discharge from Hosp."""
    hosp = create_hosp()
    jan2003 = _sas_date("01Jan2003")
    dec2003 = _sas_date("31Dec2003")
    subset = hosp[(hosp["DischrDate"] >= jan2003) & (hosp["DischrDate"] <= dec2003)].copy()
    subset = subset.iloc[207:217]  # firstobs=208, obs=217 (0-indexed: 207:217)
    df = subset[["Subject", "DischrDate"]].copy()
    df.columns = ["Patient", "Discharge"]
    df.reset_index(drop=True, inplace=True)
    save_dataset(df, "hosp_discharge")
    return df


def create_health() -> pd.DataFrame:
    data = """\
001 68 155
003 74 250
004 63 110
005 60 95"""
    df = read_datalines(data, [("Subj", "$"), ("Height", None), ("Weight", None)])
    save_dataset(df, "health")
    return df


def create_demographic() -> pd.DataFrame:
    data = """\
001 10/15/1960 M Friedman
002 8/1/1955 M Stern
003 12/25/1988 F McGoldrick
005 5/28/1949 F Chien"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[1], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"Subj": tokens[0], "DOB": sas_date,
                      "Gender": tokens[2], "Name": tokens[3]})
    df = pd.DataFrame(rows)
    save_dataset(df, "demographic")
    return df


def create_new_members() -> pd.DataFrame:
    data = """\
010 F Ostermeier 3/5/1977
013 M Brown 6/7/1999"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[3], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"Subj": tokens[0], "Gender": tokens[1],
                      "Name": tokens[2], "DOB": sas_date})
    df = pd.DataFrame(rows)
    save_dataset(df, "new_members")
    return df


def create_one_two_three() -> tuple:
    """Temporary datasets ONE, TWO, THREE from chapter 10."""
    one_data = """\
7 Adams 210
1 Smith 190
2 Schneider 110
4 Gregory 90"""
    two_data = """\
9 Shea 120
3 O'Brien 180
5 Bessler 207"""
    three_data = """\
10 M Horvath
15 F Stevens
20 M Brown"""
    one = read_datalines(one_data, [("ID", "$"), ("Name", "$"), ("Weight", None)])
    two = read_datalines(two_data, [("ID", "$"), ("Name", "$"), ("Weight", None)])
    three = read_datalines(three_data, [("ID", "$"), ("Gender", "$"), ("Name", "$")])
    save_dataset(one, "one")
    save_dataset(two, "two")
    save_dataset(three, "three")
    return one, two, three


def create_employee_hours() -> tuple:
    """Temporary datasets EMPLOYEE and HOURS from chapter 10."""
    emp_data = """\
7 Adams
1 Smith
2 Schneider
4 Gregory
5 Washington"""
    hrs_data = """\
1 A 39
4 B 44
9 B 57
5 A 35"""
    emp = read_datalines(emp_data, [("ID", "$"), ("Name", "$")])
    hrs = read_datalines(hrs_data, [("ID", "$"), ("JobClass", "$"), ("Hours", None)])
    save_dataset(emp, "employee_ch10")
    save_dataset(hrs, "hours")
    return emp, hrs


def create_bert_ernie() -> tuple:
    bert_data = "123 90\n222 95\n333 100"
    ernie_data = "123 200\n222 205\n333 317"
    bert = read_datalines(bert_data, [("ID", "$"), ("X", None)])
    ernie = read_datalines(ernie_data, [("EmpNo", "$"), ("Y", None)])
    save_dataset(bert, "bert")
    save_dataset(ernie, "ernie")
    return bert, ernie


def create_divisions() -> tuple:
    d1_data = """\
111223333 11/14/1956 M
123456789 5/17/1946 F
987654321 4/1/1977 F"""
    d2_data = """\
111-22-3333 A10 $45,123
123-45-6789 B5 $35,400
987-65-4321 A20 $87,900"""
    rows1 = []
    for line in d1_data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[1], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows1.append({"SS": int(tokens[0]), "DOB": sas_date, "Gender": tokens[2]})
    div1 = pd.DataFrame(rows1)

    rows2 = []
    for line in d2_data.strip().split("\n"):
        tokens = line.split()
        salary = float(tokens[2].replace("$", "").replace(",", ""))
        rows2.append({"SS": tokens[0], "JobCode": tokens[1], "Salary": salary})
    div2 = pd.DataFrame(rows2)

    save_dataset(div1, "division1")
    save_dataset(div2, "division2")
    return div1, div2


def create_oscar() -> pd.DataFrame:
    data = "123 200\n123 250\n222 205\n333 317\n333 400\n333 500"
    df = read_datalines(data, [("ID", "$"), ("Y", None)])
    save_dataset(df, "oscar")
    return df


def create_prices_new() -> tuple:
    # Pre-parsed: SAS uses & modifier for Description field
    raw_prices = [
        ("150", "50 foot hose", 19.95),
        ("175", "75 foot hose", 29.95),
        ("200", "greeting card", 1.99),
        ("204", "25 lb. grass seed", 18.88),
        ("208", "40 lb. fertilizer", 17.98),
    ]
    prices = pd.DataFrame(raw_prices, columns=["ItemCode", "Description", "Price"])

    new_data = "204 17.87\n175 25.11\n208 ."
    new_df = read_datalines(new_data, [("ItemCode", "$"), ("Price", None)])
    save_dataset(prices, "prices")
    save_dataset(new_df, "new15dec2017")
    return prices, new_df


def create_insurance() -> pd.DataFrame:
    data = "Fridman F\nGoldman P\nChein F\nStern P"
    df = read_datalines(data, [("Name", "$"), ("Type", "$")])
    save_dataset(df, "insurance")
    return df


def create_new_members_order() -> pd.DataFrame:
    data = """\
Ostermeier 3/5/1977 F 010
Brown 6/7/1999 M 013"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[1], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"Name": tokens[0], "DOB": sas_date,
                      "Gender": tokens[2], "Subj": tokens[3]})
    df = pd.DataFrame(rows)
    save_dataset(df, "new_members_order")
    return df


def create_inventory() -> pd.DataFrame:
    data = "M567 23.50\nS888 12.99\nL776 159.98\nX999 29.95\nM123 4.59\nS776 1.99"
    df = read_datalines(data, [("Model", "$"), ("Price", None)])
    save_dataset(df, "inventory")
    return df


def create_purchase() -> pd.DataFrame:
    data = "101 L776 1\n102 M123 10\n103 X999 2\n103 M567 1"
    df = read_datalines(data, [("CustNumber", None), ("Model", "$"), ("Quantity", None)])
    save_dataset(df, "purchase")
    return df


def create_newproducts() -> pd.DataFrame:
    data = "L939 10.99\nM135 .75"
    df = read_datalines(data, [("Model", "$"), ("Price", None)])
    save_dataset(df, "newproducts")
    return df


def create_demographic_id() -> pd.DataFrame:
    data = """\
001 10/10/37 M
002 7/12/87 F
004 1/5/2000 M
005 6/4/1966 F"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[1], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"ID": tokens[0], "DOB": sas_date, "Gender": tokens[2]})
    df = pd.DataFrame(rows)
    save_dataset(df, "demographic_id")
    return df


def create_survey1() -> pd.DataFrame:
    data = """\
001 13542
002 55443
003 21211
004 35142
005 33333"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        subj = tokens[0]
        qs = tokens[1]
        row = {"Subj": subj}
        for i in range(5):
            row[f"Q{i+1}"] = qs[i]
        rows.append(row)
    df = pd.DataFrame(rows)
    save_dataset(df, "survey1")
    return df


def create_survey2() -> pd.DataFrame:
    data = """\
001 13542
002 55443
003 21211
004 35142
005 54545"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        sid = int(tokens[0])
        qs = tokens[1]
        row = {"ID": sid}
        for i in range(5):
            row[f"Q{i+1}"] = int(qs[i])
        rows.append(row)
    df = pd.DataFrame(rows)
    save_dataset(df, "survey2")
    return df


def create_test_scores() -> pd.DataFrame:
    data = "1 90 95 98\n2 78 77 75\n3 88 91 92"
    df = read_datalines(data, [("ID", "$"), ("Score1", None), ("Score2", None), ("Score3", None)])
    save_dataset(df, "test_scores")
    return df


def create_upper() -> pd.DataFrame:
    data = """\
DANIEL FIELDS  01/03/1966
PATRICE HELMS  05/23/1988
THOMAS CHIEN  11/12/2000"""
    import re as _re
    rows = []
    for line in data.strip().split("\n"):
        parts = _re.split(r"  +", line.strip())
        name = parts[0].strip()
        d = parse_sas_date(parts[1].strip(), "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"Name": name, "DOB": sas_date})
    df = pd.DataFrame(rows)
    save_dataset(df, "upper")
    return df


def create_psych() -> pd.DataFrame:
    data = """\
001 1 3 2 4 5 4 3 4 5 4 90 92 93 90 88
002 3 3 . . 3 4 5 5 1 . 95 . . 86 85
003 . . . . 5 5 4 4 3 3 88 87 86 85 84
004 5 3 4 5 . 5 4 3 3 . 78 78 82 84 .
005 5 4 3 2 1 1 2 3 4 5 92 93 94 95 99"""
    specs = [("ID", "$")] + [(f"Ques{i}", None) for i in range(1, 11)] + \
            [(f"Score{i}", None) for i in range(1, 6)]
    df = read_datalines(data, specs)
    save_dataset(df, "psych")
    return df


def create_char_num() -> pd.DataFrame:
    data = """\
23 155 132423222 08822
56 220 123457777 90210
74 95  012003004 78010"""
    df = read_datalines(data, [("Age", "$"), ("Weight", "$"), ("SS", None), ("Zip", None)])
    save_dataset(df, "char_num")
    return df


def create_stocks() -> pd.DataFrame:
    jan1 = _sas_date("01Jan2017")
    jan31 = _sas_date("31Jan2017")
    prices = [34, 35, 39, 30, 35, 35, 37, 38, 39, 45, 47, 52,
              39, 40, 51, 52, 45, 47, 48, 50, 50, 51, 52, 53,
              55, 42, 41, 40, 46, 55, 52]
    rows = []
    for i, d in enumerate(range(jan1, jan31 + 1)):
        if i < len(prices):
            rows.append({"Date": d, "Price": prices[i]})
    df = pd.DataFrame(rows)
    save_dataset(df, "stocks")
    return df


def create_names_and_more() -> pd.DataFrame:
    data = """\
Roger   Cody        (908)782-1234  5ft. 10in.  50 1/8
Thomas  Jefferson   (315) 848-8484  6ft. 1in.  23 1/2
Marco Polo          (800)123-4567  5Ft. 6in.  40
Brian Watson        (518)355-1766  5ft. 10in  89 3/4
Michael DeMarco     (445)232-2233  6ft.       76 1/3"""
    import re as _re
    rows = []
    for line in data.strip().split("\n"):
        parts = _re.split(r"  +", line.strip())
        name = parts[0].strip()
        phone = parts[1].strip() if len(parts) > 1 else ""
        height = parts[2].strip() if len(parts) > 2 else ""
        mixed = parts[3].strip() if len(parts) > 3 else ""
        rows.append({"Name": name, "Phone": phone, "Height": height, "Mixed": mixed})
    df = pd.DataFrame(rows)
    save_dataset(df, "names_and_more")
    return df


def create_phone() -> pd.DataFrame:
    data = """\
(908)232-4856
210.343.4757
(516)  343 - 9293
9342342345"""
    rows = [{"Phone": line.strip()} for line in data.strip().split("\n")]
    df = pd.DataFrame(rows)
    save_dataset(df, "phone")
    return df


def create_study() -> pd.DataFrame:
    data = """\
001 A Low 220lbs. 2
002 A High 90Kg.  1
003 B Low 88kg    1
004 B High 165lbs. 2
005 A Low 88kG 1"""
    df = read_datalines(data, [("Subj", "$"), ("Group", "$"), ("Dose", "$"),
                                ("Weight", "$"), ("Subgroup", None)])
    save_dataset(df, "study")
    return df


def create_errors() -> pd.DataFrame:
    data = """\
001 L1232 Nichole Brown
0a2 L887X Fred Beans
003 12321 Alfred 2 Nice
004 abcde Mary Bumpers
X89 8888S Gill Sandford"""
    import re as _re
    rows = []
    for line in data.strip().split("\n"):
        parts = _re.split(r"  +", line.strip())
        if len(parts) >= 3:
            tokens = parts[0].split()
            subj = tokens[0]
            partnum = tokens[1] if len(tokens) > 1 else parts[1]
            name = parts[1] if len(tokens) > 1 else parts[2]
            if len(tokens) <= 1:
                name = " ".join(parts[2:]) if len(parts) > 2 else parts[1]
        # Simpler approach: first two tokens, rest is name
        tokens = line.strip().split(None, 2)
        subj = tokens[0]
        partnum = tokens[1]
        name = tokens[2] if len(tokens) > 2 else ""
        rows.append({"Subj": subj, "PartNumber": partnum, "Name": name})
    df = pd.DataFrame(rows)
    save_dataset(df, "errors")
    return df


def create_expose() -> pd.DataFrame:
    data = """\
001      1944     B
002      1948     E
003      1947     C
005      1945     A
006      1948     D"""
    df = read_datalines(data, [("Worker", "$"), ("Year", None), ("JobCode", "$")])
    save_dataset(df, "expose")
    return df


def create_mixed() -> pd.DataFrame:
    data = """\
Daniel Fields  123
Patrice Helms  233
Thomas chien  998"""
    import re as _re
    rows = []
    for line in data.strip().split("\n"):
        parts = _re.split(r"  +", line.strip())
        name = parts[0].strip()
        sid = int(parts[1].strip())
        rows.append({"Name": name, "ID": sid})
    df = pd.DataFrame(rows)
    save_dataset(df, "mixed")
    return df


def create_mixed_units() -> pd.DataFrame:
    data = """\
100Kgs. 59in
180lbs 60inches
88kg 150cm.
50KGS 160CM"""
    df = read_datalines(data, [("Weight", "$"), ("Height", "$")])
    save_dataset(df, "mixed_units")
    return df


def create_social() -> pd.DataFrame:
    s1_data = "123-45-6789\n001-34-9876\n007-77-6767\n102-43-9182"
    s2_data = "123-45-6789\n001-43-9876\n007-77-6767\n485-46-1182\n102-43-9188"
    social1 = pd.DataFrame({"SS1": s1_data.strip().split("\n")})
    social2 = pd.DataFrame({"SS2": s2_data.strip().split("\n")})
    # Cross join (PROC SQL implicit join)
    social1["_key"] = 1
    social2["_key"] = 1
    df = social1.merge(social2, on="_key").drop("_key", axis=1)
    save_dataset(df, "social")
    return df


def create_spss() -> pd.DataFrame:
    data = """\
68 178 55 68 210 Smith
999 200 999 999 290 Orlando
72 999 29 79 999 Ramos"""
    df = read_datalines(data, [("Height", None), ("Weight", None), ("Age", None),
                                ("HR", None), ("Chol", None), ("Name", "$")])
    save_dataset(df, "spss")
    return df


def create_personal() -> pd.DataFrame:
    data = """\
123-45-6789 M 0192M 11/15/1949
Eggs Pancakes Sausage Toast Milk Coffee Beef Chicken
013-54-9388 F 9981S 1/2/1981
Pancakes Milk Chicken
112-11-1309 M 1322M 03/29/1988
Beef Toast Eggs Coffee
778-44-4655 F 9899M 7/4/1981
Pancakes Sausauge Coffee Beef
445-45-4455 M 2938S 8/9/1977
Tea Toast"""
    lines = data.strip().split("\n")
    rows = []
    i = 0
    while i < len(lines):
        line1 = lines[i].split()
        ss = line1[0]
        gender = line1[1]
        acctnum = line1[2]
        d = parse_sas_date(line1[3], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        foods = [""] * 8
        i += 1
        if i < len(lines):
            food_tokens = lines[i].split()
            for j, f in enumerate(food_tokens[:8]):
                foods[j] = f
            i += 1
        row = {"SS": ss, "Gender": gender, "AcctNum": acctnum, "DOB": sas_date}
        for j in range(8):
            row[f"Food{j+1}"] = foods[j]
        rows.append(row)
    df = pd.DataFrame(rows)
    save_dataset(df, "personal")
    return df


def create_nines() -> pd.DataFrame:
    data = """\
1 2 3 a b c 99 88 77 66 55
2 999 999 d c e 999 7 999
10 20 999 b b b 999 999 999 33 44"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        row = {}
        row["x"] = float(tokens[0]) if len(tokens) > 0 else np.nan
        row["y"] = float(tokens[1]) if len(tokens) > 1 else np.nan
        row["z"] = float(tokens[2]) if len(tokens) > 2 else np.nan
        row["Char1"] = tokens[3] if len(tokens) > 3 else ""
        row["Char2"] = tokens[4] if len(tokens) > 4 else ""
        row["Char3"] = tokens[5] if len(tokens) > 5 else ""
        for j in range(5):
            val = tokens[6 + j] if 6 + j < len(tokens) else ""
            if val == "":
                row[f"a{j+1}"] = np.nan
            else:
                try:
                    row[f"a{j+1}"] = float(val)
                except ValueError:
                    row[f"a{j+1}"] = np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    save_dataset(df, "nines")
    return df


def create_blood() -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, "blood.txt")
    if os.path.exists(filepath):
        names = ["Subject", "Gender", "BloodType", "AgeGroup", "WBC", "RBC", "Chol"]
        df = read_sas_list_input(filepath, names, truncover=True)
        df["Gender"] = df["Gender"].astype(str)
        df["BloodType"] = df["BloodType"].astype(str)
        df["AgeGroup"] = df["AgeGroup"].astype(str)
        save_dataset(df, "blood")
        return df
    return pd.DataFrame()


def create_bloodpressure() -> pd.DataFrame:
    data = """\
M 23 144 90
F 68 110 62
M 55 130 80
F 28 120 70
M 35 142 82
M 45 150 96
F 48 138 88
F 78 132 76"""
    df = read_datalines(data, [("Gender", "$"), ("Age", None), ("SBP", None), ("DBP", None)])
    save_dataset(df, "bloodpressure")
    return df


def create_numeric() -> pd.DataFrame:
    data = """\
10/15/2000 23 12345
11/12/1923 55 39393"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        d = parse_sas_date(tokens[0], "mmddyy10.")
        sas_date = (d - pd.Timestamp("1960-01-01").date()).days if d else np.nan
        rows.append({"Date": sas_date, "Age": int(tokens[1]), "Cost": int(tokens[2])})
    df = pd.DataFrame(rows)
    save_dataset(df, "numeric")
    return df


def create_codes() -> pd.DataFrame:
    data = """\
020 Plague
022 Anthrax
390 Rheumatic fever
410 Myocardial infarction
493 Asthma
540 Appendicitis"""
    rows = []
    for line in data.strip().split("\n"):
        parts = line.strip().split(None, 1)
        rows.append({"ICD9": parts[0], "Description": parts[1]})
    df = pd.DataFrame(rows)
    save_dataset(df, "codes")
    return df


def create_college() -> pd.DataFrame:
    """Recreate COLLEGE dataset with random data."""
    rng_main = np.random.RandomState(123456)
    rng0 = np.random.RandomState(0)
    rows = []
    for i in range(100):
        student_id = str(int(round(rng_main.random() * 10000))).zfill(5)
        gender = "M" if rng0.random() < 0.4 else "F"
        r1 = rng0.random()
        if r1 < 0.3:
            school_size = "S"
        elif rng0.random() < 0.7:
            school_size = "M"
        else:
            school_size = "L"
        scholarship = "Y" if rng0.random() < 0.2 else "N"
        gpa = round(rng0.randn() * 0.5 + 3.5, 2)
        if gpa > 4:
            gpa = 4.0
        class_rank = int(rng0.random() * 60 + 41)
        if rng0.random() < 0.1:
            class_rank = np.nan
        if rng0.random() < 0.05:
            school_size = ""
        if rng0.random() < 0.05:
            gpa = np.nan
        rows.append({
            "StudentID": student_id, "Gender": gender,
            "SchoolSize": school_size, "Scholarship": scholarship,
            "GPA": gpa, "ClassRank": class_rank,
        })
    df = pd.DataFrame(rows)
    save_dataset(df, "college")
    return df


def create_fitness() -> pd.DataFrame:
    """Recreate FITNESS dataset."""
    rng = np.random.RandomState(13579246)
    rows = []
    for subj in range(1, 101):
        time_mile = round(rng.normal(8, 2), 1)
        if time_mile < 4.5:
            time_mile += 4
        rest_pulse = 40 + int(2 * time_mile) + rng.normal(5, 5)
        max_pulse = int(rest_pulse + rng.normal(100, 5))
        rows.append({"Subj": subj, "TimeMile": time_mile,
                      "RestPulse": rest_pulse, "MaxPulse": max_pulse})
    df = pd.DataFrame(rows)
    save_dataset(df, "fitness")
    return df


def create_grades() -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, "numgrades.txt")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read()
        tokens = content.split()
        rows = []
        for i in range(0, len(tokens), 2):
            if i + 1 < len(tokens):
                rows.append({"ID": tokens[i], "Grade": int(tokens[i + 1])})
        df = pd.DataFrame(rows)
        save_dataset(df, "grades")
        return df
    return pd.DataFrame()


def create_gym() -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, "gym.txt")
    if os.path.exists(filepath):
        names = ["Subj", "Date", "Fee"]
        df = read_sas_list_input(filepath, names,
                                  date_informats={"Date": "mmddyy10."},
                                  truncover=True)
        df["Subj"] = df["Subj"].apply(lambda x: str(int(x)).zfill(3) if pd.notna(x) else "")
        save_dataset(df, "gym")
        return df
    return pd.DataFrame()


def create_dxcodes() -> pd.DataFrame:
    data = """\
01 Cold
02 Flu
03 Headache
04 Heart Failure
05 Hypertension
06 Psychiatric Problem
07 Laceration
08 Blood Sugar Problems
09 Cough
10 Difficulty Breathing"""
    rows = []
    for line in data.strip().split("\n"):
        parts = line.strip().split(None, 1)
        rows.append({"Dx": parts[0], "Description": parts[1]})
    df = pd.DataFrame(rows)
    save_dataset(df, "dxcodes")
    return df


def create_wide() -> pd.DataFrame:
    data = """\
001 8 5 6 5 4 10 20 30 40 50
002 7 5 6 4 5 11 33 29 34 56
003 2 2 4 5 6 22 38 21 20 34"""
    cols = [("Subj", "$")] + [(f"X{i}", None) for i in range(1, 6)] + \
           [(f"Y{i}", None) for i in range(1, 6)]
    df = read_datalines(data, cols)
    save_dataset(df, "wide")
    return df


def create_endofyear() -> pd.DataFrame:
    data = """\
001 3000 3000 3400 . 3500 3500 3600 3600 3700 3700 3800 .
500 . . . . 400 . . . . . 100
002 . . . . . . . . . . . .
. . . . . . . . . . . .
003 2300 2300 2300 2300 2300 2400 2400 2400 2400 2400 2400 2400
. . . . . . . . . . . ."""
    lines = data.strip().split("\n")
    rows = []
    i = 0
    while i + 1 < len(lines):
        line1_tokens = lines[i].split()
        line2_tokens = lines[i + 1].split()
        row = {"ID": line1_tokens[0]}
        for j in range(12):
            val = line1_tokens[j + 1] if j + 1 < len(line1_tokens) else "."
            row[f"Pay{j+1}"] = np.nan if val == "." else float(val)
        for j in range(12):
            val = line2_tokens[j] if j < len(line2_tokens) else "."
            row[f"Extra{j+1}"] = np.nan if val == "." else float(val)
        rows.append(row)
        i += 2
    df = pd.DataFrame(rows)
    save_dataset(df, "endofyear")
    return df


def create_narrow() -> pd.DataFrame:
    data = """\
001 7 6 5 5 4
002 8 7 6 6 6
003 8 7 6 6 5"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        subj = tokens[0]
        for time_idx in range(1, 6):
            rows.append({"Subj": subj, "Time": time_idx,
                          "Score": int(tokens[time_idx])})
    df = pd.DataFrame(rows)
    save_dataset(df, "narrow")
    return df


def create_dailyprices() -> pd.DataFrame:
    data = """\
CSCO 19.75 20 20.5 21 .
IBM 76 78 75 79 81
LU 2.55 2.53 . . .
AVID 41.25 . . . .
BAC 51 51 51.2 49.9 52.1"""
    jan1 = _sas_date("01Jan2007")
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        symbol = tokens[0]
        for j in range(5):
            date_val = jan1 + j
            price_str = tokens[j + 1] if j + 1 < len(tokens) else "."
            if price_str != ".":
                rows.append({"Symbol": symbol, "Date": date_val,
                              "Price": float(price_str)})
    df = pd.DataFrame(rows)
    save_dataset(df, "dailyprices")
    return df


def create_left_right() -> tuple:
    left_data = """\
001 68 155
002 75 220
003 65 99
005 79 266
006 70 190
009 61 122"""
    right_data = """\
001 46000
003 67900
004 28200
005 98202
006 88000
007 57200"""
    left_df = read_datalines(left_data, [("Subj", "$"), ("Height", None), ("Weight", None)])
    right_df = read_datalines(right_data, [("Subj", "$"), ("Salary", None)])
    save_dataset(left_df, "left")
    save_dataset(right_df, "right")
    return left_df, right_df


def create_missing_ds() -> pd.DataFrame:
    data = """\
X Y Z
X Y Y
Z Z Z
X X .
Y Z .
X . ."""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        a = tokens[0] if tokens[0] != "." else ""
        b = tokens[1] if len(tokens) > 1 and tokens[1] != "." else ""
        c = tokens[2] if len(tokens) > 2 and tokens[2] != "." else ""
        rows.append({"A": a, "B": b, "C": c})
    df = pd.DataFrame(rows)
    save_dataset(df, "missing")
    return df


def create_first_second() -> tuple:
    first_data = "001 10 20 30\n002 11 21 31\n004 12 14 15"
    second_data = "001 33 44 55\n002 60 70 80\n003 80 90 100\n004 777 888 999"
    first_df = read_datalines(first_data, [("Subj", "$"), ("x", None), ("y", None), ("z", None)])
    second_df = read_datalines(second_data, [("Subj", "$"), ("z", None), ("y", None), ("x", None)])
    save_dataset(first_df, "first")
    save_dataset(second_df, "second")
    return first_df, second_df


def create_grouping() -> pd.DataFrame:
    data = "2 4 5 2 4 5 3 4 5 3 . 6"
    tokens = data.split()
    rows = []
    for t in tokens:
        if t == ".":
            rows.append({"X": np.nan})
        else:
            rows.append({"X": int(t)})
    df = pd.DataFrame(rows)
    save_dataset(df, "grouping")
    return df


def create_many_one_two() -> tuple:
    one_data = "123 90\n123 80\n222 95\n333 100\n333 150\n333 200"
    two_data = "123 3\n123 4\n123 5\n222 6\n333 7\n333 8"
    one = read_datalines(one_data, [("ID", None), ("X", None)])
    two = read_datalines(two_data, [("ID", None), ("Y", None)])
    save_dataset(one, "many_one")
    save_dataset(two, "many_two")
    return one, two


def create_truncate() -> pd.DataFrame:
    data = """\
18.8 100.7 98.25
25.12 122.4 5.99
64.99 188 .0001"""
    rows = []
    for line in data.strip().split("\n"):
        tokens = line.split()
        age_raw = float(tokens[0])
        weight_raw = float(tokens[1])
        cost = float(tokens[2])
        age = int(age_raw)  # INT()
        wt_kg = round(weight_raw / 2.2, 1)  # ROUND(Weight/2.2, .1)
        weight = round(weight_raw)  # ROUND(Weight)
        next_dollar = math.ceil(cost)  # CEIL(Cost)
        rows.append({"Age": age, "Weight": weight, "Cost": cost,
                      "WtKg": wt_kg, "Next_Dollar": next_dollar})
    df = pd.DataFrame(rows)
    save_dataset(df, "truncate")
    return df


# ===================================================================
# Master builder
# ===================================================================

ALL_CREATORS = {
    "address": create_address,
    "chars": create_chars,
    "careless": create_careless,
    "cleaning": create_cleaning,
    "oneper": create_oneper,
    "manyper": create_manyper,
    "school": create_school,
    "month_day_year": create_month_day_year,
    "sales": create_sales,
    "medical": create_medical,
    "bicycles": create_bicycles,
    "assign": create_assign,
    "survey": create_survey,
    "clinic": create_clinic,
    "hosp": create_hosp,
    "hosp_discharge": create_hosp_discharge,
    "health": create_health,
    "demographic": create_demographic,
    "new_members": create_new_members,
    "insurance": create_insurance,
    "new_members_order": create_new_members_order,
    "inventory": create_inventory,
    "purchase": create_purchase,
    "newproducts": create_newproducts,
    "demographic_id": create_demographic_id,
    "survey1": create_survey1,
    "survey2": create_survey2,
    "test_scores": create_test_scores,
    "upper": create_upper,
    "psych": create_psych,
    "char_num": create_char_num,
    "stocks": create_stocks,
    "names_and_more": create_names_and_more,
    "phone": create_phone,
    "study": create_study,
    "errors": create_errors,
    "expose": create_expose,
    "mixed": create_mixed,
    "mixed_units": create_mixed_units,
    "social": create_social,
    "spss": create_spss,
    "personal": create_personal,
    "nines": create_nines,
    "blood": create_blood,
    "bloodpressure": create_bloodpressure,
    "numeric": create_numeric,
    "codes": create_codes,
    "college": create_college,
    "fitness": create_fitness,
    "grades": create_grades,
    "gym": create_gym,
    "dxcodes": create_dxcodes,
    "wide": create_wide,
    "endofyear": create_endofyear,
    "narrow": create_narrow,
    "dailyprices": create_dailyprices,
    "missing": create_missing_ds,
    "grouping": create_grouping,
    "truncate": create_truncate,
}

# Datasets that return tuples
_TUPLE_CREATORS = {
    "one_two_three": create_one_two_three,
    "employee_hours": create_employee_hours,
    "bert_ernie": create_bert_ernie,
    "divisions": create_divisions,
    "oscar": create_oscar,
    "prices_new": create_prices_new,
    "left_right": create_left_right,
    "first_second": create_first_second,
    "many_one_two": create_many_one_two,
}


def build_all(export_csv: bool = False, csv_dir: Optional[str] = None) -> dict:
    """Build every dataset and optionally export reference CSVs.

    Parameters
    ----------
    export_csv : bool
        If ``True``, write each DataFrame to a CSV file.
    csv_dir : str, optional
        Directory for CSVs (defaults to ``tests/reference_data/``).

    Returns
    -------
    dict
        ``{name: DataFrame}`` for all single-DataFrame datasets.
    """
    if csv_dir is None:
        csv_dir = os.path.join(os.path.dirname(__file__), "tests", "reference_data")
    os.makedirs(csv_dir, exist_ok=True)

    results = {}

    for name, creator in ALL_CREATORS.items():
        print(f"  Creating {name}...", end=" ")
        try:
            df = creator()
            results[name] = df
            if export_csv and not df.empty:
                df.to_csv(os.path.join(csv_dir, f"{name}.csv"), index=False)
            print("OK" + (f" ({len(df)} rows)" if not df.empty else " (empty)"))
        except Exception as exc:
            print(f"FAILED: {exc}")

    # Tuple creators
    for group_name, creator in _TUPLE_CREATORS.items():
        print(f"  Creating {group_name}...", end=" ")
        try:
            result = creator()
            if isinstance(result, tuple):
                for idx, df in enumerate(result):
                    if isinstance(df, pd.DataFrame) and not df.empty and export_csv:
                        # Individual datasets are saved inside their creators
                        pass
            print("OK")
        except Exception as exc:
            print(f"FAILED: {exc}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build all SAS example datasets")
    parser.add_argument("--csv", action="store_true", help="Export reference CSVs")
    parser.add_argument("--csv-dir", help="Directory for CSV output")
    args = parser.parse_args()

    print("Building all datasets...")
    results = build_all(export_csv=args.csv, csv_dir=args.csv_dir)
    print(f"\nDone. Built {len(results)} datasets in {DATASETS_DIR}")
