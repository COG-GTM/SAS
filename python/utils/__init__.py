"""
SAS-to-Python utility layer.

This package provides Python equivalents for common SAS functionality:
- sas_formats: PROC FORMAT replication (formats, informats, registry)
- sas_functions: SAS DATA step function equivalents
- io_helpers: Data I/O helpers (libname, INFILE, datalines)
"""

from python.utils.sas_formats import SASFormat, SASInformat, FormatRegistry, default_registry
from python.utils.sas_functions import (
    compress, scan, substr, find, catx, cats, cat,
    sas_mean, sas_sum, sas_round, sas_input, sas_put,
    intck, intnx, mdy, weekday, today,
)
from python.utils.io_helpers import (
    save_dataset, load_dataset, list_datasets,
    read_fwf_sas, read_csv_sas, read_datalines,
)

__all__ = [
    "SASFormat",
    "SASInformat",
    "FormatRegistry",
    "default_registry",
    "compress",
    "scan",
    "substr",
    "find",
    "catx",
    "cats",
    "cat",
    "sas_mean",
    "sas_sum",
    "sas_round",
    "sas_input",
    "sas_put",
    "intck",
    "intnx",
    "mdy",
    "weekday",
    "today",
    "save_dataset",
    "load_dataset",
    "list_datasets",
    "read_fwf_sas",
    "read_csv_sas",
    "read_datalines",
]
