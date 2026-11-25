"""Run the PySpark ports on the mock data and write every snapshot to build/pyspark/<case>/<label>.parquet."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cases import CASES  # noqa: E402


def spark_session():
    from pyspark.sql import SparkSession
    return (SparkSession.builder.master("local[2]").appName("sas-parity")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.ansi.enabled", "false")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.ui.enabled", "false")
            .getOrCreate())


def save(df, path: Path):
    cols = [c for c in df.columns if c != "_ord"]
    if "_ord" in df.columns:
        df = df.orderBy("_ord")
    types = {f.name: f.dataType.simpleString() for f in df.schema.fields}
    rows = df.select(*cols).collect()
    arrays, fields = [], []
    for c in cols:
        is_char = types[c] == "string"
        vals = [r[c] for r in rows]
        if is_char:
            arrays.append(pa.array(vals, pa.string()))
        else:
            arrays.append(pa.array([None if v is None else float(v) for v in vals], pa.float64()))
        fields.append({"name": c, "type": "char" if is_char else "num", "spark_type": types[c]})
    t = pa.Table.from_arrays(arrays, names=cols).replace_schema_metadata({"pyspark": json.dumps(fields)})
    pq.write_table(t, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--build", default=str(HERE / "build"))
    a = ap.parse_args()
    build = Path(a.build)
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ["PYTHONPATH"] = os.pathsep.join([str(HERE), os.environ.get("PYTHONPATH", "")])
    spark = spark_session()
    spark.sparkContext.setLogLevel("ERROR")
    from pyspark_ports import ports
    for c in CASES:
        if a.cases and c.id not in a.cases:
            continue
        out = build / "pyspark" / c.id
        out.mkdir(parents=True, exist_ok=True)
        for f in out.glob("*.parquet"):
            f.unlink()
        t0 = time.time()
        err = None
        try:
            dfs = ports.run(c.id, spark, build / "mock")
            for label, df in dfs.items():
                save(df, out / f"{label}.parquet")
        except Exception as e:  # recorded in the report, never hidden
            err = f"{type(e).__name__}: {str(e).splitlines()[0][:300]}"
        res = {"case": c.id, "seconds": round(time.time() - t0, 1), "error": err,
               "datasets": sorted(f.stem for f in out.glob("*.parquet"))}
        (out / "result.json").write_text(json.dumps(res, indent=2))
        print(f"[pyspark] {c.id:<22} {res['seconds']:>6}s datasets={len(res['datasets'])}"
              + (f" ERROR {err}" if err else ""))
    spark.stop()


if __name__ == "__main__":
    main()
