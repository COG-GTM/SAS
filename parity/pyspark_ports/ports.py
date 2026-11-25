"""PySpark ports of the SAS programs listed in parity/cases.py.

Each ``case_<id>(spark, mock)`` returns ``{label: DataFrame}`` using the same snapshot labels as
the SAS run (``s<chapter>_<program>_<dataset>``). Comments quote the SAS statement being ported.
"""
from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from .sasspark import (W, arr, char, col_, compbl, concat_sets, cumulative, datalines, date9, day, dollar,
                       fixed_char, freq_out, interleave, lag, largest, match_merge, max_of, mean_of, min_of,
                       missing_char, mmddyy, month, n_of, num, obs_from_stream, propcase, raw, renumber,
                       sas_int, sas_round, scan, sortn, sum_of, token_stream, tokens, tranwrd, update, weekday,
                       year, yrdif_actact)

L = F.lit
NULL = F.lit(None).cast("double")


def _ws(df: DataFrame, names: list[str]) -> DataFrame:
    return tokens(df, names)


# ------------------------------------------------------------------ ch01 / ch02 / ch03
def case_ch01_veggies(spark, mock):
    # input Name $ Code $ Days Number Price;  CostPerSeed = Price / Number;
    t = _ws(raw(spark, mock, "veggies.txt"), ["Name", "Code", "Days", "Number", "Price"])
    veg = t.select("_ord", char("Name", 8).alias("Name"), char("Code", 8).alias("Code"),
                   num("Days").alias("Days"), num("Number").alias("Number"), num("Price").alias("Price"))
    veg = veg.withColumn("CostPerSeed", F.col("Price") / F.col("Number"))      # x/0 -> missing
    return {"s1_1_veg": veg}


def case_ch02_bmi(spark, mock):
    t = _ws(raw(spark, mock, "mydata.txt"), ["Gender", "Age", "Height", "Weight"])
    d = t.select("_ord", char("Gender", 8).alias("Gender"), *[num(c).alias(c) for c in ("Age", "Height", "Weight")])
    d = d.withColumn("BMI", (F.col("Weight") / 2.2) / F.pow(F.col("Height") * .0254, 2))
    c = raw(spark, mock, "mydata.csv")
    p = F.split(F.col("value"), ",", -1)                                         # dsd: ,, = missing
    unq = lambda i: F.regexp_replace(F.element_at(p, i), '^"|"$', "")           # noqa: E731
    d2 = c.select("_ord", char(unq(1), 8).alias("Gender"), num(unq(2)).alias("Age"),
                  num(unq(3)).alias("Height"), num(unq(4)).alias("Weight"))
    return {"s2_2_demographic": d, "s3_2_demographics": d2}


def case_ch03_bank(spark, mock):
    b = raw(spark, mock, "bank.txt")
    # Subj $ 1-3  DOB $ 4-13  Gender $ 14  Balance 15-21
    f1 = b.select("_ord", fixed_char(col_(1, 3), 3).alias("Subj"), fixed_char(col_(4, 10), 10).alias("DOB"),
                  fixed_char(col_(14, 1), 1).alias("Gender"), num(col_(15, 7)).alias("Balance"))
    # @1 Subj $3. @4 DOB mmddyy10. @14 Gender $1. @15 Balance 7.
    f2 = b.select("_ord", fixed_char(col_(1, 3), 3).alias("Subj"), mmddyy(col_(4, 10)).alias("DOB"),
                  fixed_char(col_(14, 1), 1).alias("Gender"), num(col_(15, 7)).alias("Balance"))
    return {"s3_6_financial": f1, "s3_7_financial": f2}


def case_ch03_list(spark, mock):
    c = raw(spark, mock, "list.csv")
    p = F.split(F.col("value"), ',(?=(?:[^"]*"[^"]*")*[^"]*$)', -1)               # dsd: commas outside quotes
    unq = lambda i: F.regexp_replace(F.element_at(p, i), '^"|"$', "")            # noqa: E731
    a = c.select("_ord", char(unq(1), 3).alias("Subj"), char(unq(2), 20).alias("Name"),
                 mmddyy(unq(3)).alias("DOB"), dollar(unq(4)).alias("Salary"))
    t = raw(spark, mock, "list.txt")
    rx = r"^\s*(\S+)\s+(.+?)\s{2,}(\S+)\s+(\S+)"                                 # Name & $20. ends at 2 blanks
    g = lambda i: F.regexp_extract("value", rx, i)                                # noqa: E731
    b = t.select("_ord", char(g(1), 3).alias("Subj"), char(g(2), 20).alias("Name"),
                 mmddyy(g(3)).alias("DOB"), dollar(g(4)).alias("Salary"))
    return {"s3_10_list_example": a, "s3_12_list_example": b}


