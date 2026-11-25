"""Compare blackbox-SAS snapshots with PySpark snapshots and write the parity report.

Checks per dataset: presence, schema (variable names case-insensitively, char/num types,
variable order), row count, and row-level values (char: trailing blanks ignored, missing
char == ''; num: |a-b| <= ABS_TOL + REL_TOL*|a|, missing == missing). Datasets listed as
unordered in cases.py are compared as sorted multisets.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pyarrow.parquet as pq

from cases import CASES, label
from sasread import read_sas
from triage import NOTES

HERE = Path(__file__).resolve().parent
ABS_TOL, REL_TOL = 1e-9, 1e-9
MAX_EXAMPLES = 3


def read_spark(path: Path):
    t = pq.read_table(path)
    fields = json.loads(t.schema.metadata[b"pyspark"])
    d = t.to_pydict()
    rows = [{f["name"]: d[f["name"]][i] for f in fields} for i in range(t.num_rows)]
    return fields, rows


def norm(v, typ):
    if typ == "char":
        return "" if v is None else str(v).rstrip()
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v)


def same(a, b, typ):
    if typ == "char" or a is None or b is None:
        return a == b
    return abs(a - b) <= ABS_TOL + REL_TOL * max(abs(a), abs(b))


def sort_key(row):
    return tuple((0, "") if v is None else (1, v) if isinstance(v, float) else (2, v) for v in row)


def compare(sas_p: Path, spk_p: Path, unordered: bool) -> dict:
    r: dict = {"status": "PASS", "issues": []}
    if not sas_p.exists():
        r.update(status="MISSING_SAS")
        return r
    if not spk_p.exists():
        r.update(status="MISSING_PYSPARK")
        return r
    scols, srows = read_sas(sas_p)
    pcols, prows = read_spark(spk_p)
    r["rows_sas"], r["rows_pyspark"] = len(srows), len(prows)
    r["cols_sas"], r["cols_pyspark"] = len(scols), len(pcols)
    sl = {c["name"].lower(): c for c in scols}
    pl = {c["name"].lower(): c for c in pcols}
    only_s, only_p = [c for c in sl if c not in pl], [c for c in pl if c not in sl]
    if only_s or only_p:
        r["issues"].append(f"columns only in SAS: {[sl[c]['name'] for c in only_s]}, "
                           f"only in PySpark: {[pl[c]['name'] for c in only_p]}")
    common = [c for c in sl if c in pl]
    tdiff = [c for c in common if sl[c]["type"] != pl[c]["type"]]
    if tdiff:
        r["issues"].append("type differs: " + ", ".join(f"{sl[c]['name']} SAS={sl[c]['type']} PySpark={pl[c]['type']}"
                                                        for c in tdiff))
    if [c for c in sl if c in pl] != [c for c in pl if c in sl]:
        r["issues"].append(f"variable order differs: SAS={[c['name'] for c in scols]} "
                           f"PySpark={[c['name'] for c in pcols]}")
    if len(srows) != len(prows):
        r["issues"].append(f"row count SAS={len(srows)} PySpark={len(prows)}")
    cmp_cols = [c for c in common if c not in tdiff]
    S = [[norm(row[sl[c]["name"]], sl[c]["type"]) for c in cmp_cols] for row in srows]
    P = [[norm(row[pl[c]["name"]], sl[c]["type"]) for c in cmp_cols] for row in prows]
    if unordered:
        S, P = sorted(S, key=sort_key), sorted(P, key=sort_key)
    bad_rows, per_col = 0, {}
    for i in range(min(len(S), len(P))):
        row_bad = False
        for j, c in enumerate(cmp_cols):
            if not same(S[i][j], P[i][j], sl[c]["type"]):
                row_bad = True
                e = per_col.setdefault(sl[c]["name"], {"count": 0, "examples": []})
                e["count"] += 1
                if len(e["examples"]) < MAX_EXAMPLES:
                    e["examples"].append({"row": i + 1, "sas": S[i][j], "pyspark": P[i][j]})
        bad_rows += row_bad
    r["rows_compared"] = min(len(S), len(P))
    r["cells_compared"] = r["rows_compared"] * len(cmp_cols)
    r["mismatched_rows"], r["mismatches"] = bad_rows, per_col
    if per_col:
        r["issues"].append(f"{bad_rows} row(s) with value differences in {', '.join(per_col)}")
    if r["issues"]:
        r["status"] = "DIFF"
    return r


def fmt(v):
    if v is None:
        return "."
    if isinstance(v, float):
        return f"{v:.10g}"
    return repr(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=str(HERE / "build"))
    ap.add_argument("--report", default=str(HERE / "PARITY_REPORT.md"))
    ap.add_argument("cases", nargs="*", help="case ids (default: all); must match the runs being compared")
    a = ap.parse_args()
    build = Path(a.build)
    results = []
    for c in CASES:
        if a.cases and c.id not in a.cases:
            continue
        sres = json.loads((build / "sas" / c.id / "result.json").read_text())
        log = build / "sas" / c.id / f"{c.id}.log"
        sres["invalid_data_notes"] = log.read_text().count("NOTE: Invalid data") if log.exists() else 0
        pres = json.loads((build / "pyspark" / c.id / "result.json").read_text())
        ds = []
        for step, snaps in c.steps:
            for d in snaps:
                lb = label(step, d)
                r = compare(build / "sas" / c.id / "out" / f"{lb}.parquet",
                            build / "pyspark" / c.id / f"{lb}.parquet", lb in c.unordered)
                r.update(label=lb, step=step, dataset=d, unordered=lb in c.unordered)
                note = NOTES.get(lb)
                if note and r["status"] == "DIFF":
                    r["classification"], r["explanation"] = note
                elif r["status"] == "DIFF":
                    r["classification"], r["explanation"] = "UNTRIAGED", ""
                ds.append(r)
        results.append({"case": c, "sas": sres, "pyspark": pres, "datasets": ds})
    (build / "parity_results.json").write_text(json.dumps(
        [{"case": x["case"].id, "sas": x["sas"], "pyspark": x["pyspark"],
          "datasets": x["datasets"]} for x in results], indent=2, default=str))
    Path(a.report).write_text(render(results))
    summary(results)


def summary(results):
    tot = {"PASS": 0, "DIFF": 0, "MISSING_SAS": 0, "MISSING_PYSPARK": 0}
    print(f"{'case':<22} {'datasets':>8} {'pass':>5} {'diff':>5} {'miss':>5}  rows(SAS)  cells compared")
    for x in results:
        d = x["datasets"]
        p = sum(r["status"] == "PASS" for r in d)
        f = sum(r["status"] == "DIFF" for r in d)
        m = len(d) - p - f
        for r in d:
            tot[r["status"]] += 1
        print(f"{x['case'].id:<22} {len(d):>8} {p:>5} {f:>5} {m:>5}  {sum(r.get('rows_sas', 0) for r in d):>9}"
              f"  {sum(r.get('cells_compared', 0) for r in d):>14}")
    n = sum(tot.values())
    print(f"TOTAL: {n} datasets, {tot['PASS']} PASS, {tot['DIFF']} DIFF, "
          f"{tot['MISSING_SAS'] + tot['MISSING_PYSPARK']} missing")


def render(results) -> str:
    from report import render_report
    return render_report(results, fmt)


if __name__ == "__main__":
    main()
