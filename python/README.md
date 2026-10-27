# sas_examples

Python ports of the programs in *Learning SAS by Example* (`../Example code/`).
The `.sas` sources and `../Data/` are never modified.

## Setup

```bash
pip install -e "python/[dev]"
cd python
pytest
ruff check .
```

## Layout

- `sas_examples/chNN.py` — one module per book chapter; one function per SAS
  program, named `program_<ch>_<n>()` (e.g. `program_3_1()` for `*3-1;`).
- `sas_examples/config.py` — replaces the hard-coded `c:\books\learning` paths.
- `tests/` — pytest suite.

## Paths

All file access goes through `sas_examples.config`:

| Setting    | Default                  | Override env var           |
|------------|--------------------------|----------------------------|
| `data_dir` | `<repo>/Data`            | `SAS_EXAMPLES_DATA_DIR`    |
| `learn_dir`| `<repo>/python/output/learn` | `SAS_EXAMPLES_LEARN_DIR` |

- `data_path("Veggies.txt")` returns the raw file in `data_dir` (matched
  case-insensitively, since the SAS code and `Data/` disagree on case).
- `learn_path("Blood")` returns the Parquet file for the rebuilt `Learn.Blood`
  dataset in `learn_dir`.
- `resolve_sas_path(r"c:\books\learning\survey.txt")` maps a path literal from
  the SAS code to one of the two above.