# ------------------------------------------------------------------ ch05 / ch07 / ch08
def case_ch05_survey(spark, mock):
    names = ["ID", "Gender", "Age", "Salary"] + [f"Ques{i}" for i in range(1, 6)]
    t = _ws(raw(spark, mock, "survey.txt"), names)
    s = t.select("_ord", char("ID", 3).alias("ID"), char("Gender", 1).alias("Gender"),
                 num("Age").alias("Age"), num("Salary").alias("Salary"),
                 *[char(f"Ques{i}", 1).alias(f"Ques{i}") for i in range(1, 6)])
    males = renumber(s.where(F.col("Gender") == "M"))
    females = renumber(s.where(F.col("Gender") == "F"))
    return {"s5_7_survey": s, "s10_3_males": males, "s10_3_females": females}


def _conditional(spark, mock, key):
    t = _ws(datalines(spark, mock, key), ["Age", "Gender", "Midterm", "Quiz", "FinalExam"])
    d = t.select("_ord", char("Gender", 1).alias("Gender"), char("Quiz", 2).alias("Quiz"),
                 num("Age").alias("Age"), num("Midterm").alias("Midterm"), num("FinalExam").alias("FinalExam"))
    age = F.col("Age")
    grp = (F.when(age.isNull(), NULL).when(age < 20, 1.0).when(age < 40, 2.0)
            .when(age < 60, 3.0).when(age >= 60, 4.0))
    return d.withColumn("AgeGroup", grp.cast("double"))


def case_ch07_conditional(spark, mock):
    return {"s7_3_conditional": _conditional(spark, mock, "book_7-3"),
            "s7_5_conditional": _conditional(spark, mock, "book_7-5")}


def case_ch08_grades_retain(spark, mock):
    # infile missover: short records leave trailing variables missing
    t = _ws(raw(spark, mock, "grades.txt"), ["Age", "Gender", "Midterm", "Quiz", "FinalExam"])
    g = t.select("_ord", char("Gender", 1).alias("Gender"), char("Quiz", 2).alias("Quiz"),
                 num("Age").alias("Age"), num("Midterm").alias("Midterm"), num("FinalExam").alias("FinalExam"))
    g = g.where(F.col("Age").isNotNull())                                        # if missing(Age) then delete
    young = F.col("Age") <= 39
    g = g.select("_ord", "Gender", "Quiz",
                 F.when(young, L("Younger group")).otherwise(L("Older group")).alias("AgeGroup"),
                 "Age", "Midterm", "FinalExam",
                 F.when(young, .4 * F.col("Midterm") + .6 * F.col("FinalExam"))
                  .otherwise((F.col("Midterm") + F.col("FinalExam")) / 2).alias("Grade"))
    r = _ws(datalines(spark, mock, "book_8-5"), ["Day", "Revenue"])
    r = r.select("_ord", char("Day", 3).alias("Day"), dollar("Revenue").alias("Revenue"))
    r = r.select("_ord", cumulative(F.col("Revenue")).alias("Total"), "Day", "Revenue")   # retain Total 0
    return {"s8_2_grades": renumber(g), "s8_5_revenue": r}


def case_ch08_loops(spark, mock):
    yrs = spark.range(1, 101).select(F.col("id").cast("double").alias("Year"), F.col("id").alias("_ord"))
    tot = 100 * F.pow(L(1.0375), F.col("Year"))
    base = yrs.select("_ord", L(.0375).alias("Interest"), tot.alias("Total"), "Year")
    compound = base.where(F.col("Year") <= 3)
    # do until (Total ge 200): body runs, then the test -> includes first year with Total >= 200
    first200 = base.where(F.col("Total") >= 200).agg(F.min("Year")).first()[0]
    double = base.where(F.col("Year") <= first200)
    # do Year=1 to 100 until(Total ge 200); ... if Total le 150 then continue; output;
    cont = base.where((F.col("Year") <= first200) & (F.col("Total") > 150))
    scores = token_stream(spark.createDataFrame([(0, "250 222 230 210 199"), (1, "166 183 123 129 234")],
                                                "_ord long, value string"))
    sc = scores.withColumn("_i", F.row_number().over(W) - 1)
    easy = sc.select(F.col("_i").alias("_ord"),
                     F.when(F.col("_i") % 10 < 5, L("Placebo")).otherwise(L("Active")).alias("Group"),
                     (F.col("_i") % 5 + 1).cast("double").alias("Subj"), num("tok").alias("Score"))
    return {"s8_9_compound": compound, "s8_13_double": double, "s8_19_continue_on": cont,
            "s8_12_easyway": easy}


