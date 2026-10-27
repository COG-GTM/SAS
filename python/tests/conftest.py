import pytest

from sas_examples.config import DATA_DIR_ENV, LEARN_DIR_ENV


@pytest.fixture(autouse=True)
def _default_paths(monkeypatch):
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.delenv(LEARN_DIR_ENV, raising=False)
