"""Small PySpark helpers that reproduce SAS DATA-step / PROC semantics.

Conventions used by every port:
  * row order is explicit: each DataFrame carries a long column ``_ord`` (dropped on output);
  * SAS numerics are doubles, SAS missing numerics are NULL;
  * SAS character missing is the empty string; values are truncated to the SAS LENGTH;
  * SAS dates are day counts since 1960-01-01 (doubles), exactly like SAS stores them.
"""
from __future__ import annotations

from functools import reduce
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

YEARCUTOFF = 1940          # engine + SAS Viya default (SAS 9.4 shipped 1926); see report
SAS_EPOCH = "1960-01-01"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
W = Window.orderBy("_ord")


# ----------------------------------------------------------------------------- reading input
def lines(spark: SparkSession, path: Path) -> DataFrame:
    """INFILE: one row per record, ``_ord`` = record number (0-based), ``value`` = text."""
    rdd = spark.sparkContext.textFile(str(path)).zipWithIndex().map(lambda t: (t[1], t[0].rstrip("\r")))
    return spark.createDataFrame(rdd, "_ord long, value string")


def datalines(spark, mock: Path, key: str, k: int = 1) -> DataFrame:
    return lines(spark, mock / "datalines" / f"{key}__{k}.dat")


def raw(spark, mock: Path, name: str) -> DataFrame:
    return lines(spark, mock / "raw" / name)


def tokens(df: DataFrame, names: list[str], dlm: str = r"\s+") -> DataFrame:
    """List input (blank-delimited): tokens[i] -> column names[i] as raw strings."""
    t = F.split(F.trim(F.col("value")), dlm)
    return df.select("_ord", *[F.element_at(t, i + 1).alias(n) for i, n in enumerate(names)])


def token_stream(df: DataFrame) -> DataFrame:
    """All blank-delimited tokens across records, in order (for @@ input). Columns _ord, tok."""
    x = df.select("_ord", F.posexplode(F.split(F.trim("value"), r"\s+")).alias("_p", "tok"))
    x = x.where(F.col("tok") != "")
    return x.select((F.col("_ord") * 10000 + F.col("_p")).alias("_ord"), "tok")


def obs_from_stream(stream: DataFrame, names: list[str]) -> DataFrame:
    """input v1 ... vn @@ : consecutive groups of n tokens; an incomplete final group is not output."""
    n = len(names)
    s = stream.withColumn("_i", F.row_number().over(W) - 1)
    s = s.withColumn("_obs", F.floor(F.col("_i") / n)).withColumn("_k", F.col("_i") % n)
    g = s.groupBy("_obs").agg(F.map_from_entries(F.collect_list(F.struct("_k", "tok"))).alias("m"),
                              F.count("*").alias("_c"))
    g = g.where(F.col("_c") == n)
    return g.select(F.col("_obs").alias("_ord"), *[F.col("m")[i].alias(nm) for i, nm in enumerate(names)])


# ----------------------------------------------------------------------------- informats
def num(c) -> F.Column:
    """w. / BEST. informat: blank or '.' -> missing; unparseable -> missing."""
    c = F.trim(c if not isinstance(c, str) else F.col(c))
    return F.when((c == "") | (c == ".") | c.isNull(), F.lit(None)).otherwise(c.cast("double"))


def dollar(c) -> F.Column:
    """DOLLARw. / COMMAw. informat: strip $ , and blanks."""
    c = c if not isinstance(c, str) else F.col(c)
    return num(F.regexp_replace(c, r"[$,]", ""))


def char(c, length: int) -> F.Column:
    """$w. / list-input character value: '.' -> missing, left-aligned, truncated to LENGTH."""
    c = c if not isinstance(c, str) else F.col(c)
    c = F.ltrim(F.coalesce(c, F.lit("")))
    return F.substring(F.when(F.trim(c) == ".", F.lit("")).otherwise(c), 1, length)


def fixed_char(c, length: int) -> F.Column:
    """Formatted $w. input / column input: leading blanks removed, '.' kept as text only if not alone."""
    c = c if not isinstance(c, str) else F.col(c)
    return F.substring(F.ltrim(F.coalesce(c, F.lit(""))), 1, length)


def col_(start: int, width: int) -> F.Column:
    """Columns start..start+width-1 of the current record (1-based)."""
    return F.substring(F.col("value"), start, width)


def _sasday(y, m, d) -> F.Column:
    dt = F.make_date(y.cast("int"), m.cast("int"), d.cast("int"))
    return F.datediff(dt, F.lit(SAS_EPOCH)).cast("double")


