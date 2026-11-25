"""Parity case registry.

A case is a list of steps run in ONE SAS session (and one PySpark job). Each step is a
snippet of the repo's own SAS code plus the datasets to snapshot right after it runs:

  book:<n-m>          program *n-m; from "Example code/Programs Used in the Second Edition.sas"
  section:ch10-setup  the "Programs to create data sets One, Two, and Three" block of chapter 10
  cd:<NAME>           the "*Data set NAME;" block of "Example code/Create_Datasets.sas"

A snapshot "WORK.X" or "LEARN.X" is saved as s<n>_<m>_<x> (lower case) and compared with
the dataset of the same label produced by the PySpark port.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Case:
    id: str
    title: str
    steps: list[tuple[str, list[str]]]
    unordered: set[str] = field(default_factory=set)   # labels compared as multisets
    sql_capture: bool = False                           # turn PROC SQL SELECTs into CREATE TABLE


CASES: list[Case] = [
    Case("ch01_veggies", "List input, $8 default length, division by zero",
         [("book:1-1", ["Veg"])]),
    Case("ch02_bmi", "List input + BMI expression with missing values",
         [("book:2-2", ["Demographic"]), ("book:3-2", ["Demographics"])]),
    Case("ch03_bank", "Column input and formatted input (mmddyy10., 7.)",
         [("book:3-6", ["Financial"]), ("book:3-7", ["Financial"])]),
    Case("ch03_list", "DSD / & modifier list input with informats",
         [("book:3-10", ["List_Example"]), ("book:3-12", ["list_example"])]),
    Case("ch05_survey", "PAD infile, grouped informats, user formats on a permanent dataset",
         [("book:5-6", []), ("book:5-7", ["Learn.Survey"]), ("book:10-3", ["Males", "Females"])]),
    Case("ch07_conditional", "IF/ELSE-IF chains and SELECT/WHEN over missing values",
         [("book:7-3", ["Conditional"]), ("book:7-5", ["Conditional"])]),
    Case("ch08_grades_retain", "MISSOVER, DO groups, RETAIN and sum statements",
         [("book:8-2", ["Grades"]), ("book:8-5", ["Revenue"])]),
    Case("ch08_loops", "Iterative DO, DO UNTIL, CONTINUE with explicit OUTPUT",
         [("book:8-9", ["Compound"]), ("book:8-13", ["Double"]), ("book:8-19", ["Continue_on"]),
          ("book:8-12", ["Easyway"])]),
    Case("ch09_dates", "Date informats, YEARCUTOFF, YRDIF, WEEKDAY/DAY/MONTH/YEAR",
         [("book:9-2", ["Four_Dates"]), ("book:9-3", ["Ages"]), ("book:9-6", ["Extract"])]),
    Case("ch10_combine", "SET concatenation, interleave, MERGE with IN=, multi-OUTPUT",
         [("section:ch10-setup", []), ("book:10-4", ["One_Two"]), ("book:10-5", ["One_Three"]),
          ("book:10-6", ["Interleave"]), ("book:10-8", ["Combine"]), ("book:10-10", ["Combine"]),
          ("book:10-11", ["In_Both", "Missing_Name"])]),
    Case("ch10_keys", "RENAME= merge, PUT(ssn11.), INPUT/COMPRESS, UPDATE",
         [("section:ch10-setup", []), ("book:10-13", ["Sesame"]), ("book:10-14", ["Both_Divisions"]),
          ("book:10-15", ["Division2N"]), ("book:10-16", ["Prices_15dec2017"])]),
    Case("ch10_means_set", "PROC MEANS autoname + IF _N_=1 THEN SET",
         [("cd:BLOOD", []), ("book:10-7", ["Means", "Percent"])]),
    Case("ch11_functions", "Numeric functions, LAG/DIF, LARGEST, CALL SORTN, missing counters",
         [("cd:BLOOD", []), ("book:11-3", ["Test_Miss"]), ("book:11-1", ["Truncate"]),
          ("book:11-4", ["Psych"]), ("book:11-5", ["Three_Large"]), ("book:11-7", ["Math"]),
          ("book:11-15", ["Look_Back"]), ("book:11-16", ["Laggard"]), ("book:11-18", ["Diff"]),
          ("book:11-19", ["Quizzes"]), ("book:11-20", ["Quizzes"])]),
    Case("ch12_strings", "PROPCASE/COMPBL, SUBSTR, SCAN, TRANSLATE, TRANWRD, #n pointers",
         [("cd:ADDRESS", []), ("book:12-3", ["Standard"]), ("book:12-12", ["Extract"]),
          ("book:12-13", ["First_Last"]), ("book:12-14", ["Last"]), ("book:12-16", ["Trans"]),
          ("book:12-17", ["Address"])]),
    Case("ch13_arrays", "Arrays, non-1 lower bounds, _TEMPORARY_ answer keys, @@",
         [("book:13-5", ["Temp"]), ("book:13-6", ["Account"]), ("book:13-7", ["Score"])]),
    Case("ch16_means", "PROC MEANS OUTPUT: stats, NWAY, CHARTYPE _TYPE_, split by _TYPE_",
         [("cd:BLOOD", []), ("book:16-7", ["Many_Stats"]), ("book:16-11", ["With_Class"]),
          ("book:16-13", ["Summary"]), ("book:16-15", ["Grand", "By_gender", "By_Age", "Cellmeans"])]),
    Case("ch23_transpose", "Wide<->long with arrays, FIRST./LAST., PROC TRANSPOSE",
         [("cd:ONEPER", []), ("book:23-1", ["Learn.ManyPer"]), ("book:23-2", ["OnePer"]),
          ("book:23-3", ["ManyPer"]), ("book:23-5", ["OnePer"])]),
    Case("ch24_by_groups", "BY-group processing, PROC FREQ OUT=, conditional LAG",
         [("cd:CLINIC", []), ("book:24-1", ["Last"]), ("book:24-2", ["Count"]), ("book:24-3", ["Counts"]),
          ("book:24-4", ["Counts", "Clinic"]), ("book:24-5", ["Difference"]), ("book:24-6", ["First_Last"]),
          ("book:24-7", ["First_Last"]), ("book:24-8", ["Hypertension"])]),
    Case("ch26_sql", "PROC SQL: WHERE, inner/left/right/full joins, remerged summary",
         [("cd:HEALTH", []), ("cd:DEMOGRAPHIC", []), ("book:26-3", ["Height65"]),
          ("book:26-7", ["Inner"]), ("book:26-8", ["_sql1"]),
          ("book:26-9", ["_sql1", "_sql2", "_sql3"]), ("book:26-11", ["_sql1"])],
         unordered={"s26_8__sql1", "s26_9__sql1", "s26_9__sql2", "s26_9__sql3"},
         sql_capture=True),
]


def label(step: str, ds: str) -> str:
    sid = step.split(":", 1)[1].replace("-", "_")
    name = ds.split(".")[-1].lower()
    return f"s{sid}_{name}"


def by_id(case_id: str) -> Case:
    return next(c for c in CASES if c.id == case_id)