# ------------------------------------------------------------------ ch09
def case_ch09_dates(spark, mock):
    d = raw(spark, mock, "dates.txt")   # truncover
    four = d.select("_ord", fixed_char(col_(1, 3), 3).alias("Subject"), mmddyy(col_(5, 10)).alias("DOB"),
                    mmddyy(col_(16, 8)).alias("VisitDate"), mmddyy(col_(26, 8)).alias("TwoDigit"),
                    date9(col_(34, 9)).alias("LastDate"))
    ages = four.withColumn("Age", yrdif_actact(F.col("DOB"), F.col("VisitDate")))
    ext = four.select("*", weekday(F.col("DOB")).alias("Day"), day(F.col("DOB")).alias("DayOfMonth"),
                      month(F.col("DOB")).alias("Month"), year(F.col("DOB")).alias("Year"))
    return {"s9_2_four_dates": four, "s9_3_ages": ages, "s9_6_extract": ext}


# ------------------------------------------------------------------ ch10
def _ch10_setup(spark, mock):
    k = "section_ch10-setup"

    def ws(i, names):
        return _ws(datalines(spark, mock, k, i), names)
    one = ws(1, ["ID", "Name", "Weight"]).select("_ord", char("ID", 3).alias("ID"), char("Name", 12).alias("Name"),
                                                 num("Weight").alias("Weight"))
    two = ws(2, ["ID", "Name", "Weight"]).select("_ord", char("ID", 3).alias("ID"), char("Name", 12).alias("Name"),
                                                 num("Weight").alias("Weight"))
    three = ws(3, ["ID", "Gender", "Name"]).select("_ord", char("ID", 3).alias("ID"),
                                                   char("Gender", 1).alias("Gender"), char("Name", 12).alias("Name"))
    emp = ws(4, ["ID", "Name"]).select("_ord", char("ID", 3).alias("ID"), char("Name", 12).alias("Name"))
    hrs = ws(5, ["ID", "JobClass", "Hours"]).select("_ord", char("ID", 3).alias("ID"),
                                                    char("JobClass", 1).alias("JobClass"), num("Hours").alias("Hours"))
    bert = ws(6, ["ID", "X"]).select("_ord", char("ID", 8).alias("ID"), num("X").alias("X"))
    ernie = ws(7, ["EmpNo", "Y"]).select("_ord", char("EmpNo", 8).alias("EmpNo"), num("Y").alias("Y"))
    div1 = ws(8, ["SS", "DOB", "Gender"]).select("_ord", num("SS").alias("SS"), mmddyy("DOB").alias("DOB"),
                                                 char("Gender", 1).alias("Gender"))
    div2 = ws(9, ["SS", "JobCode", "Salary"]).select("_ord", char("SS", 11).alias("SS"),
                                                     char("JobCode", 3).alias("JobCode"), dollar("Salary").alias("Salary"))
    rx = r"^\s*(\S+)\s+(.+?)\s{2,}(\S+)"                                         # Description & ...
    pr = datalines(spark, mock, k, 11)
    prices = pr.select("_ord", char(F.regexp_extract("value", rx, 1), 3).alias("ItemCode"),
                       char(F.regexp_extract("value", rx, 2), 17).alias("Description"),
                       num(F.regexp_extract("value", rx, 3)).alias("Price"))
    new = ws(12, ["ItemCode", "Price"]).select("_ord", char("ItemCode", 3).alias("ItemCode"), num("Price").alias("Price"))
    return dict(one=one, two=two, three=three, emp=emp, hrs=hrs, bert=bert, ernie=ernie, div1=div1, div2=div2,
                prices=prices, new=new)


def case_ch10_combine(spark, mock):
    s = _ch10_setup(spark, mock)
    out = {"s10_4_one_two": concat_sets(s["one"], s["two"]),
           "s10_5_one_three": concat_sets(s["one"], s["three"])}
    one, two = renumber(s["one"], "ID"), renumber(s["two"], "ID")
    out["s10_6_interleave"] = interleave(["ID"], one, two)
    emp, hrs = renumber(s["emp"], "ID"), renumber(s["hrs"], "ID")
    out["s10_8_combine"] = match_merge(["ID"], emp, hrs)
    m = match_merge(["ID"], emp, hrs, ins=["In_Employee", "In_Hours"])
    out["s10_10_combine"] = renumber(m.where("In_Employee and In_Hours").drop("In_Employee", "In_Hours"))
    out["s10_11_in_both"] = renumber(m.where("In_Employee and In_Hours").drop("In_Employee", "In_Hours"))
    out["s10_11_missing_name"] = renumber(m.where("In_Hours and not In_Employee")
                                          .drop("In_Employee", "In_Hours", "Name"))
    return out