def _yy(y: F.Column) -> F.Column:
    y = y.cast("int")
    return F.when(y >= YEARCUTOFF % 100, y + (YEARCUTOFF // 100) * 100).otherwise(y + (YEARCUTOFF // 100 + 1) * 100)


def mmddyy(c) -> F.Column:
    """MMDDYYw. informat: m/d/yyyy, mm-dd-yyyy, mmddyyyy, m/d/yy, mmddyy."""
    c = F.trim(c if not isinstance(c, str) else F.col(c))
    sep4 = r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$"
    sep2 = r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2})$"
    dig8 = r"^(\d{2})(\d{2})(\d{4})$"
    dig6 = r"^(\d{2})(\d{2})(\d{2})$"

    def g(p, i):
        return F.regexp_extract(c, p, i)
    return (F.when(c.rlike(sep4), _sasday(g(sep4, 3), g(sep4, 1), g(sep4, 2)))
             .when(c.rlike(sep2), _sasday(_yy(g(sep2, 3)), g(sep2, 1), g(sep2, 2)))
             .when(c.rlike(dig8), _sasday(g(dig8, 3), g(dig8, 1), g(dig8, 2)))
             .when(c.rlike(dig6), _sasday(_yy(g(dig6, 3)), g(dig6, 1), g(dig6, 2))))


def date9(c) -> F.Column:
    """DATEw. informat: ddMONyyyy (case-insensitive month)."""
    c = F.upper(F.trim(c if not isinstance(c, str) else F.col(c)))
    p = r"^(\d{1,2})([A-Z]{3})(\d{2}|\d{4})$"
    mmap = F.create_map(*[x for i, m in enumerate(MONTHS) for x in (F.lit(m), F.lit(i + 1))])
    mon = F.coalesce(F.element_at(mmap, F.regexp_extract(c, p, 2)), F.lit(0))
    y = F.regexp_extract(c, p, 3)
    y = F.when(F.length(y) == 2, _yy(y)).otherwise(y.cast("int"))
    return F.when(c.rlike(p) & (mon > 0), _sasday(y, mon, F.regexp_extract(c, p, 1)))


# ----------------------------------------------------------------------------- functions
def to_date(c) -> F.Column:
    return F.date_add(F.lit(SAS_EPOCH).cast("date"), c.cast("int"))


def weekday(c):
    return F.dayofweek(to_date(c)).cast("double")


def day(c):
    return F.dayofmonth(to_date(c)).cast("double")


def month(c):
    return F.month(to_date(c)).cast("double")


def year(c):
    return F.year(to_date(c)).cast("double")


def _diy(y):
    return F.when(((y % 4 == 0) & (y % 100 != 0)) | (y % 400 == 0), F.lit(366.0)).otherwise(F.lit(365.0))


def yrdif_actact(a, b) -> F.Column:
    """YRDIF(start, end) with the default 'ACT/ACT' basis."""
    lo, hi = F.least(a, b), F.greatest(a, b)
    y1, y2 = F.year(to_date(lo)), F.year(to_date(hi))
    jan1 = lambda y: F.datediff(F.make_date(y, F.lit(1), F.lit(1)), F.lit(SAS_EPOCH))  # noqa: E731
    same = (hi - lo) / _diy(y1)
    span = (jan1(y1 + 1) - lo) / _diy(y1) + (y2 - y1 - 1) + (hi - jan1(y2)) / _diy(y2)
    v = F.when(y1 == y2, same).otherwise(span)
    return F.when(a.isNull() | b.isNull(), F.lit(None)).when(b < a, -v).otherwise(v)


def arr(*cols) -> F.Column:
    return F.array(*[F.col(c) if isinstance(c, str) else c for c in cols])


def nonmiss(a: F.Column) -> F.Column:
    return F.filter(a, lambda x: x.isNotNull())


def n_of(a):
    return F.size(nonmiss(a)).cast("double")


def sum_of(a):
    nm = nonmiss(a)
    return F.when(F.size(nm) > 0, F.aggregate(nm, F.lit(0.0), lambda acc, x: acc + x))


def mean_of(a):
    nm = nonmiss(a)
    return F.when(F.size(nm) > 0, F.aggregate(nm, F.lit(0.0), lambda acc, x: acc + x) / F.size(nm))


def max_of(a):
    return F.array_max(nonmiss(a))


def min_of(a):
    return F.array_min(nonmiss(a))


def largest(k: int, a):
    s = F.sort_array(nonmiss(a), asc=False)
    return F.when(F.size(s) >= k, F.element_at(s, k))


