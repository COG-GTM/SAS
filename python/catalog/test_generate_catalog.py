"""Tests for generate_catalog.py (stdlib + pytest; no SAS runtime needed)."""

from __future__ import annotations

import csv
import importlib.util
import itertools
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "generate_catalog", HERE / "generate_catalog.py"
)
assert _spec and _spec.loader
gc = importlib.util.module_from_spec(_spec)
sys.modules["generate_catalog"] = gc
_spec.loader.exec_module(gc)


@pytest.fixture(scope="module")
def programs() -> list[dict[str, object]]:
    return gc.build_programs()


@pytest.fixture(scope="module")
def by_key(programs: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(p["key"]): p for p in programs}


def _split(v: object) -> list[str]:
    return [x for x in str(v).split(";") if x]


# --- lexer ----------------------------------------------------------------- #


def test_clean_removes_comments_and_keeps_layout() -> None:
    src = "*a comment;\ndata x; /* block\n comment */ set y;\nx = a * b;\n"
    out = gc.clean(src)
    assert out.text.count("\n") == src.count("\n")
    assert "comment" not in out.text
    assert "x = a * b;" in out.text
    assert out.line_starts_in_code[0] is True


def test_clean_blanks_datalines() -> None:
    src = "data x;\ninput a $;\ndatalines;\nset learn.fake\n*not a comment\n;\nproc print data=x;\nrun;\n"
    out = gc.clean(src)
    assert "learn.fake" not in out.text
    assert "proc print" in out.text
    assert out.datalines_lines == {3, 4, 5}


def test_clean_datalines4_ends_at_four_semicolons() -> None:
    src = "data x;\ninput a $;\ndatalines4;\na;b\n;;;;\nrun;\n"
    out = gc.clean(src)
    assert "a;b" not in out.text
    assert "run;" in out.text


def test_macro_call_without_semicolon_ends_statement() -> None:
    src = "%print_n(learn.bicycles, 4)\n\n*25-5;\nproc print;run;\n"
    out = gc.clean(src)
    assert out.line_starts_in_code[2] is True


def test_split_statements_respects_quotes() -> None:
    stmts = gc.split_statements("title 'a;b';\nproc print;\n", 10)
    assert stmts == [("title 'a;b'", 10), ("proc print", 11)]


def test_sql_sources_parses_aliases_and_commas() -> None:
    stmt = "create table both as select * from learn.health as h, learn.demographic d where h.subj = d.subj"
    assert gc._sql_sources(stmt) == ["learn.health", "learn.demographic"]
    assert gc._sql_sources("select * from one left join two on one.id = two.id") == [
        "one",
        "two",
    ]


def test_names_drops_dataset_options() -> None:
    assert gc._names("learn.a(keep=x y) b (where=(x>1)) end=last") == ["learn.a", "b"]


# --- whole-catalog acceptance --------------------------------------------- #


@pytest.mark.parametrize(
    "prefix,filename",
    [
        ("ed2", "Programs Used in the Second Edition.sas"),
        ("sol", "Solutions_to_Odd_Numbered_problems.sas"),
    ],
)
def test_every_tag_appears_exactly_once(
    programs: list[dict[str, object]], prefix: str, filename: str
) -> None:
    text = gc.read_source(gc.SOURCE_DIR / filename)
    tags = [
        f"{int(a)}-{int(b)}"
        for a, b in re.findall(r"(?m)^\s*\*\s*(\d+)\s*[-.]\s*(\d+)\s*;\s*$", text)
    ]
    ids = [str(p["program_id"]) for p in programs if p["source_file"] == filename]
    assert sorted(ids) == sorted(tags)
    assert len(ids) == len(set(ids))