def case_ch10_keys(spark, mock):
    s = _ch10_setup(spark, mock)
    out = {"s10_13_sesame": match_merge(["ID"], s["bert"], s["ernie"].withColumnRenamed("EmpNo", "ID"))}
    d1 = s["div1"]
    ssn = F.lpad(F.col("SS").cast("long").cast("string"), 9, "0")                  # put(NumSS, ssn11.)
    d1c = d1.select("_ord", "DOB", "Gender",
                    F.concat_ws("-", F.substring(ssn, 1, 3), F.substring(ssn, 4, 2), F.substring(ssn, 6, 4)).alias("SS"))
    out["s10_14_both_divisions"] = match_merge(["SS"], d1c, s["div2"])
    d2 = s["div2"]
    out["s10_15_division2n"] = d2.select("_ord", "JobCode", "Salary",
                                         num(F.regexp_replace("SS", r"\D", "")).alias("SS"))
    out["s10_16_prices_15dec2017"] = update(["ItemCode"], renumber(s["prices"], "ItemCode"),
                                            renumber(s["new"], "ItemCode"))
    return out


# ------------------------------------------------------------------ blood (Create_Datasets.sas)
def _blood(spark, mock):
    t = _ws(raw(spark, mock, "blood.txt"), ["Subject", "Gender", "BloodType", "AgeGroup", "WBC", "RBC", "Chol"])
    return t.select("_ord", char("Gender", 6).alias("Gender"), char("BloodType", 2).alias("BloodType"),
                    char("AgeGroup", 5).alias("AgeGroup"), num("Subject").alias("Subject"),
                    num("WBC").alias("WBC"), num("RBC").alias("RBC"), num("Chol").alias("Chol"))


def case_ch10_means_set(spark, mock):
    b = _blood(spark, mock)
    means = b.agg(F.avg("Chol").alias("Chol_Mean")).withColumn("_ord", L(0))
    cm = means.first()["Chol_Mean"]
    pct = b.select("_ord", "Subject", "Chol", L(cm).cast("double").alias("Chol_Mean"),
                   (F.col("Chol") / L(cm)).alias("PercentChol"))
    return {"s10_7_means": means, "s10_7_percent": pct}


def case_ch11_functions(spark, mock):
    b = _blood(spark, mock)
    out = {}
    chol = F.col("Chol")
    out["s11_3_test_miss"] = b.select(
        "*", cumulative(F.when(missing_char("Gender"), 1.0)).alias("MissGender"),
        cumulative(F.when(F.col("WBC").isNull(), 1.0).otherwise(0.0) +
                   F.when(F.col("RBC").isNull(), 1.0).otherwise(0.0)).alias("MissWBC"),
        F.when((chol < 200) & chol.isNotNull(), L("Low")).when(chol >= 200, L("High")).otherwise(L("")).alias("Level"))

    t = _ws(datalines(spark, mock, "book_11-1"), ["Age", "Weight", "Cost"])
    t = t.select("_ord", *[num(c).alias(c) for c in ("Age", "Weight", "Cost")])
    out["s11_1_truncate"] = t.select("_ord", sas_int(F.col("Age")).alias("Age"), sas_round(F.col("Weight")).alias("Weight"),
                                     "Cost", sas_round(F.col("Weight") / 2.2, .1).alias("WtKg"),
                                     F.ceil(F.col("Cost")).cast("double").alias("Next_Dollar"))

    qs = [f"Q{i}" for i in range(1, 11)]
    p = _ws(datalines(spark, mock, "book_11-4"), ["ID"] + qs).select("_ord", char("ID", 8).alias("ID"),
                                                                    *[num(q).alias(q) for q in qs])
    a = arr(*qs)
    psych = p.select("*", F.when(n_of(a) >= 7, mean_of(a)).alias("Score"),
                     max_of(a).alias("MaxScore"), min_of(a).alias("MinScore"))
    out["s11_4_psych"] = psych
    out["s11_5_three_large"] = p.select("*", sum_of(F.array(largest(1, a), largest(2, a), largest(3, a))).alias("SumThree"))

    x = obs_from_stream(token_stream(datalines(spark, mock, "book_11-7")), ["x"]).select("_ord", num("x").alias("x"))
    xc = F.col("x")
    out["s11_7_math"] = x.select("_ord", "x", F.abs(xc).alias("Absolute"),
                                 F.when(xc >= 0, F.sqrt(xc)).alias("Square"), F.exp(xc).alias("Exponent"),
                                 F.when(xc > 0, F.log(xc)).alias("Natural"))

    lt = _ws(datalines(spark, mock, "book_11-15"), ["Time", "Temperature"])
    lt = lt.select("_ord", num("Time").alias("Time"), num("Temperature").alias("Temperature"))
    out["s11_15_look_back"] = lt.select("*", lag(F.col("Temperature")).alias("Prev_Temp"),
                                        lag(F.col("Temperature"), 2).alias("Two_Back"))
    lx = obs_from_stream(token_stream(datalines(spark, mock, "book_11-16")), ["X"]).select("_ord", num("X").alias("X"))
    # if X ge 5 then Last_X = lag(X);   -> the LAG queue only sees executions where X >= 5
    hit = lx.where(F.col("X") >= 5).select("_ord", lag(F.col("X")).alias("Last_X"))
    out["s11_16_laggard"] = lx.join(hit, "_ord", "left")
    dt = _ws(datalines(spark, mock, "book_11-18"), ["Time", "Temperature"])
    dt = dt.select("_ord", num("Time").alias("Time"), num("Temperature").alias("Temperature"))
    out["s11_18_diff"] = dt.select("*", (F.col("Temperature") - lag(F.col("Temperature"))).alias("Diff_Temp"))

    qz = [f"Quiz{i}" for i in range(1, 9)]
    q = _ws(datalines(spark, mock, "book_11-19"), ["ID"] + qz).select("_ord", char("ID", 8).alias("ID"),
                                                                     *[num(c).alias(c) for c in qz])
    qa = arr(*qz)
    out["s11_19_quizzes"] = q.select("*", F.when(n_of(qa) >= 7, mean_of(F.array(*[largest(k, qa) for k in range(1, 7)])))
                                     .alias("Quiz_Score"))
    q2 = _ws(datalines(spark, mock, "book_11-20"), ["ID"] + qz).select("_ord", char("ID", 8).alias("ID"),
                                                                      *[num(c).alias(c) for c in qz])
    srt = q2.select("_ord", "ID", qa.alias("_a"), sortn(qa).alias("_s"))
    srt = srt.select("_ord", "ID", *[F.col("_s")[i].alias(c) for i, c in enumerate(qz)],
                     F.when(n_of(F.col("_a")) >= 7, mean_of(F.slice("_s", 3, 6))).alias("Quiz_Score"))
    out["s11_20_quizzes"] = srt
    return out


