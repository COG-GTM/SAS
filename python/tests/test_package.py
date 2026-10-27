import importlib

import pytest

import sas_examples

CHAPTERS = range(1, 28)


@pytest.mark.parametrize("chapter", CHAPTERS)
def test_chapter_module_imports(chapter):
    module = importlib.import_module(f"sas_examples.ch{chapter:02d}")
    assert module.__doc__


def test_chapter_functions_follow_naming():
    for chapter in CHAPTERS:
        module = importlib.import_module(f"sas_examples.ch{chapter:02d}")
        for name in dir(module):
            if name.startswith("program_"):
                assert name.startswith(f"program_{chapter}_"), f"{module.__name__}.{name}"


def test_public_api():
    assert set(sas_examples.__all__) <= set(dir(sas_examples))


@pytest.mark.parametrize(
    "module",
    [
        "pandas",
        "numpy",
        "pyarrow",
        "duckdb",
        "openpyxl",
        "xlrd",
        "scipy",
        "statsmodels",
        "matplotlib",
        "jinja2",
    ],
)
def test_dependency_importable(module):
    importlib.import_module(module)


def test_parquet_and_duckdb_roundtrip(tmp_path):
    import duckdb
    import pandas as pd

    from sas_examples.config import Config, learn_path

    cfg = Config(tmp_path, tmp_path / "learn")
    path = learn_path("Demo", cfg, create_dir=True)
    pd.DataFrame({"x": [1, 2, 3], "g": ["a", "b", "a"]}).to_parquet(path)
    result = duckdb.sql(
        f"select g, sum(x) as total from read_parquet('{path}') group by g order by g"
    ).df()
    assert result.to_dict("list") == {"g": ["a", "b"], "total": [4, 2]}