def sortn(a):
    """CALL SORTN: ascending, missing values first."""
    nm = nonmiss(a)
    return F.concat(F.array_repeat(F.lit(None).cast("double"), F.size(a) - F.size(nm)), F.array_sort(nm))


def sas_round(x, unit: float = 1.0):
    """ROUND(x, unit): nearest multiple of unit, halves away from zero."""
    q = x / F.lit(unit)
    r = F.when(q >= 0, F.floor(q + 0.5 + 1e-12)).otherwise(F.ceil(q - 0.5 - 1e-12))
    return r.cast("double") * F.lit(unit)


def sas_int(x):
    return F.when(x >= 0, F.floor(x)).otherwise(F.ceil(x)).cast("double")


def lag(c, n: int = 1, w=W):
    return F.lag(c, n).over(w)


def cumulative(expr, w=None):
    """Sum statement (var + expr): retained, starts at 0, missing increments ignored."""
    w = w or W.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    return F.sum(F.coalesce(expr, F.lit(0.0))).over(w).cast("double")


def propcase(c):
    """PROPCASE(c): lower-case, then upper-case the first letter and every letter after / - ( . tab or blank."""
    chars = F.split(F.lower(F.coalesce(c, F.lit(""))), "")
    delims = F.array(*[F.lit(x) for x in " /-(.\t"])
    up = F.transform(chars, lambda x, i: F.when((i == 0) | F.array_contains(delims, F.element_at(chars, i)),
                                                F.upper(x)).otherwise(x))
    return F.array_join(up, "")


def compbl(c):
    return F.regexp_replace(c, " {2,}", " ")


def tranwrd(c, target: str, repl: str):
    import re
    return F.regexp_replace(c, re.escape(target), repl.replace("\\", "\\\\").replace("$", "\\$"))


def scan(c, n: int):
    """SCAN(c, n, ' ')."""
    parts = F.filter(F.split(F.coalesce(c, F.lit("")), " "), lambda x: x != "")
    idx = F.lit(n) if n > 0 else F.size(parts) + n + 1
    return F.when((idx >= 1) & (idx <= F.size(parts)), F.element_at(parts, idx)).otherwise(F.lit(""))


# ----------------------------------------------------------------------------- procs / steps
def renumber(df: DataFrame, *keys) -> DataFrame:
    """Reassign _ord after a stable sort on keys (PROC SORT default EQUALS)."""
    w = Window.orderBy(*keys, "_ord")
    return df.withColumn("_ord", F.row_number().over(w).cast("long"))


def concat_sets(*dfs: DataFrame) -> DataFrame:
    """SET a b ...: rows of a, then b...; columns in first-seen order, missing ones NULL."""
    cols: list[str] = []
    for d in dfs:
        cols += [c for c in d.columns if c not in cols]
    parts = []
    for i, d in enumerate(dfs):
        sel = [F.col(c) if c in d.columns else F.lit(None).alias(c) for c in cols if c != "_ord"]
        parts.append(d.select(*sel, (F.lit(i) * 10**9 + F.col("_ord")).alias("_ord")))
    out = reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), parts)
    return renumber(out)


def interleave(by: list[str], *dfs: DataFrame) -> DataFrame:
    """SET a b; BY keys; -> rows ordered by key, ties: dataset order then row order."""
    cols: list[str] = []
    for d in dfs:
        cols += [c for c in d.columns if c not in cols and c != "_ord"]
    parts = [d.select(*[F.col(c) if c in d.columns else F.lit(None).alias(c) for c in cols],
                      F.lit(i).alias("_ds"), F.col("_ord").alias("_o")) for i, d in enumerate(dfs)]
    out = reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), parts)
    w = Window.orderBy(*by, "_ds", "_o")
    return out.withColumn("_ord", F.row_number().over(w).cast("long")).drop("_ds", "_o")