# ------------------------------------------------------------------ ch12
def case_ch12_strings(spark, mock):
    out = {}
    a = datalines(spark, mock, "cd_ADDRESS")
    a = a.withColumn("_r", F.floor(F.col("_ord") / 3)).withColumn("_l", F.col("_ord") % 3)
    g = a.groupBy("_r").agg(*[F.max(F.when(F.col("_l") == i, F.col("value"))).alias(f"l{i}") for i in range(3)])
    sub = lambda c, s, w: F.substring(F.coalesce(F.col(c), L("")), s, w)        # noqa: E731
    addr = g.select(F.col("_r").alias("_ord"), fixed_char(sub("l0", 1, 40), 40).alias("Name"),
                    fixed_char(sub("l1", 1, 40), 40).alias("Street"), fixed_char(sub("l2", 1, 20), 20).alias("City"),
                    fixed_char(sub("l2", 21, 2), 2).alias("State"), fixed_char(sub("l2", 24, 5), 5).alias("Zip"))
    out["s12_3_standard"] = addr.select("_ord", *[F.substring(compbl(propcase(F.col(c))), 1, w).alias(c)
                                                  for c, w in (("Name", 40), ("Street", 40), ("City", 20))],
                                        F.upper("State").alias("State"), "Zip")

    ids = obs_from_stream(token_stream(datalines(spark, mock, "book_12-12")), ["ID"]).select("_ord", char("ID", 10).alias("ID"))
    out["s12_12_extract"] = ids.select("_ord", "ID", F.substring("ID", 1, 2).alias("State"),
                                       F.substring("ID", 5, 1).alias("Gender"), F.substring(F.expr("substring(ID, 6)"), 1, 5).alias("Last"),
                                       num(F.substring("ID", 3, 2)).alias("Number"))
    orig = datalines(spark, mock, "book_12-13").select("_ord", fixed_char(F.substring("value", 1, 30), 30).alias("Name"))
    out["s12_13_first_last"] = orig.select("_ord", "Name", F.substring(scan(F.col("Name"), 1), 1, 15).alias("First"),
                                           F.substring(scan(F.col("Name"), 2), 1, 15).alias("Last"))
    last = orig.select("_ord", "Name", F.substring(scan(F.col("Name"), -1), 1, 15).alias("Last_Name"))
    out["s12_14_last"] = renumber(last, "Last_Name")
    tr = _ws(datalines(spark, mock, "book_12-16"), ["Answer"]).select("_ord", char("Answer", 5).alias("Answer"))
    out["s12_16_trans"] = tr.select("_ord", F.translate("Answer", "12345", "ABCDE").alias("Answer"))

    b = datalines(spark, mock, "book_12-17")
    b = b.withColumn("_r", F.floor(F.col("_ord") / 3)).withColumn("_l", F.col("_ord") % 3)
    g = b.groupBy("_r").agg(*[F.max(F.when(F.col("_l") == i, F.col("value"))).alias(f"l{i}") for i in range(3)])
    rx = r"^[ ,]*(.+?)[ ,]{2,}([^ ,]+)[ ,]+([^ ,]+)"                              # City & $20. State : $2. Zip : $5.
    name = fixed_char(F.substring("l0", 1, 30), 30)
    for t in ("Mr.", "Mrs.", "Dr.", "Ms."):
        name = tranwrd(name, t, " ")
    line1 = fixed_char(F.substring("l1", 1, 40), 40)
    for s_, r_ in (("Street", "St."), ("Road", "Rd."), ("Avenue", "Ave.")):
        line1 = tranwrd(line1, s_, r_)
    out["s12_17_address"] = g.select(F.col("_r").alias("_ord"), F.substring(F.ltrim(name), 1, 30).alias("Name"),
                                     F.substring(line1, 1, 40).alias("Line1"),
                                     char(F.regexp_extract("l2", rx, 1), 20).alias("City"),
                                     char(F.regexp_extract("l2", rx, 2), 2).alias("State"),
                                     char(F.regexp_extract("l2", rx, 3), 5).alias("Zip"))
    return out


