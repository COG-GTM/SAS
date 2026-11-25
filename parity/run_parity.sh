#!/usr/bin/env bash
# One command: mock data -> blackbox SAS engine -> PySpark ports -> comparison -> PARITY_REPORT.md
# Usage: BLACKBOX_SAS=/path/to/blackbox-engines/engines/sas/bin/sas parity/run_parity.sh [case ...]
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" mockgen.py
"$PY" sas_runner.py "$@"
"$PY" run_pyspark.py "$@" 2> build/pyspark.stderr.log
"$PY" compare.py "$@"
"$PY" render_summary.py
echo "report: $(pwd)/PARITY_REPORT.md"
