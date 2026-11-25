"""Run the repo's SAS snippets on the blackbox SAS engine against the mock data.

For each case: extract the snippets from the repo's .sas files, point every
C:\\books\\learning path at the mock data / a per-case LEARN library, swap DATALINES
blocks for their mock versions, snapshot the requested datasets after each step into
an output library, then run the program with the engine's sas.exe-compatible CLI.

Engine: set BLACKBOX_SAS to engines/sas/bin/sas of a blackbox-engines checkout
(default ../../blackbox-engines/engines/sas/bin/sas relative to this file).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from cases import CASES, Case, label

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BOOK = REPO / "Example code" / "Programs Used in the Second Edition.sas"
CREATE = REPO / "Example code" / "Create_Datasets.sas"
SECTIONS = {"ch10-setup": "*Programs to create data sets One, Two, and Three;"}


def _read(p: Path) -> list[str]:
    return p.read_text(encoding="latin-1").splitlines()


def extract(step: str) -> str:
    kind, key = step.split(":", 1)
    if kind == "book":
        lines = _read(BOOK)
        start = next(i for i, ln in enumerate(lines) if ln.strip() == f"*{key};")
        stop = re.compile(r"^\*(\d+-\d+|Chapter \d+ Programs|Programs to create);")
    elif kind == "section":
        lines = _read(BOOK)
        start = next(i for i, ln in enumerate(lines) if ln.strip() == SECTIONS[key])
        stop = re.compile(r"^\*\d+-\d+;")
    elif kind == "cd":
        lines = _read(CREATE)
        hits = [i for i, ln in enumerate(lines) if ln.strip().upper() == f"*DATA SET {key.upper()};"]
        start = hits[-1]
        stop = re.compile(r"^\*(Data set|Temporary|Program)", re.I)
    else:
        raise ValueError(step)
    end = next((j for j in range(start + 1, len(lines)) if stop.match(lines[j])), len(lines))
    return "\n".join(lines[start:end]) + "\n"


def mock_datalines(text: str, step: str, mock: Path) -> str:
    key = step.replace(":", "_")
    out, lines, k, i = [], text.split("\n"), 0, 0
    while i < len(lines):
        out.append(lines[i])
        if re.match(r"^\s*(datalines|cards)\s*;\s*$", lines[i], re.I):
            k += 1
            j = i + 1
            while not re.match(r"^\s*;\s*$", lines[j]):
                j += 1
            f = mock / "datalines" / f"{key}__{k}.dat"
            out.extend(f.read_text().rstrip("\n").split("\n") if f.exists() else lines[i + 1:j])
            out.append(";")
            i = j
        i += 1
    return "\n".join(out)


def rewrite_paths(text: str, mock: Path, learn: Path) -> str:
    def repl(m):
        q, rest = m.group(1), m.group(2)
        if rest.strip("\\") == "":
            return f"{q}{learn}{q}"
        return f"{q}{mock / 'raw' / rest.strip(chr(92)).lower()}{q}"
    return re.sub(r"(['\"])[cC]:\\books\\learning((?:\\[^'\"]*)?)\1", repl, text)


def sql_capture(text: str) -> str:
    n = 0

    def fix(stmt: str) -> str:
        nonlocal n
        m = re.match(r"(\s*(?:title[^;]*;\s*)*)\s*select\b", stmt, re.I)
        if m and re.match(r"\s*select\b", stmt[len(m.group(1)):], re.I):
            n += 1
            return f"{m.group(1)}create table _sql{n} as {stmt[len(m.group(1)):].lstrip()}"
        return stmt
    parts = re.split(r"(;)", text)
    return "".join(fix(p) if p != ";" else p for p in parts)


def build_program(case: Case, mock: Path, learn: Path, out: Path) -> str:
    prog = [f"libname learn '{learn}';", f"libname bbout '{out}';", "options fmtsearch=(learn);"]
    for step, snaps in case.steps:
        txt = rewrite_paths(mock_datalines(extract(step), step, mock), mock, learn)
        if case.sql_capture and step.startswith("book:"):
            txt = sql_capture(txt)
        prog.append(f"/* ===== {step} ===== */\n{txt}")
        for ds in snaps:
            src = ds if "." in ds else f"work.{ds}"
            prog.append(f"data bbout.{label(step, ds)}; set {src}; run;")
    return "\n".join(prog) + "\n"


def run_case(case: Case, engine: str, mock: Path, build: Path) -> dict:
    root = build / "sas" / case.id
    shutil.rmtree(root, ignore_errors=True)
    learn, out = root / "learn", root / "out"
    learn.mkdir(parents=True)
    out.mkdir()
    sas = root / f"{case.id}.sas"
    sas.write_text(build_program(case, mock, learn, out))
    t0 = time.time()
    p = subprocess.run([engine, "-sysin", str(sas), "-log", str(root / f"{case.id}.log"),
                        "-print", str(root / f"{case.id}.lst"), "-work", str(root / "work")],
                       cwd=root, capture_output=True, text=True, timeout=1800)
    log = (root / f"{case.id}.log").read_text(errors="replace") if (root / f"{case.id}.log").exists() else ""
    res = {"case": case.id, "rc": p.returncode, "seconds": round(time.time() - t0, 1),
           "errors": [ln for ln in log.splitlines() if ln.startswith("ERROR")][:20],
           "warnings": [ln for ln in log.splitlines() if ln.startswith("WARNING")][:20],
           "datasets": sorted(f.stem for f in out.glob("*.parquet"))}
    (root / "result.json").write_text(json.dumps(res, indent=2))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--engine", default=os.environ.get(
        "BLACKBOX_SAS", str(REPO.parent / "blackbox-engines" / "engines" / "sas" / "bin" / "sas")))
    ap.add_argument("--build", default=str(HERE / "build"))
    a = ap.parse_args()
    build = Path(a.build)
    if not Path(a.engine).exists():
        raise SystemExit(f"blackbox SAS engine not found at {a.engine}; set BLACKBOX_SAS")
    for c in CASES:
        if a.cases and c.id not in a.cases:
            continue
        r = run_case(c, a.engine, build / "mock", build)
        print(f"[sas] {c.id:<22} rc={r['rc']} {r['seconds']:>6}s datasets={len(r['datasets'])} "
              f"errors={len(r['errors'])}")


if __name__ == "__main__":
    main()