# ------------------------------------------------------------------ ch13
def case_ch13_arrays(spark, mock):
    out = {}
    fah = [f"Fahren{i}" for i in range(1, 25)]
    t = obs_from_stream(token_stream(datalines(spark, mock, "book_13-5")), fah)
    t = t.select("_ord", *[num(c).alias(c) for c in fah])
    out["s13_5_temp"] = t.select("*", *[((F.col(f"Fahren{i}") - 32) / 1.8).alias(f"Celsius{i}") for i in range(1, 25)])
    inc = [f"Income{y}" for y in range(2010, 2018)]
    a = _ws(datalines(spark, mock, "book_13-6"), ["ID"] + inc).select("_ord", num("ID").alias("ID"),
                                                                      *[num(c).alias(c) for c in inc])
    out["s13_6_account"] = a.select("*", *[(.25 * F.col(f"Income{y}")).alias(f"Taxes{y}") for y in range(2010, 2018)],
                                    L(2018.0).alias("Year"))
    key = "ABCDEEDCBA"
    s = datalines(spark, mock, "book_13-7")
    idt = F.regexp_extract("value", r"^\s*(\S+)", 1)
    # list input leaves the pointer one column past the delimiter that ended ID; (Ans1-Ans10)($1.) reads from there
    s = s.select("_ord", num(idt).alias("ID"), F.rpad("value", 200, " ").alias("_v"),
                 (F.length(F.regexp_extract("value", r"^\s*\S+", 0)) + 2).alias("_s"))
    raw_score = sum((F.expr(f"substring(_v, _s + {q}, 1)") == L(key[q])).cast("double") for q in range(10))
    out["s13_7_score"] = s.select("_ord", "ID", raw_score.alias("RawScore"), (100 * raw_score / 10).alias("Percent"))
    return out


# ------------------------------------------------------------------ ch16
def _means(df, cls: list[str], stats: list[tuple[str, str, str]]):
    aggs = [F.count("*").cast("double").alias("_FREQ_")]
    for var, stat, name in stats:
        e = {"mean": F.avg(var), "n": F.count(var).cast("double"),
             "nmiss": (F.count("*") - F.count(var)).cast("double"), "median": F.median(var)}[stat]
        aggs.append(e.cast("double").alias(name))
    return df.groupBy(*cls).agg(*aggs) if cls else df.agg(*aggs)


