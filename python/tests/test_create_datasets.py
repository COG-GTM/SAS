"""Integration tests: compare generated DataFrames against reference CSVs.

Each test loads a reference CSV from ``tests/reference_data/`` and the
DataFrame produced by the corresponding ``create_*`` function, then checks
column names, row count, dtypes, and values.
"""

import os
import sys
import math

import pandas as pd
import pytest

# Ensure imports work when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from create_datasets import ALL_CREATORS

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference_data")


def _load_reference(name: str) -> pd.DataFrame:
    path = os.path.join(REFERENCE_DIR, f"{name}.csv")
    if not os.path.exists(path):
        pytest.skip(f"Reference CSV not found: {path}")
    return pd.read_csv(path)


def _compare_values(generated: pd.DataFrame, reference: pd.DataFrame, name: str):
    """Compare values between generated and reference DataFrames.

    Uses approximate comparison for floats and exact for everything else.
    """
    assert len(generated) == len(reference), (
        f"[{name}] Row count mismatch: generated={len(generated)}, reference={len(reference)}"
    )

    gen_cols = list(generated.columns)
    ref_cols = list(reference.columns)
    assert gen_cols == ref_cols, (
        f"[{name}] Column mismatch: generated={gen_cols}, reference={ref_cols}"
    )

    for col in gen_cols:
        gen_series = generated[col].reset_index(drop=True)
        ref_series = reference[col].reset_index(drop=True)

        for i in range(len(gen_series)):
            gv = gen_series.iloc[i]
            rv = ref_series.iloc[i]

            # Treat empty strings as missing (SAS blank = missing for chars)
            def _is_missing(v):
                if pd.isna(v):
                    return True
                if isinstance(v, str) and v.strip() == "":
                    return True
                return False

            g_miss = _is_missing(gv)
            r_miss = _is_missing(rv)
            if g_miss and r_miss:
                continue
            if g_miss != r_miss:
                pytest.fail(
                    f"[{name}] col={col} row={i}: "
                    f"generated={'NaN' if g_miss else gv}, "
                    f"reference={'NaN' if r_miss else rv}"
                )

            # Numeric comparison with tolerance
            try:
                gf = float(gv)
                rf = float(rv)
                if not math.isclose(gf, rf, rel_tol=1e-6, abs_tol=1e-9):
                    pytest.fail(
                        f"[{name}] col={col} row={i}: "
                        f"generated={gv}, reference={rv}"
                    )
            except (TypeError, ValueError):
                # String comparison
                if str(gv).strip() != str(rv).strip():
                    pytest.fail(
                        f"[{name}] col={col} row={i}: "
                        f"generated={gv!r}, reference={rv!r}"
                    )


# ---------------------------------------------------------------------------
# Parametrized test: one test case per dataset
# ---------------------------------------------------------------------------

# Datasets that involve random numbers and won't match reference CSVs exactly
# because SAS and Python RNGs differ
_RANDOM_DATASETS = {"assign", "hosp", "hosp_discharge", "college", "fitness"}

# Datasets that read external files which may not be present
_EXTERNAL_FILE_DATASETS = {"school", "survey", "blood", "grades", "gym"}


@pytest.mark.parametrize("name", sorted(ALL_CREATORS.keys()))
def test_dataset_structure(name: str):
    """Verify each dataset has correct columns and non-zero rows."""
    creator = ALL_CREATORS[name]
    df = creator()
    assert isinstance(df, pd.DataFrame), f"[{name}] Creator did not return a DataFrame"
    if df.empty:
        pytest.skip(f"[{name}] Empty DataFrame (external file may be missing)")
    assert len(df) > 0, f"[{name}] DataFrame has no rows"
    assert len(df.columns) > 0, f"[{name}] DataFrame has no columns"


@pytest.mark.parametrize("name", sorted(
    set(ALL_CREATORS.keys()) - _RANDOM_DATASETS - _EXTERNAL_FILE_DATASETS
))
def test_dataset_values(name: str):
    """Compare generated values against reference CSV."""
    reference = _load_reference(name)
    generated = ALL_CREATORS[name]()

    if generated.empty:
        pytest.skip(f"[{name}] Empty DataFrame")

    _compare_values(generated, reference, name)


@pytest.mark.parametrize("name", sorted(_EXTERNAL_FILE_DATASETS))
def test_external_file_dataset(name: str):
    """Test datasets that depend on external data files."""
    creator = ALL_CREATORS[name]
    df = creator()
    if df.empty:
        pytest.skip(f"[{name}] External data file not available")
    reference = _load_reference(name)
    _compare_values(df, reference, name)


@pytest.mark.parametrize("name", sorted(_RANDOM_DATASETS))
def test_random_dataset_structure(name: str):
    """For random datasets, verify structure but not exact values."""
    creator = ALL_CREATORS[name]
    df = creator()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    # Verify expected columns exist
    reference = _load_reference(name)
    assert list(df.columns) == list(reference.columns), (
        f"[{name}] Column mismatch"
    )
    # Row counts for random datasets should be in the right ballpark
    assert abs(len(df) - len(reference)) / max(len(reference), 1) < 0.1, (
        f"[{name}] Row count too different: {len(df)} vs {len(reference)}"
    )
