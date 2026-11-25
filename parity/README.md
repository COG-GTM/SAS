# SAS → PySpark parity harness

Runs a representative set of the book's programs (`Example code/Programs Used in the Second Edition.sas`,
plus the dataset-creation blocks of `Example code/Create_Datasets.sas` they depend on) on the **blackbox SAS
engine** against deterministic mock inputs, runs hand-written **PySpark ports** of the same programs on the same
inputs, and compares every output dataset (schema, row count, row-level values with numeric tolerance).
The result is [`PARITY_REPORT.md`](PARITY_REPORT.md) plus `parity_summary.png`.

## One command

```sh
python3 -m venv ~/venvs/sasparity && . ~/venvs/sasparity/bin/activate
pip install -r parity/requirements.txt          # needs Java 11/17 on PATH for Spark
export BLACKBOX_SAS=/path/to/blackbox-engines/engines/sas/bin/sas
parity/run_parity.sh                            # or: parity/run_parity.sh ch09_dates ch12_strings
```

Steps it runs (each also works on its own):

| Step | Script | Output |
|---|---|---|
| 1. mock inputs (seed `20261125`) | `mockgen.py` | `build/mock/raw/*` (files the book reads with INFILE), `build/mock/datalines/*` (replacement DATALINES blocks) |
| 2. SAS on the blackbox engine | `sas_runner.py` | `build/sas/<case>/` — generated `.sas`, `.log`, `.lst`, `out/*.parquet`, `result.json` |
| 3. PySpark ports | `run_pyspark.py` (+ `pyspark_ports/`) | `build/pyspark/<case>/*.parquet`, `result.json` |
| 4. compare + report | `compare.py`, `report.py`, `triage.py` | `build/parity_results.json`, `PARITY_REPORT.md` |
| 5. chart | `render_summary.py` | `parity_summary.png` |

Harness unit tests (no engine or Spark needed): `python3 -m unittest discover -s parity/tests`.

## How it works

* `cases.py` is the registry: each case is a list of book programs (`book:7-3`), `Create_Datasets.sas` blocks
  (`cd:BLOOD`) and the datasets to snapshot after each step. One case = one SAS session.
* `sas_runner.py` extracts each program by its `*n-m;` marker, replaces DATALINES with the mock files, rewrites
  `C:\books\learning\...` paths to the mock data / a per-case `learn` library, appends
  `data bbout.<label>; set <ds>; run;` snapshots, and calls
  `$BLACKBOX_SAS -sysin prog.sas -log prog.log -print prog.lst -work <dir>`.
* `pyspark_ports/sasspark.py` holds the SAS semantics the ports need (list/column/formatted input, informats,
  missing-value rules, SAS dates, RETAIN/LAG/FIRST./LAST. via windows, SET/MERGE/UPDATE, PROC MEANS/FREQ/
  TRANSPOSE output shapes). Row order is carried in an explicit `_ord` column so observation order is compared.
* `compare.py` reads the engine's Parquet (SAS names/types from the `sas` schema metadata), matches columns
  case-insensitively, compares chars after removing trailing blanks and numbers with
  `|a-b| <= 1e-9 + 1e-9*max(|a|,|b|)`. `triage.py` records the classification of each known difference; the
  report only shows a note when that dataset actually differs in the latest run.

## Getting the blackbox engine (not committed here)

The engine is a separate clean-room SAS interpreter (`blackbox-engines` repository, `engines/sas`). Do not copy
its source into this repo. Either:

1. **Source checkout / archive** — obtain `blackbox-engines` (git clone or the `blackbox-engines-main.zip`
   archive from its owner), unpack it *outside* this repo, install its runtime deps
   (`pip install <blackbox-engines>/engines/bteq numpy scipy pyarrow pyreadstat openpyxl duckdb`, matching
   `engines/sas/Dockerfile`), then `export BLACKBOX_SAS=<blackbox-engines>/engines/sas/bin/sas`.
2. **Container** — `python3 tools/containers.py build sas` in the engine checkout (or pull
   `ghcr.io/iancmoritz/blackbox-sas` if you have access), then point `BLACKBOX_SAS` at a wrapper:
   ```sh
   #!/bin/sh
   exec docker run --rm --user "$(id -u):$(id -g)" -v /:/host -w "/host$PWD" blackbox-sas "$@"
   ```
   (paths passed by the runner are absolute, so mount them at the same location, e.g. `-v "$HOME:$HOME"`).

The report in this directory was produced with option 1 (Python 3.12, PySpark 3.5.3, OpenJDK 17).
