# SAS → Python Migration

Python equivalents for every program in *Learning SAS by Example, 2nd Edition* by Ron Cody.

## Quick Start

```bash
cd python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run all chapter examples
python -m chapters.ch01_introduction
python -m chapters.ch20_sgplot       # generates plots in python/output/

# Run tests
pytest tests/ -v
```

## Structure

```
python/
├── chapters/          # One module per chapter (ch01–ch27)
├── utils/
│   ├── data_helpers.py   # Path helpers, I/O utilities
│   └── formats.py        # SAS PROC FORMAT → Python dicts
├── tests/
│   └── test_datasets.py  # Unit tests (pytest)
├── create_datasets.py    # All 30+ in-memory datasets
├── solutions_odd_numbered.py
├── requirements.txt
└── SAS_TO_PYTHON_MAPPING.md   # Full SAS → Python reference
```

## Coverage

| Chapters | Topic | Module |
|---|---|---|
| 1-5 | Data I/O, formats, labels | `ch01` – `ch05` |
| 6-10 | Excel, conditionals, loops, dates, merging | `ch06` – `ch10` |
| 11-15 | Functions, arrays, PROC PRINT/REPORT | `ch11` – `ch15` |
| 16-20 | MEANS, FREQ, TABULATE, ODS, SGPLOT | `ch16` – `ch20` |
| 21-27 | Advanced I/O, formats, reshape, macros, SQL, regex | `ch21` – `ch27` |

See [`SAS_TO_PYTHON_MAPPING.md`](SAS_TO_PYTHON_MAPPING.md) for the complete construct-by-construct reference.
