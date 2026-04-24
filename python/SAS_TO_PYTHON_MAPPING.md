# SAS → Python Migration Mapping

Comprehensive reference mapping every SAS construct from *Learning SAS by Example, 2nd Edition* to its Python equivalent.

---

## Data I/O

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `DATA step / INPUT` | `pd.read_csv()`, `pd.read_fwf()` | 1-3 |
| `INFILE … DLM=','` | `pd.read_csv(sep=',')` | 2-3 |
| `INFILE … DSD` | `pd.read_csv(quotechar='"')` | 3 |
| `datalines / cards` | `pd.read_csv(StringIO(text))` | 2-3 |
| Column input (fixed-width) | `pd.read_fwf(colspecs=...)` | 3 |
| `INFILE … MISSOVER` | `pd.read_csv(na_values=...)` | 21 |
| `INFILE … PAD` | `pd.read_fwf()` (default pads short lines) | 21 |
| `OBS= / FIRSTOBS=` | `df.head(n)` / `df.iloc[start:end]` | 21 |
| Multiple obs per line (`@@`) | Split + reshape | 21 |
| Multi-line records (`#n`) | Custom line-pair parsing | 21 |
| `PROC IMPORT DBMS=CSV` | `pd.read_csv()` | 6 |
| `PROC IMPORT DBMS=XLS` | `pd.read_excel(engine='xlrd')` | 6 |
| `PROC IMPORT DBMS=XLSX` | `pd.read_excel(engine='openpyxl')` | 6 |
| `PROC EXPORT DBMS=CSV` | `df.to_csv()` | 6 |
| `PROC EXPORT DBMS=XLSX` | `df.to_excel()` | 6 |

## Data Sets & Libraries

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `LIBNAME` | `pathlib.Path` directories | 4 |
| Permanent data set | `df.to_csv()` / `df.to_parquet()` | 4 |
| `PROC CONTENTS` | `df.dtypes`, `df.info()`, `df.memory_usage()` | 4 |
| `DATA new; SET old;` | `df.copy()` | 4 |
| `KEEP=` / `DROP=` | `df[cols]` / `df.drop(columns=...)` | 10 |

## Formats & Labels

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `PROC FORMAT VALUE` | Python `dict` mapping | 5, 22 |
| `PROC FORMAT INVALUE` | `dict` for reverse lookup | 22 |
| `PROC FORMAT PICTURE` | `f-string` / `str.format()` | 22 |
| `CNTLIN=` / `CNTLOUT=` | Build dict from DataFrame | 22 |
| Multilabel format (`MLF`) | Overlapping bin logic + explode | 22 |
| `PUT(var, fmt.)` | `dict.get()` / `Series.map()` | 5, 11 |
| `INPUT(var, infmt.)` | `pd.to_numeric()` / `pd.to_datetime()` | 11 |
| `LABEL` statement | `df.rename(columns=...)` | 14 |
| `FORMAT var fmt.` | `Series.map(dict)` / `.apply(func)` | 5, 17 |

## Conditional Logic

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `IF … THEN` | `np.where()` / `np.select()` | 7 |
| `IF … THEN DELETE` | `df[mask]` (boolean filter) | 7 |
| `WHERE` | `df.query()` / `df[mask]` | 7, 14 |
| `SELECT / WHEN` | `dict.get()` / `match-case` | 7 |
| `IN (val1, val2)` | `Series.isin([...])` | 7 |

## Iterative Processing

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `DO i = 1 TO n` | `for i in range(1, n+1)` | 8 |
| `DO i = 1 TO n BY 2` | `range(1, n+1, 2)` | 8 |
| `DO WHILE (cond)` | `while cond:` | 8 |
| `DO UNTIL (cond)` | `while True: ... if cond: break` | 8 |
| `LEAVE` | `break` | 8 |
| `CONTINUE` | `continue` | 8 |
| Nested `DO` loops | Nested `for` loops | 8 |
| `RETAIN` | `cumsum()`, `shift()`, closure variables | 8, 24 |

## Date Handling

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| SAS date values | `pd.Timestamp` / `datetime.date` | 9 |
| Date informats (`mmddyy10.`) | `pd.to_datetime(format=...)` | 9 |
| `YRDIF(start, end)` | `(end - start).days / 365.25` | 9 |
| `INTCK('month', d1, d2)` | `relativedelta` / `dt.month` arithmetic | 9 |
| `INTNX('month', d, n)` | `pd.offsets.MonthBegin(n)` / `relativedelta(months=n)` | 9 |
| `MDY(m, d, y)` | `pd.to_datetime({'year':…, 'month':…, 'day':…})` | 9 |
| `WEEKDAY()` | `dt.dayofweek` | 9 |
| `TODAY()` | `pd.Timestamp.today()` | 9 |

## Combining Data

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `SET ds1 ds2` (append) | `pd.concat([df1, df2])` | 10 |
| `SET ds1 ds2; BY var` (interleave) | `pd.concat().sort_values()` | 10 |
| `MERGE ds1 ds2; BY var` | `pd.merge(on=..., how=...)` | 10 |
| `IN=` flags | `merge(indicator=True)` | 10 |
| Inner join | `merge(how='inner')` | 10, 26 |
| Left/Right/Full join | `merge(how='left'/'right'/'outer')` | 10, 26 |
| `UPDATE master trans` | `df.set_index().update()` | 10 |
| `RENAME=` | `df.rename(columns={...})` | 10 |