def case_ch16_means(spark, mock):
    b = _blood(spark, mock)
    out = {}
    ms = _means(b, [], [("RBC", "mean", "M_RBC"), ("WBC", "mean", "M_WBC"), ("RBC", "n", "N_RBC"), ("WBC", "n", "N_WBC"),
                        ("RBC", "nmiss", "Miss_RBC"), ("WBC", "nmiss", "Miss_WBC"),
                        ("RBC", "median", "Med_RBC"), ("WBC", "median", "Med_WBC")])
    out["s16_7_many_stats"] = ms.select(L(0.0).alias("_TYPE_"), "*", L(0).alias("_ord"))
    auto = [("RBC", "mean", "RBC_Mean"), ("WBC", "mean", "WBC_Mean"), ("RBC", "n", "RBC_N"), ("WBC", "n", "WBC_N")]
    bg = b.where(~missing_char("Gender"))
    wc = _means(bg, ["Gender"], auto)
    out["s16_11_with_class"] = renumber(wc.select("Gender", L(1.0).alias("_TYPE_"), *wc.columns[1:], L(0).alias("_ord")),
                                        "Gender")
    bb = bg.where(~missing_char("AgeGroup"))
    parts = []
    for typ, cls in (("00", []), ("01", ["AgeGroup"]), ("10", ["Gender"]), ("11", ["Gender", "AgeGroup"])):
        m = _means(bb, cls, auto)
        parts.append(m.select(*[F.col(c) if c in cls else L("").alias(c) for c in ("Gender", "AgeGroup")],
                              L(typ).alias("_TYPE_"), "_FREQ_", *[n for _, _, n in auto]))
    summ = parts[0]
    for p in parts[1:]:
        summ = summ.unionByName(p)
    summ = renumber(summ.withColumn("_ord", L(0)), "_TYPE_", "Gender", "AgeGroup")
    out["s16_13_summary"] = summ
    stats = [n for _, _, n in auto]
    pick = lambda t, cols: renumber(summ.where(F.col("_TYPE_") == t)                  # noqa: E731
                                    .select("_ord", *cols, F.col("_FREQ_").alias("Number"), *stats))
    out["s16_15_grand"] = pick("00", [])
    out["s16_15_by_gender"] = pick("10", ["Gender"])
    out["s16_15_by_age"] = pick("01", ["AgeGroup"])
    out["s16_15_cellmeans"] = pick("11", ["Gender", "AgeGroup"])
    return out


# ------------------------------------------------------------------ ch23
def case_ch23_transpose(spark, mock):
    out = {}
    t = _ws(datalines(spark, mock, "cd_ONEPER"), ["Subj", "Dx1", "Dx2", "Dx3"])
    one = t.select("_ord", char("Subj", 3).alias("Subj"), *[num(f"Dx{i}").alias(f"Dx{i}") for i in (1, 2, 3)])
    # do Visit=1 to 3; if missing(Dx{Visit}) then delete; ... output; end;  (DELETE ends the whole iteration)
    rows = []
    for v in (1, 2, 3):
        alive = F.lit(True)
        for u in range(1, v + 1):
            alive = alive & F.col(f"Dx{u}").isNotNull()
        rows.append(one.where(alive).select((F.col("_ord") * 10 + v).alias("_ord"), "Subj",
                                            L(float(v)).alias("Visit"), F.col(f"Dx{v}").alias("Diagnosis")))
    many = renumber(rows[0].unionByName(rows[1]).unionByName(rows[2]))
    out["s23_1_manyper"] = many
    ms = renumber(many, "Subj", "Visit")
    piv = ms.groupBy("Subj").agg(F.max("_ord").alias("_ord"),
                                 *[F.max(F.when(F.col("Visit") == v, F.col("Diagnosis"))).alias(f"Dx{v}") for v in (1, 2, 3)])
    out["s23_2_oneper"] = renumber(piv)
    tr = [one.select((F.col("_ord") * 10 + i).alias("_ord"), "Subj", L(f"Dx{i}").alias("_NAME_"),
                     F.col(f"Dx{i}").alias("COL1")) for i in (1, 2, 3)]
    out["s23_3_manyper"] = renumber(tr[0].unionByName(tr[1]).unionByName(tr[2]))
    k = many.withColumn("_k", F.row_number().over(Window.partitionBy("Subj").orderBy("_ord")))
    kmax = k.agg(F.max("_k")).first()[0]
    p2 = k.groupBy("Subj").agg(F.min("_ord").alias("_ord"),
                               *[F.max(F.when(F.col("_k") == i, F.col("Diagnosis"))).alias(f"Dx{i}") for i in range(1, kmax + 1)])
    out["s23_5_oneper"] = renumber(p2)
    return out