def match_merge(by: list[str], *dfs: DataFrame, ins: list[str | None] | None = None) -> DataFrame:
    """MERGE a b ...; BY keys;  (SAS match-merge incl. one-to-many / many-to-many semantics).

    Inside a BY group, obs k of every dataset is combined; a dataset with fewer obs keeps
    contributing its last obs (values retained). IN= flags are 1 for every row of a BY group
    the dataset participates in. For same-named non-BY variables the right-most dataset wins.
    """
    ins = ins or [None] * len(dfs)
    skip = set(by) | {"_ord"}
    keyed = []
    for i, d in enumerate(dfs):
        wg = Window.partitionBy(*by).orderBy("_ord")
        x = d.select(*[F.col(b).alias(f"_b{j}") for j, b in enumerate(by)],
                     F.row_number().over(wg).alias(f"_k{i}"),
                     F.count("*").over(Window.partitionBy(*by)).alias(f"_n{i}"),
                     *[F.col(c).alias(f"{c}__{i}") for c in d.columns if c not in skip])
        keyed.append(x)
    bcols = [f"_b{j}" for j in range(len(by))]
    sizes = [k.groupBy(*bcols).agg(F.max(f"_n{i}").alias(f"_n{i}")) for i, k in enumerate(keyed)]
    skel = reduce(lambda a, b: _full_join_sizes(a, b, bcols), sizes)
    ncols = [f"_n{i}" for i in range(len(dfs))]
    out = skel.select(*bcols, *ncols, F.explode(F.sequence(F.lit(1), F.greatest(*[F.coalesce(F.col(n), F.lit(0))
                                                                                    for n in ncols]))).alias("_k"))
    for i, x in enumerate(keyed):
        r = x.drop(f"_n{i}").select(*[F.col(c).alias(f"{c}_r") if c in bcols else F.col(c) for c in x.columns
                                      if c != f"_n{i}"])
        cond = [out[c].eqNullSafe(r[f"{c}_r"]) for c in bcols] + [F.least(out["_k"], out[f"_n{i}"]) == r[f"_k{i}"]]
        out = out.join(r, cond, "left").drop(*[f"{c}_r" for c in bcols])
        if ins[i]:
            out = out.withColumn(ins[i], F.col(f"_n{i}").isNotNull())
    order: list[str] = []
    for d in dfs:
        order += [c for c in d.columns if c != "_ord" and c not in order]
    sel = []
    for c in order:
        if c in by:
            sel.append(F.col(f"_b{by.index(c)}").alias(c))
            continue
        srcs = [f"{c}__{i}" for i, d in enumerate(dfs) if c in d.columns]
        sel.append((F.coalesce(*[F.col(s) for s in reversed(srcs)]) if len(srcs) > 1 else F.col(srcs[0])).alias(c))
    sel += [F.col(f) for f in ins if f]
    w = Window.orderBy(*bcols, "_k")
    out = out.withColumn("_ord", F.row_number().over(w).cast("long"))
    return out.select(*sel, "_ord")


def _full_join_sizes(a: DataFrame, b: DataFrame, bcols: list[str]) -> DataFrame:
    rb = b.select(*[F.col(c).alias(f"{c}_r") if c in bcols else F.col(c) for c in b.columns])
    j = a.join(rb, [a[c].eqNullSafe(rb[f"{c}_r"]) for c in bcols], "full")
    keep = [F.coalesce(F.col(c), F.col(f"{c}_r")).alias(c) for c in bcols]
    return j.select(*keep, *[c for c in j.columns if c not in bcols and not c.endswith("_r")])


def update(by: list[str], master: DataFrame, trans: DataFrame) -> DataFrame:
    """UPDATE master trans; BY keys;  non-missing transaction values replace master values."""
    vals = [c for c in trans.columns if c not in by + ["_ord"]]
    wl = Window.partitionBy(*by).orderBy("_ord").rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    t = trans.select(*by, *[F.last(F.when(F.col(c).isNotNull() & (F.col(c).cast("string") != ""), F.col(c)),
                                   ignorenulls=True).over(wl).alias(f"{c}__t") for c in vals]).dropDuplicates(by)
    m = master.join(t, by, "full")
    cols = [c for c in master.columns if c != "_ord"] + [c for c in vals if c not in master.columns]
    sel = [F.coalesce(F.col(f"{c}__t"), F.col(c)).alias(c) if c in vals else F.col(c) for c in cols]
    out = m.select(*sel)
    return renumber(out.withColumn("_ord", F.lit(0)), *by)


def freq_out(df: DataFrame, var: str) -> DataFrame:
    """PROC FREQ; TABLES var / OUT= : var COUNT PERCENT (missing levels excluded)."""
    nm = df.where(F.col(var).isNotNull() & (F.col(var) != ""))
    tot = nm.count()
    g = nm.groupBy(var).agg(F.count("*").cast("double").alias("COUNT"))
    g = g.withColumn("PERCENT", F.col("COUNT") * 100.0 / F.lit(float(tot)))
    return renumber(g.withColumn("_ord", F.lit(0)), var)


def missing_char(c):
    return F.col(c).isNull() | (F.trim(F.col(c)) == "")