## Functions

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `INT()` | `int()` / `Series.astype(int)` | 11 |
| `ROUND()` | `round()` / `Series.round()` | 11 |
| `CEIL()` | `np.ceil()` | 11 |
| `ABS()`, `SQRT()`, `EXP()`, `LOG()` | `np.abs()`, `np.sqrt()`, `np.exp()`, `np.log()` | 11 |
| `N()`, `MEAN()`, `MIN()`, `MAX()` | `.count()`, `.mean()`, `.min()`, `.max()` (axis=1) | 11 |
| `LARGEST(n, of vars)` | `nlargest()` | 11 |
| `LAG()`, `DIF()` | `Series.shift()`, `Series.diff()` | 11 |
| `RAND('uniform')` | `np.random.default_rng()` | 11 |
| `UPCASE()` / `LOWCASE()` / `PROPCASE()` | `.str.upper()` / `.str.lower()` / `.str.title()` | 12 |
| `COMPRESS()` | `.str.replace(regex)` | 12 |
| `FIND()` / `FINDW()` | `.str.contains()` / `.str.find()` | 12 |
| `SCAN()` | `.str.split().str[n]` | 12 |
| `SUBSTR()` | `.str[start:end]` | 12 |
| `TRANSLATE()` | `str.maketrans()` + `.translate()` | 12 |
| `TRANWRD()` | `.str.replace()` | 12 |
| `SPEDIS()` | `difflib.SequenceMatcher` | 12, 26 |
| `CAT()` / `CATS()` / `CATX()` | `+` / `.strip()+` / `" ".join()` | 12 |

## Arrays

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `ARRAY vars{n}` | Column list: `[f"col{i}" for i in range(n)]` | 13 |
| `_CHARACTER_` array | `df.select_dtypes(include='object').columns` | 13 |
| `_TEMPORARY_` array | Python list / dict (answer key) | 13 |
| 2D temporary array | `dict[(row, col)]` lookup | 13 |
| Array DO loop | `df[cols].apply(func, axis=1)` or vectorized | 13 |

## Procedures

| SAS Procedure | Python Equivalent | Chapter |
|---|---|---|
| `PROC PRINT` | `print(df.to_string())` / `display(df)` | 14 |
| `PROC SORT` | `df.sort_values()` | 14 |
| `PROC REPORT` | `groupby().agg()` + custom formatting | 15 |
| `PROC MEANS` | `df.describe()`, `df.agg()`, `groupby().agg()` | 16 |
| `PROC FREQ` | `value_counts()`, `pd.crosstab()` | 17 |
| `PROC TABULATE` | `pd.pivot_table()`, `pd.crosstab()` | 18 |
| `PROC UNIVARIATE` | `scipy.stats`, `nsmallest/nlargest` | 19 |
| `PROC TTEST` | `scipy.stats.ttest_ind()` | 19 |
| `PROC TRANSPOSE` | `pd.melt()` (wide→long), `df.pivot()` (long→wide) | 23 |
| `PROC SQL` | `pd.merge()`, `df.query()`, `sqlite3` | 26 |

## Output & Graphics

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `ODS HTML` | `df.to_html()` | 19 |
| `ODS SELECT` | Select specific output programmatically | 19 |
| `ODS OUTPUT` | Store results in DataFrame | 19 |
| `PROC SGPLOT / VBAR` | `matplotlib` bar chart | 20 |
| `PROC SGPLOT / HBAR` | `matplotlib` horizontal bar | 20 |
| `PROC SGPLOT / SCATTER` | `plt.scatter()` / `sns.scatterplot()` | 20 |
| `PROC SGPLOT / REG` | `sns.regplot()` | 20 |
| `PROC SGPLOT / SERIES` | `plt.plot()` | 20 |
| `PROC SGPLOT / HISTOGRAM` | `plt.hist()` + `scipy.stats.norm.pdf()` | 20 |
| `PROC SGPLOT / HBOX` | `plt.boxplot()` | 20 |
| `PROC SGPLOT / LOESS` | `sns.regplot(lowess=True)` | 20 |

## Advanced Topics

| SAS Construct | Python Equivalent | Chapter |
|---|---|---|
| `FIRST.var` / `LAST.var` | `groupby().first()` / `.last()`, `.head(1)` / `.tail(1)` | 24 |
| Visit counting | `groupby().size()` | 24 |
| Visit-to-visit diff | `groupby().diff()` | 24 |
| `%LET` | Python variable | 25 |
| `%MACRO / %MEND` | `def function():` | 25 |
| `&macro_var` | f-string: `f"...{var}..."` | 25 |
| `CALL SYMPUTX` | Store in Python variable | 25 |
| `PROC SQL` joins | `pd.merge()` | 26 |
| `PROC SQL` subqueries | Chained pandas / `sqlite3` | 26 |
| `PRXMATCH` / `PRXPARSE` | `re.compile()` + `re.match()` | 27 |
| `PRXCHANGE` | `re.sub()` | 27 |
| Perl regex patterns | `re` module / `Series.str` regex | 27 |