# ------------------------------------------------------------------ ch24
def case_ch24_by_groups(spark, mock):
    out = {}
    t = _ws(datalines(spark, mock, "cd_CLINIC"), ["ID", "VisitDate", "Dx", "HR", "SBP", "DBP"])
    lc = t.select("_ord", char("ID", 5).alias("ID"), mmddyy("VisitDate").alias("VisitDate"), char("Dx", 3).alias("Dx"),
                  *[num(c).alias(c) for c in ("HR", "SBP", "DBP")])
    lc = renumber(lc, "ID", "VisitDate")                                          # proc sort learn.clinic
    g = Window.partitionBy("ID")
    go = Window.partitionBy("ID").orderBy("_ord")
    flag = lc.select("*", (F.row_number().over(go) == 1).alias("_first"),
                     (F.row_number().over(go) == F.count("*").over(g)).alias("_last"),
                     F.row_number().over(go).cast("double").alias("_k"))
    out["s24_1_last"] = renumber(flag.where("_last").drop("_first", "_last", "_k"))
    out["s24_2_count"] = renumber(flag.where("_last").withColumnRenamed("_k", "N_visits").drop("_first", "_last"))
    out["s24_3_counts"] = freq_out(lc, "ID")                                      # 24-3: out=Counts (COUNT PERCENT)
    counts = freq_out(lc, "ID").withColumnRenamed("COUNT", "N_Visits").drop("PERCENT")   # 24-4: rename/drop
    out["s24_4_counts"] = counts
    clinic = match_merge(["ID"], lc, counts)
    out["s24_4_clinic"] = clinic
    cf = clinic.select("*", (F.row_number().over(go) == 1).alias("_first"),
                       (F.row_number().over(go) == F.count("*").over(g)).alias("_last"))
    multi = cf.where(~(F.col("_first") & F.col("_last")))                         # delete single-visit patients
    d = multi.select("*", *[(F.col(v) - lag(F.col(v))).alias(f"Diff_{v}") for v in ("HR", "SBP", "DBP")])
    out["s24_5_difference"] = renumber(d.where(~F.col("_first")).drop("_first", "_last"))
    # lag() only executes on first/last rows -> on the last row it returns the group's first row
    fl = multi.where(F.col("_first") | F.col("_last"))
    fl = fl.select("*", *[(F.col(v) - lag(F.col(v))).alias(f"Diff_{v}") for v in ("HR", "SBP", "DBP")])
    out["s24_6_first_last"] = renumber(fl.where("_last").drop("_first", "_last"))
    wf = Window.partitionBy("ID").orderBy("_ord").rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    rf = multi.select("*", *[(F.col(v) - F.first(v).over(wf)).alias(f"Diff_{v}") for v in ("HR", "SBP", "DBP")])
    out["s24_7_first_last"] = renumber(rf.where("_last").drop("_first", "_last"))
    hb = flag.select("*", F.max((F.col("SBP") > 140).cast("int")).over(
        Window.partitionBy("ID").orderBy("_ord").rowsBetween(Window.unboundedPreceding, 0)).alias("_hi"))
    out["s24_8_hypertension"] = renumber(hb.where("_last").select(
        "_ord", "ID", "VisitDate", "Dx", "HR", "SBP", "DBP",
        F.when(F.col("_hi") == 1, L("Yes")).otherwise(L("No")).alias("HighBP")))
    return out


# ------------------------------------------------------------------ ch26
def case_ch26_sql(spark, mock):
    out = {}
    h = _ws(datalines(spark, mock, "cd_HEALTH"), ["Subj", "Height", "Weight"])
    h = h.select("_ord", char("Subj", 3).alias("Subj"), num("Height").alias("Height"), num("Weight").alias("Weight"))
    d = _ws(datalines(spark, mock, "cd_DEMOGRAPHIC"), ["Subj", "DOB", "Gender", "Name"])
    d = d.select("_ord", char("Subj", 3).alias("Subj"), mmddyy("DOB").alias("DOB"), char("Gender", 1).alias("Gender"),
                 char("Name", 20).alias("Name"))
    out["s26_3_height65"] = renumber(h.where(F.col("Height") > 65))
    m = match_merge(["Subj"], renumber(h, "Subj"), renumber(d, "Subj"), ins=["in_Health", "in_Demographic"])
    out["s26_7_inner"] = renumber(m.where("in_Health and in_Demographic").drop("in_Health", "in_Demographic"))
    H, D = h.alias("H"), d.alias("D")
    on = F.col("H.Subj").eqNullSafe(F.col("D.Subj"))                             # SAS SQL: missing = missing
    o = L(0).alias("_ord")
    out["s26_8__sql1"] = H.join(D, on, "inner").select(
        F.col("H.Subj").alias("Subj_Health"), F.col("D.Subj").alias("Subj_Demog"), "H.Height", "H.Weight",
        "D.Name", "D.Gender", o)
    for i, how in enumerate(("left", "right", "full"), 1):
        out[f"s26_9__sql{i}"] = H.join(D, on, how).select(
            F.col("H.Subj").alias("Subj_Health"), F.col("D.Subj").alias("Subj_Demog"), "H.Height", "D.Gender", o)
    avg = h.agg(F.avg("Height")).first()[0]
    out["s26_11__sql1"] = h.select("_ord", "Subj", "Height", "Weight", L(avg).cast("double").alias("Ave_Height"),
                                   (100 * F.col("Height") / L(avg)).alias("Percent_Height"))
    return out


def run(case_id: str, spark, mock: Path) -> dict[str, DataFrame]:
    return globals()[f"case_{case_id}"](spark, mock)
