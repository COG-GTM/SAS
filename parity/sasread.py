"""Read blackbox-engine Parquet datasets back into logical SAS columns."""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq


def read_sas(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (columns, rows). columns: [{name,type,length,format}], rows: list of dicts."""
    t = pq.read_table(path)
    meta = json.loads((t.schema.metadata or {}).get(b"sas", b"{}"))
    vars_ = meta.get("columns")
    if not vars_:
        raise ValueError(f"{path}: no sas metadata")
    cols = []
    for i, v in enumerate(vars_):
        cols.append({"name": v.get("name"), "type": "char" if v.get("type") in ("char", "C", 2, "$") else "num",
                     "length": v.get("length"), "format": v.get("format"),
                     "phys": t.schema.names[i]})
    data = t.to_pydict()
    rows = [{c["name"]: data[c["phys"]][r] for c in cols} for r in range(t.num_rows)]
    return cols, rows
