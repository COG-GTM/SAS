"""Render build/parity_summary.png (per-case PASS/DIFF bar chart + totals) from build/parity_results.json."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent


def main():
    res = json.loads((HERE / "build" / "parity_results.json").read_text())
    names = [x["case"] for x in res]
    st = {k: [sum(r["status"] == k for r in x["datasets"]) for x in res] for k in ("PASS", "DIFF")}
    st["MISSING"] = [len(x["datasets"]) - p - d for x, p, d in zip(res, st["PASS"], st["DIFF"])]
    fig, ax = plt.subplots(figsize=(11, 7))
    left = [0] * len(res)
    for k, colr in (("PASS", "#2e7d32"), ("DIFF", "#e65100"), ("MISSING", "#9e9e9e")):
        ax.barh(names, st[k], left=left, color=colr, label=k)
        left = [a + b for a, b in zip(left, st[k])]
    ax.invert_yaxis()
    ax.set_xlabel("datasets compared")
    tot = {k: sum(v) for k, v in st.items()}
    cells = sum(r.get("cells_compared", 0) for x in res for r in x["datasets"])
    ax.set_title(f"Blackbox SAS engine vs PySpark — {sum(len(x['datasets']) for x in res)} datasets, "
                 f"{tot['PASS']} PASS / {tot['DIFF']} DIFF / {tot['MISSING']} missing, {cells:,} cells compared")
    for i, x in enumerate(res):
        diffs = [r["label"] for r in x["datasets"] if r["status"] != "PASS"]
        if diffs:
            ax.text(left[i] + 0.1, i, ", ".join(diffs), va="center", fontsize=7)
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_xlim(0, max(left) + 4)
    fig.tight_layout()
    out = HERE / "parity_summary.png"
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