def test_counts(programs: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for p in programs:
        counts[str(p["source_file"])] = counts.get(str(p["source_file"]), 0) + 1
    assert counts["Programs Used in the Second Edition.sas"] == 331
    assert counts["Solutions_to_Odd_Numbered_problems.sas"] == 119
    assert counts["Create_Datasets.sas"] == 72


def test_keys_unique_and_ranges_disjoint(programs: list[dict[str, object]]) -> None:
    keys = [p["key"] for p in programs]
    assert len(keys) == len(set(keys))
    by_file: dict[str, list[tuple[int, int]]] = {}
    for p in programs:
        by_file.setdefault(str(p["source_file"]), []).append(
            (int(p["start_line"]), int(p["end_line"]))
        )  # type: ignore[arg-type]
    for ranges in by_file.values():
        ranges.sort()
        for (s1, e1), (s2, _) in itertools.pairwise(ranges):
            assert s1 <= e1 < s2


def test_irregular_tags_are_normalised(by_key: dict[str, dict[str, object]]) -> None:
    assert by_key["sol:24-7"]["tag"] == "*24.7;"
    assert by_key["ed2:22-8"]["tag"] == "*22-08;"
    assert "normalised" in str(by_key["sol:24-7"]["notes"])


def test_program_1_1(by_key: dict[str, dict[str, object]]) -> None:
    p = by_key["ed2:1-1"]
    assert _split(p["files_read"]) == ["Data/veggies.txt"]
    assert _split(p["datasets_written"]) == ["veg"]
    assert _split(p["procs"]) == ["PRINT", "FREQ", "MEANS"]
    assert p["chapter"] == "1"


def test_sql_program_reads_learn_tables(by_key: dict[str, dict[str, object]]) -> None:
    p = by_key["ed2:26-4"]
    assert p["proc_sql"] == 1
    assert _split(p["datasets_required"]) == ["learn.health", "learn.demographic"]


def test_feature_flags(by_key: dict[str, dict[str, object]]) -> None:
    assert by_key["sol:25-3"]["macro"] == 1
    assert by_key["sol:24-3"]["retain_by"] == 1
    assert by_key["ed2:15-13"]["user_formats"] == 1
    assert by_key["ed2:6-4"]["ods"] == 1
    assert any(p["prx"] == 1 for p in by_key.values())
    assert any(p["arrays"] == 1 for p in by_key.values())
    assert any(p["sgplot"] == 1 for p in by_key.values())


def test_commented_out_programs_have_no_code(
    by_key: dict[str, dict[str, object]],
) -> None:
    for key in ("ed2:6-1", "ed2:21-8", "sol:1-1"):
        assert by_key[key]["has_code"] == 0
        assert by_key[key]["files_read"] == ""


def test_filename_and_excel_libname(by_key: dict[str, dict[str, object]]) -> None:
    assert _split(by_key["sol:21-9"]["files_read"]) == [
        "Data/xyz1.txt",
        "Data/xyz2.txt",
    ]
    assert "Data/Wages.xls" in _split(by_key["ed2:6-3"]["files_read"])


def test_learn_alias_librefs(by_key: dict[str, dict[str, object]]) -> None:
    assert "learn.survey2018" in _split(by_key["sol:4-3"]["datasets_written"])


def test_create_datasets_untagged_tail(by_key: dict[str, dict[str, object]]) -> None:
    tail = by_key["cd:cd-72"]
    assert tail["tag"] == ""
    assert _split(tail["datasets_written"]) == ["many_one", "many_two", "truncate"]
    assert _split(by_key["cd:cd-71"]["datasets_written"]) == ["learn.grouping"]


def test_datasets_catalog(programs: list[dict[str, object]]) -> None:
    rows = {str(r["name"]): r for r in gc.build_datasets(programs)}
    assert rows["learn.blood"]["producers"] == "cd:cd-52"
    assert "ed2:16-1" in _split(rows["learn.blood"]["consumers"])
    assert rows["one"]["kind"] == "work_shared"
    assert rows["Data/veggies.txt"]["exists"] == 1
    data_files = {
        p.name for p in gc.DATA_DIR.iterdir() if p.is_file() and p.name != "readme.md"
    }
    assert {
        n[len("Data/") :] for n, r in rows.items() if r["kind"] == "data_file"
    } == data_files
    learn = [r for r in rows.values() if r["kind"] == "learn"]
    assert all(r["producers"] for r in learn)


def test_checked_in_csvs_are_current(tmp_path: Path) -> None:
    assert gc.main(["--out-dir", str(tmp_path)]) == 0
    for name in ("programs.csv", "datasets.csv"):
        assert (tmp_path / name).read_text(encoding="utf-8") == (HERE / name).read_text(
            encoding="utf-8"
        ), f"{name} is stale: run python3 python/catalog/generate_catalog.py"
    with (HERE / "programs.csv").open(encoding="utf-8") as fh:
        assert list(csv.DictReader(fh).fieldnames or []) == gc.PROGRAM_FIELDS
