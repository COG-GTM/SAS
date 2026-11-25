"""Triage notes for datasets that differ: label -> (classification, columns it explains, explanation).

Classifications: ENGINE_GAP (blackbox engine deviates from documented SAS behaviour; the PySpark port
keeps the documented behaviour), TRANSLATION_BUG (PySpark port wrong, not yet fixed).
A note is applied only when the dataset differs in the latest run, only in those columns, with no row-count or
column-set differences; anything else is reported as UNTRIAGED.
"""
_SURVEY = ("ENGINE_GAP", {f"Ques{i}" for i in range(1, 6)}, "`input ... (Ques1-Ques5)(: $1.);` — the engine ignores the `$` in a grouped informat "
           "list and creates Ques1-Ques5 as numeric (values 1-5) instead of character $1. SAS reads them as character "
           "(that is why the program attaches the character format `$Likert.`). PySpark keeps them character.")
NOTES: dict[str, tuple[str, set[str], str]] = {
    "s5_7_survey": _SURVEY,
    "s10_3_males": _SURVEY,
    "s10_3_females": _SURVEY,
    "s8_12_easyway": ("ENGINE_GAP", {"Group"}, "`do Group = 'Placebo','Active';` — the engine creates Group as a numeric variable "
                      "and every value is missing; SAS creates a character variable (length 7) holding "
                      "'Placebo' for Subj 1-5 and 'Active' for Subj 6-10. All other columns match."),
    "s9_3_ages": ("UNVERIFIED_SEMANTICS", {"Age"}, "`Age = yrdif(DOB, VisitDate);` — with no basis argument the "
                  "engine uses the 'AGE' basis (`_yrdif(ctx, a, b, basis=\"AGE\")` in sasengine/functions.py); the "
                  "PySpark port uses 'ACT/ACT'. Which one SAS uses when the basis is omitted was not verified against a "
                  "licensed SAS run in this work, so this is neither claimed as an engine gap nor as a port bug. "
                  "Differences are at most 0.0026 year."),
    "s12_3_standard": ("ENGINE_GAP", {"Name"}, "`propcase(Name)` — the engine also upper-cases the letter after an apostrophe "
                       "(O'Brien); SAS's default PROPCASE delimiters are blank / - ( . and tab, so SAS returns "
                       "O'brien (the SAS documentation example gives `Ed O'brien`). PySpark follows SAS."),
    "s12_17_address": ("ENGINE_GAP", {"City", "State", "Zip"}, "`infile datalines dlm=' ,'; input ... #3 City & $20. State : $2. Zip : $5.;` — "
                       "with the & modifier SAS keeps single embedded blanks and ends the value at two consecutive "
                       "delimiters (', '), giving City='Long Beach', State='NJ'. The engine ends City at the first "
                       "blank ('Long'), shifting State/Zip. Only records whose city has an embedded blank differ."),
}

# Translation bugs found by earlier runs of this harness and fixed in the PySpark ports.
FIXED: list[tuple[str, str]] = [
    ("s10_8_combine, s10_11_missing_name, s10_13_sesame, s10_14_both_divisions",
     "`match_merge` lost every non-BY value (all NULL) because the self-joined frames had ambiguous column "
     "lineage; rewritten with uniquely renamed columns per input dataset."),
    ("s10_14_both_divisions", "MERGE output put the BY variable first; SAS's PDV order is first appearance across "
     "the input datasets (DOB Gender SS JobCode Salary). Ports now keep that order."),
    ("s24_3_counts", "The port applied 24-4's `(rename=(count=N_Visits) drop=percent)` to 24-3's `out=Counts`; 24-3 "
     "keeps COUNT and PERCENT. Split into s24_3_counts and s24_4_counts."),
    ("ch09_dates (job failure)", "DATE9. informat used `array_position(array, column)`, which PySpark 3.5 rejects "
     "(`Column is not iterable`); replaced with a month map lookup."),
    ("ch12_strings (job failure)", "PROPCASE was a Python UDF whose module was not importable on the Spark "
     "workers; replaced with a native higher-order-function expression."),
]
