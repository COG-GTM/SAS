from pathlib import Path

import pytest

from sas_examples import config as config_module
from sas_examples.config import (
    DATA_DIR_ENV,
    DEFAULT_DATA_DIR,
    DEFAULT_LEARN_DIR,
    DEFAULT_OUTPUT_DIR,
    LEARN_DIR_ENV,
    OUTPUT_DIR_ENV,
    REPO_ROOT,
    Config,
    data_path,
    get_config,
    learn_path,
    output_path,
    resolve_sas_path,
)


def test_defaults_point_at_repo():
    cfg = get_config()
    assert cfg.data_dir == DEFAULT_DATA_DIR == REPO_ROOT / "Data"
    assert cfg.output_dir == DEFAULT_OUTPUT_DIR == REPO_ROOT / "python" / "output"
    assert cfg.learn_dir == DEFAULT_LEARN_DIR == REPO_ROOT / "python" / "output" / "learn"
    assert (REPO_ROOT / "Example code").is_dir()
    assert cfg.data_dir.is_dir()


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "data"))
    monkeypatch.setenv(LEARN_DIR_ENV, str(tmp_path / "learn"))
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path / "out"))
    assert get_config() == Config(tmp_path / "data", tmp_path / "learn", tmp_path / "out")


def test_outside_checkout_requires_env(monkeypatch, tmp_path):
    monkeypatch.setattr(config_module, "_in_repo_checkout", lambda: False)
    with pytest.raises(RuntimeError, match=DATA_DIR_ENV):
        get_config()
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "data"))
    monkeypatch.setenv(LEARN_DIR_ENV, str(tmp_path / "learn"))
    monkeypatch.setenv(OUTPUT_DIR_ENV, str(tmp_path / "out"))
    assert get_config().data_dir == tmp_path / "data"


def test_data_path_exact():
    assert data_path("blood.txt") == DEFAULT_DATA_DIR / "blood.txt"


def test_data_path_case_insensitive():
    path = data_path("BLOOD.TXT")
    assert path.name == "blood.txt"
    assert path.is_file()


def test_data_path_missing():
    with pytest.raises(FileNotFoundError, match="not found"):
        data_path("no_such_file.txt")


@pytest.mark.parametrize(
    "name", ["", ".", "..", "../README.md", "/etc/passwd", r"..\README.md", "c:x.txt", "sub/a.txt"]
)
def test_data_path_rejects_non_bare_names(name):
    with pytest.raises(ValueError):
        data_path(name)


def test_data_path_ambiguous(tmp_path):
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "A.TXT").write_text("2")
    cfg = Config(tmp_path, tmp_path / "learn", tmp_path / "out")
    if len(list(tmp_path.iterdir())) < 2:
        pytest.skip("case-insensitive filesystem")
    with pytest.raises(FileNotFoundError, match="Ambiguous"):
        data_path("a.Txt", cfg)


def test_learn_path(tmp_path):
    cfg = Config(tmp_path, tmp_path / "learn", tmp_path / "out")
    path = learn_path("Blood", cfg)
    assert path == tmp_path / "learn" / "blood.parquet"
    assert not path.parent.exists()
    learn_path("Blood", cfg, create_dir=True)
    assert path.parent.is_dir()


@pytest.mark.parametrize("name", ["", "../x", "a b", "x.parquet"])
def test_learn_path_rejects_bad_names(name):
    with pytest.raises(ValueError):
        learn_path(name)


def test_output_path(tmp_path):
    cfg = Config(tmp_path, tmp_path / "learn", tmp_path / "out")
    path = output_path("ODS_Example.csv", cfg, create_dir=True)
    assert path == tmp_path / "out" / "ODS_Example.csv"
    assert path.parent.is_dir()
    with pytest.raises(ValueError):
        output_path("../escape.csv", cfg)


@pytest.mark.parametrize(
    ("sas", "mode", "expected"),
    [
        (r"c:\books\learning\survey.txt", "read", DEFAULT_DATA_DIR / "survey.txt"),
        (r"C:\books\Learning\Health.txt", "read", DEFAULT_DATA_DIR / "health.txt"),
        ("c:/books/learning/blood.txt", "read", DEFAULT_DATA_DIR / "blood.txt"),
        (r"C:\books\learning\Mydata", "read", DEFAULT_LEARN_DIR / "mydata.parquet"),
        (r"C:\books\learning\Mydata", "write", DEFAULT_LEARN_DIR / "mydata.parquet"),
        (r"C:\books\learning", "read", DEFAULT_LEARN_DIR),
        (r"C:\books\learning", "write", DEFAULT_OUTPUT_DIR),
        (r"c:\books\learning\\", "write", DEFAULT_OUTPUT_DIR),
        (r"C:\books\learning\ODS_Example.csv", "write", DEFAULT_OUTPUT_DIR / "ODS_Example.csv"),
    ],
)
def test_resolve_sas_path(sas, mode, expected):
    assert resolve_sas_path(sas, mode=mode) == expected


def test_resolve_sas_path_write_never_targets_data_dir():
    assert (DEFAULT_DATA_DIR / "ODS_Example.csv").is_file()
    path = resolve_sas_path(r"C:\books\learning\ODS_Example.csv", mode="write")
    assert DEFAULT_DATA_DIR not in path.parents


@pytest.mark.parametrize(
    "sas",
    [r"d:\other\file.txt", r"c:\books\learning2\blood.txt", r"c:\books\learningx"],
)
def test_resolve_sas_path_rejects_other_roots(sas):
    with pytest.raises(ValueError, match="Not a"):
        resolve_sas_path(sas)


def test_resolve_sas_path_rejects_nested_and_bad_mode():
    with pytest.raises(ValueError, match="Nested"):
        resolve_sas_path(r"c:\books\learning\sub\blood.txt")
    with pytest.raises(ValueError, match="mode"):
        resolve_sas_path(r"c:\books\learning\blood.txt", mode="append")


def test_config_is_path_typed():
    cfg = get_config()
    assert all(isinstance(p, Path) for p in (cfg.data_dir, cfg.learn_dir, cfg.output_dir))
