from pathlib import Path

import pytest

from sas_examples.config import (
    DATA_DIR_ENV,
    DEFAULT_DATA_DIR,
    DEFAULT_LEARN_DIR,
    LEARN_DIR_ENV,
    REPO_ROOT,
    Config,
    data_path,
    get_config,
    learn_path,
    resolve_sas_path,
)


def test_defaults_point_at_repo():
    cfg = get_config()
    assert cfg.data_dir == DEFAULT_DATA_DIR == REPO_ROOT / "Data"
    assert cfg.learn_dir == DEFAULT_LEARN_DIR == REPO_ROOT / "python" / "output" / "learn"
    assert (REPO_ROOT / "Example code").is_dir()
    assert cfg.data_dir.is_dir()


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "data"))
    monkeypatch.setenv(LEARN_DIR_ENV, str(tmp_path / "learn"))
    assert get_config() == Config(tmp_path / "data", tmp_path / "learn")


def test_data_path_exact():
    assert data_path("blood.txt") == DEFAULT_DATA_DIR / "blood.txt"


def test_data_path_case_insensitive():
    path = data_path("BLOOD.TXT")
    assert path.name == "blood.txt"
    assert path.is_file()


def test_data_path_missing():
    with pytest.raises(FileNotFoundError, match="not found"):
        data_path("no_such_file.txt")


def test_data_path_ambiguous(tmp_path):
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "A.TXT").write_text("2")
    cfg = Config(tmp_path, tmp_path / "learn")
    if len(list(tmp_path.iterdir())) < 2:
        pytest.skip("case-insensitive filesystem")
    with pytest.raises(FileNotFoundError, match="Ambiguous"):
        data_path("a.Txt", cfg)


def test_learn_path(tmp_path):
    cfg = Config(tmp_path, tmp_path / "learn")
    path = learn_path("Blood", cfg)
    assert path == tmp_path / "learn" / "blood.parquet"
    assert not path.parent.exists()
    learn_path("Blood", cfg, create_dir=True)
    assert path.parent.is_dir()


@pytest.mark.parametrize("name", ["", "../x", "a b", "x.parquet"])
def test_learn_path_rejects_bad_names(name):
    with pytest.raises(ValueError):
        learn_path(name)


@pytest.mark.parametrize(
    ("sas", "expected"),
    [
        (r"c:\books\learning\survey.txt", DEFAULT_DATA_DIR / "survey.txt"),
        (r"C:\books\Learning\Health.txt", DEFAULT_DATA_DIR / "health.txt"),
        (r"C:\books\learning\Mydata", DEFAULT_LEARN_DIR / "mydata.parquet"),
        (r"C:\books\learning", DEFAULT_LEARN_DIR),
        ("c:/books/learning/blood.txt", DEFAULT_DATA_DIR / "blood.txt"),
    ],
)
def test_resolve_sas_path(sas, expected):
    assert resolve_sas_path(sas) == expected


def test_resolve_sas_path_rejects_other_roots():
    with pytest.raises(ValueError):
        resolve_sas_path(r"d:\other\file.txt")


def test_config_is_path_typed():
    cfg = get_config()
    assert isinstance(cfg.data_dir, Path)
    assert isinstance(cfg.learn_dir, Path)
