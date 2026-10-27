#!/usr/bin/env python3
"""Generate programs.csv and datasets.csv from the SAS sources in ``Example code/``.

Standard library only. Run from anywhere::

    python3 python/catalog/generate_catalog.py

The parser is a static scanner, not a SAS interpreter: it strips comments and
DATALINES blocks, splits the remaining code into statements and looks for the
statements that read or write data (DATA/SET/MERGE/INFILE/PROC ... DATA= / OUT=,
PROC SQL FROM/JOIN/CREATE TABLE, ODS OUTPUT, LIBNAME, FILENAME).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "Example code"
DATA_DIR = REPO_ROOT / "Data"
OUT_DIR = Path(__file__).resolve().parent

SOURCES = (
    ("cd", "Create_Datasets.sas"),
    ("ed2", "Programs Used in the Second Edition.sas"),
    ("sol", "Solutions_to_Odd_Numbered_problems.sas"),
)

LEARN_PATH = r"c:\books\learning"
LIST_SEP = ";"

PROGRAM_FIELDS = [
    "key",
    "program_id",
    "source_file",
    "chapter",
    "tag",
    "start_line",
    "end_line",
    "has_code",
    "datasets_read",
    "datasets_written",
    "datasets_required",
    "files_read",
    "files_written",
    "procs",
    "macro",
    "proc_sql",
    "prx",
    "arrays",
    "retain_by",
    "ods",
    "sgplot",
    "user_formats",
    "inline_data",
    "notes",
]
FLAG_FIELDS = (
    "macro",
    "proc_sql",
    "prx",
    "arrays",
    "retain_by",
    "ods",
    "sgplot",
    "user_formats",
    "inline_data",
)
DATASET_FIELDS = ["name", "kind", "path", "exists", "producers", "consumers", "notes"]

TAG_RE = re.compile(r"^\s*\*\s*(\d+)\s*[-.]\s*(\d+)\s*;\s*$")
CHAPTER_RE = re.compile(r"^\s*\*+\s*Chapter\s+\d+", re.IGNORECASE)
CD_HEADER_RE = re.compile(
    r"^\s*\*\s*(Data set|Temporary|Program to create|Format used)", re.IGNORECASE
)
DATALINES_STMT_RE = re.compile(r"^\s*(datalines|cards|lines)(4?)\s*$", re.IGNORECASE)
MACRO_CALL_RE = re.compile(
    r"^\s*%(?!(?:let|put|if|do|end|global|local)\b)\w+\s*\(.*\)\s*$",
    re.DOTALL | re.IGNORECASE,
)
NAME_TOKEN = r"(?:[A-Za-z_&][\w&.]*?\.)?(?:'[^']*'n|\"[^\"]*\"n|[A-Za-z_&][\w&]*)"
NAME_RE = re.compile(NAME_TOKEN, re.IGNORECASE)
SQL_STOP = {
    "where",
    "group",
    "order",
    "having",
    "on",
    "left",
    "right",
    "inner",
    "full",
    "outer",
    "cross",
    "natural",
    "join",
    "union",
    "except",
    "intersect",
    "as",
    "select",
    "quit",
    "using",
}


# --------------------------------------------------------------------------- #
# Lexing
# --------------------------------------------------------------------------- #


def read_source(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@dataclass
class Cleaned:
    """Source with comments and DATALINES blanked (same line/column layout)."""

    text: str
    line_starts_in_code: list[bool]
    datalines_lines: set[int]


def clean(text: str) -> Cleaned:
    """Blank out SAS comments and DATALINES/CARDS data, keeping newlines.

    ``line_starts_in_code[i]`` is True when line ``i`` (0-based) starts in plain
    code at a statement boundary, i.e. a ``*...;`` there is a statement comment.
    """
    out: list[str] = []
    line_flags: list[bool] = []
    data_lines: set[int] = set()
    state = "code"
    stmt_start = True
    stmt_buf: list[str] = []
    pending_datalines: str | None = None  # "" or "4" once DATALINES; seen
    lines = text.split("\n")
    for lineno, line in enumerate(lines):
        if state == "datalines4" or state == "datalines":
            data_lines.add(lineno)
            line_flags.append(False)
            terminator = (
                (line.strip().startswith(";;;;"))
                if state == "datalines4"
                else (";" in line)
            )
            out.append(" " * len(line))
            if terminator:
                state = "code"
                stmt_start = True
                stmt_buf = []
            continue
        line_flags.append(state == "code" and stmt_start)
        buf: list[str] = []
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            nxt = line[i + 1] if i + 1 < n else ""
            if state == "block":
                if ch == "*" and nxt == "/":
                    buf.append("  ")
                    i += 2
                    state = "code"
                    continue
                buf.append(" ")
                i += 1
                continue
            if state == "stmt_comment":
                buf.append(" ")
                if ch == ";":
                    state = "code"
                    stmt_start = True
                    stmt_buf = []
                i += 1
                continue
            if state in ("squote", "dquote"):
                buf.append(ch)
                stmt_buf.append(ch)
                if (state == "squote" and ch == "'") or (
                    state == "dquote" and ch == '"'
                ):
                    state = "code"
                i += 1
                continue
            # code
            if ch == "/" and nxt == "*":
                buf.append("  ")
                i += 2
                state = "block"
                continue
            if stmt_start and ch == "*":
                buf.append(" ")
                state = "stmt_comment"
                i += 1
                continue
            if stmt_start and ch == "%" and nxt == "*":
                buf.append("  ")
                state = "stmt_comment"
                i += 2
                continue
            if ch == "'":
                state = "squote"
            elif ch == '"':
                state = "dquote"
            buf.append(ch)
            if ch == ";":
                m = DATALINES_STMT_RE.match("".join(stmt_buf))
                stmt_buf = []
                stmt_start = True
                if m:
                    pending_datalines = m.group(2)
            else:
                stmt_buf.append(ch)
                if not ch.isspace():
                    stmt_start = False
            i += 1
        out.append("".join(buf))
        if state == "code" and MACRO_CALL_RE.match("".join(stmt_buf)):
            # A macro invocation such as %print_n(x, 4) needs no semicolon.
            stmt_start = True
            stmt_buf = []
        if pending_datalines is not None:
            state = "datalines4" if pending_datalines == "4" else "datalines"
            pending_datalines = None
        else:
            stmt_buf.append("\n")
    return Cleaned("\n".join(out), line_flags, data_lines)


def split_statements(code: str, first_line: int) -> list[tuple[str, int]]:
    """Split cleaned code into (statement, 1-based line) pairs, respecting quotes."""
    stmts: list[tuple[str, int]] = []
    buf: list[str] = []
    line = first_line
    start_line: int | None = None
    quote = ""
    for ch in code:
        if ch == "\n":
            line += 1
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "'\"":
            quote = ch
        if ch == ";":
            text = " ".join("".join(buf).split())
            if text:
                stmts.append((text, start_line or line))
            buf = []
            start_line = None
            continue
        if start_line is None and not ch.isspace():
            start_line = line
        buf.append(ch)
    text = " ".join("".join(buf).split())
    if text:
        stmts.append((text, start_line or line))
    return stmts


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #


@dataclass
class Segment:
    key: str
    program_id: str
    source_file: str
    chapter: str
    tag: str
    start_line: int  # 1-based, inclusive
    end_line: int
    notes: list[str] = field(default_factory=list)


def _comment_text(lines: list[str], start: int) -> str:
    parts = []
    for line in lines[start:]:
        parts.append(line.strip())
        if ";" in line:
            break
    return " ".join(" ".join(parts).lstrip("*").split(";")[0].split())


def _trim_end(lines: list[str], start: int, end: int) -> int:
    while end > start and not lines[end - 1].strip():
        end -= 1
    return end


def segment_tagged(
    prefix: str, filename: str, text: str, cleaned: Cleaned
) -> list[Segment]:
    lines = text.split("\n")
    marks: list[tuple[int, str, re.Match[str] | None]] = []
    for i, line in enumerate(lines):
        if not cleaned.line_starts_in_code[i]:
            continue
        m = TAG_RE.match(line)
        if m:
            marks.append((i, "tag", m))
        elif CHAPTER_RE.match(line):
            marks.append((i, "chapter", None))
    segs: list[Segment] = []
    for idx, (i, kind, m) in enumerate(marks):
        if kind != "tag" or m is None:
            continue
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        end = _trim_end(lines, i, end)
        ch, num = int(m.group(1)), int(m.group(2))
        pid = f"{ch}-{num}"
        raw = line_tag = lines[i].strip()
        notes = []
        if f"*{pid};" != line_tag.replace(" ", ""):
            notes.append(f"tag written as '{raw}' (normalised to {pid})")
        segs.append(
            Segment(f"{prefix}:{pid}", pid, filename, str(ch), raw, i + 1, end, notes)
        )
    return segs


def _header_names(header: str) -> set[str]:
    return {
        w.lower()
        for w in re.findall(r"[A-Za-z_]\w*", header)
        if w.isupper() or "_" in w
    }


def segment_create_datasets(
    prefix: str, filename: str, text: str, cleaned: Cleaned
) -> list[Segment]:
    """Split Create_Datasets.sas at its ``*Data set X;``-style header comments.

    A DATA step that follows a blank line, is not the first step of its
    segment and writes a dataset not named in the header starts a new
    untagged segment (the trailing MANY_ONE / MANY_TWO / TRUNCATE block).
    """
    lines = text.split("\n")
    clines = cleaned.text.split("\n")
    heads = [
        i
        for i, line in enumerate(lines)
        if cleaned.line_starts_in_code[i] and CD_HEADER_RE.match(line)
    ]
    bounds: list[tuple[int, str]] = [(i, _comment_text(lines, i)) for i in heads]
    extra: list[tuple[int, str]] = []
    for n, (start, header) in enumerate(bounds):
        stop = bounds[n + 1][0] if n + 1 < len(bounds) else len(lines)
        names = _header_names(header)
        steps_seen = 0
        for j in range(start + 1, stop):
            m = re.match(r"\s*(data|proc)\b\s*([^;]*)", clines[j], re.IGNORECASE)
            if not m:
                continue
            steps_seen += 1
            if m.group(1).lower() != "data" or steps_seen == 1 or lines[j - 1].strip():
                continue
            written = {w.split(".")[-1].lower() for w in NAME_RE.findall(m.group(2))}
            if not written & names:
                extra.append((j, ""))
                break
    bounds = sorted(bounds + extra)
    segs: list[Segment] = []
    for n, (start, header) in enumerate(bounds):
        stop = bounds[n + 1][0] if n + 1 < len(bounds) else len(lines)
        stop = _trim_end(lines, start, stop)
        pid = f"cd-{n + 1:02d}"
        notes = [] if header else ["untagged block (no header comment)"]
        segs.append(
            Segment(
                f"{prefix}:{pid}", pid, filename, "", header, start + 1, stop, notes
            )
        )
    return segs


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #


@dataclass
class Context:
    """State that carries across programs within one source file."""

    librefs: dict[str, str] = field(default_factory=dict)  # libref -> path
    filerefs: dict[str, list[str]] = field(default_factory=dict)
    format_names: set[str] = field(default_factory=set)


def _strip_parens(s: str) -> str:
    out, depth = [], 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _names(s: str) -> list[str]:
    """Dataset names in a DATA/SET/MERGE-style list (options and keywords dropped)."""
    s = _strip_parens(s.split("/")[0])
    s = re.sub(r"\w+\s*=\s*\S+", " ", s)
    return [t for t in NAME_RE.findall(s) if t]


def _quoted(s: str) -> list[str]:
    return [a or b for a, b in re.findall(r"'([^']*)'|\"([^\"]*)\"", s)]


def _basename(path: str) -> str:
    return re.split(r"[\\/]", path)[-1]


class Analyzer:
    def __init__(
        self,
        ctx: Context,
        data_files: dict[str, str],
        datalines: set[int] | None = None,
    ):
        self._datalines = datalines or set()
        self.ctx = ctx
        self.data_files = data_files  # lowercased basename -> actual name

    def norm_ds(self, name: str) -> str | None:
        name = name.strip()
        if not name or name.lower().split(".")[-1] in {
            "_null_",
            "_data_",
            "_last_",
            "_all_",
        }:
            return None
        if (
            "." in name
            and not name.lower().endswith(("'n", '"n'))
            or re.match(r"^\w+\.['\"]", name)
        ):
            lib, _, mem = name.partition(".")
            lib = lib.lower()
            mem = mem if mem[:1] in "'\"" else mem.lower()
            if lib == "work":
                return mem
            path = self.ctx.librefs.get(lib, "")
            if lib != "learn" and path.lower().rstrip("\\/") == LEARN_PATH:
                self.aliases.add(lib)
                lib = "learn"
            return f"{lib}.{mem}"
        return name.lower()

    def file_ref(self, path: str) -> str:
        base = _basename(path)
        actual = self.data_files.get(base.lower())
        if actual and actual != base:
            self.case_mismatch.add(f"{base} -> Data/{actual}")
        return f"Data/{actual}" if actual else base

    def analyze(self, code: str, first_line: int, seg: Segment) -> dict[str, object]:
        self.aliases: set[str] = set()
        self.case_mismatch: set[str] = set()
        reads: list[str] = []
        writes: list[str] = []
        required: list[str] = []
        files_read: list[str] = []
        files_written: list[str] = []
        procs: list[str] = []
        flags = dict.fromkeys(FLAG_FIELDS, False)
        dynamic = False
        step = ""  # "data", proc name, or ""
        format_step = False

        def add(lst: list[str], item: str | None) -> None:
            if item and item not in lst:
                lst.append(item)

        def read(name: str) -> None:
            nonlocal dynamic
            ds = self.norm_ds(name)
            if not ds:
                return
            if "&" in ds:
                dynamic = True
            lib = ds.split(".")[0] if "." in ds else ""
            path = self.ctx.librefs.get(lib, "")
            if lib and re.search(r"\.xlsx?$", path, re.IGNORECASE):
                add(files_read, self.file_ref(path))
            add(reads, ds)
            if ds not in writes:
                add(required, ds)

        def write(name: str) -> None:
            nonlocal dynamic
            ds = self.norm_ds(name)
            if ds:
                dynamic = dynamic or "&" in ds
                add(writes, ds)

        for stmt, _line in split_statements(code, first_line):
            low = stmt.lower()
            first = low.split(None, 1)[0] if low else ""
            rest = stmt[len(first) :].strip()

            if re.search(
                r"%(macro|let|do|if|put|sysfunc|eval|str|global|local)\b|&[a-z_]|call\s+symputx?\b|symget",
                low,
            ):
                flags["macro"] = True
            if re.search(r"\bprx\w*\s*\(|call\s+prx", low):
                flags["prx"] = True
            if first == "ods":
                flags["ods"] = True

            if first == "libname":
                parts = rest.split(None, 1)
                if parts:
                    q = _quoted(rest)
                    if q:
                        self.ctx.librefs[parts[0].lower()] = q[0]
                        if re.search(r"\.xlsx?$", q[0], re.IGNORECASE):
                            add(files_read, self.file_ref(q[0]))
                continue
            if first == "filename":
                parts = rest.split(None, 1)
                if parts:
                    self.ctx.filerefs[parts[0].lower()] = _quoted(rest)
                continue
            if first == "options":
                continue

            if first == "data" and step != "sql":
                step = "data"
                format_step = False
                for n in _names(rest):
                    write(n)
                continue
            if first == "proc":
                pname = (rest.split(None, 1)[0] if rest else "").lower()
                step = "sql" if pname == "sql" else pname
                format_step = pname == "format"
                add(procs, pname.upper())
                if pname == "sql":
                    flags["proc_sql"] = True
                if pname.startswith("sg"):
                    flags["sgplot"] = True
                if pname == "format":
                    flags["user_formats"] = True
                m = re.search(r"\bdata\s*=\s*(" + NAME_TOKEN + ")", stmt, re.IGNORECASE)
                if m:
                    read(m.group(1))
                    if pname == "sort" and not re.search(r"\bout\s*=", low):
                        write(m.group(1))
                for m in re.finditer(
                    r"\b(?:out|cntlout)\s*=\s*(" + NAME_TOKEN + ")", stmt, re.IGNORECASE
                ):
                    write(m.group(1))
                for m in re.finditer(
                    r"\bdatafile\s*=\s*(['\"][^'\"]*['\"])", stmt, re.IGNORECASE
                ):
                    add(files_read, self.file_ref(_quoted(m.group(1))[0]))
                for m in re.finditer(
                    r"\boutfile\s*=\s*(['\"][^'\"]*['\"])", stmt, re.IGNORECASE
                ):
                    add(files_written, _basename(_quoted(m.group(1))[0]))
                continue
            if first in ("run", "quit"):
                if first == "quit" or step != "sql":
                    step = "" if first == "quit" or step != "data" else step
                continue

            if first == "ods":
                m = re.match(r"ods\s+output\s+(.*)$", stmt, re.IGNORECASE)
                if m:
                    for mm in re.finditer(r"=\s*(" + NAME_TOKEN + ")", m.group(1)):
                        write(mm.group(1))
                for q in re.findall(
                    r"\b(?:file|body)\s*=\s*(['\"][^'\"]*['\"])", stmt, re.IGNORECASE
                ):
                    add(files_written, _basename(_quoted(q)[0]))
                continue

            if format_step:
                for m in re.finditer(
                    r"\b(?:value|invalue|picture)\s+(\$?[A-Za-z_]\w*)",
                    stmt,
                    re.IGNORECASE,
                ):
                    self.ctx.format_names.add(m.group(1).lower().lstrip("$"))
                continue

            if step == "sql":
                for m in re.finditer(
                    r"\bcreate\s+(?:table|view)\s+(" + NAME_TOKEN + ")",
                    stmt,
                    re.IGNORECASE,
                ):
                    write(m.group(1))
                for m in re.finditer(
                    r"\b(?:insert\s+into|update|delete\s+from)\s+(" + NAME_TOKEN + ")",
                    stmt,
                    re.IGNORECASE,
                ):
                    write(m.group(1))
                for name in _sql_sources(stmt):
                    read(name)
                continue

            # DATA step (or global) statements
            m = re.match(
                r"(?:.*?\b(?:then|else)\s+)?(?:do\s*;\s*)?(set|merge|update|modify)\b\s*(.*)$",
                stmt,
                re.IGNORECASE,
            )
            if m and (
                first in ("set", "merge", "update", "modify")
                or re.search(r"\b(then|else)\s+(set|merge|update|modify)\b", low)
            ):
                for n in _names(m.group(2)):
                    read(n)
                continue
            if first == "by" and step == "data":
                flags["retain_by"] = True
            if first == "retain" or re.search(r"\b(first|last)\.\w", low):
                flags["retain_by"] = True
            if (
                step == "data"
                and re.match(r"^[A-Za-z_]\w*\s*\+\s*[^=]+$", stmt)
                and first not in ("if", "else", "output", "put")
            ):
                flags["retain_by"] = True
            if first == "array":
                flags["arrays"] = True
            if first == "infile":
                target = rest.split(None, 1)[0] if rest else ""
                if target[:1] in "'\"":
                    add(files_read, self.file_ref(_quoted(rest)[0]))
                elif target.lower() in ("datalines", "cards"):
                    flags["inline_data"] = True
                elif target.lower() in self.ctx.filerefs:
                    for p in self.ctx.filerefs[target.lower()]:
                        add(files_read, self.file_ref(p))
                continue
            if first == "file":
                q = _quoted(rest)
                if q:
                    add(files_written, _basename(q[0]))
                continue
            for mm in re.finditer(
                r"dataset\s*:\s*['\"]([^'\"]+)['\"]", stmt, re.IGNORECASE
            ):
                read(mm.group(1))

        cleaned_lines = range(seg.start_line - 1, seg.end_line)
        if any(i in self._datalines for i in cleaned_lines):
            flags["inline_data"] = True
        if self.ctx.format_names and not flags["user_formats"]:
            pat = (
                r"(?<![\w.$])\$?("
                + "|".join(sorted(map(re.escape, self.ctx.format_names)))
                + r")\d*\.(?!\w*\.)"
            )
            if re.search(pat, code, re.IGNORECASE):
                flags["user_formats"] = True
        notes = list(seg.notes)
        if not code.strip():
            notes.append(
                "no executable code (comment-only answer or commented-out demonstration)"
            )
        for lib in sorted(self.aliases):
            notes.append(
                f"libref {lib.upper()} points at the Learn folder (catalogued as learn.*)"
            )
        if self.case_mismatch:
            notes.append(
                "file name case differs from Data/: "
                + ", ".join(sorted(self.case_mismatch))
            )
        if dynamic:
            notes.append("dataset names built from macro variables")
        missing = [f for f in files_read if not f.startswith("Data/")]
        if missing:
            notes.append("external file(s) not in Data/: " + ", ".join(missing))
        return {
            "has_code": int(bool(code.strip())),
            "datasets_read": LIST_SEP.join(reads),
            "datasets_written": LIST_SEP.join(writes),
            "datasets_required": LIST_SEP.join(required),
            "files_read": LIST_SEP.join(files_read),
            "files_written": LIST_SEP.join(files_written),
            "procs": LIST_SEP.join(procs),
            **{k: int(v) for k, v in flags.items()},
            "notes": "; ".join(notes),
        }


def _sql_sources(stmt: str) -> list[str]:
    names: list[str] = []
    for m in re.finditer(r"\b(?:from|join)\s+", stmt, re.IGNORECASE):
        pos = m.end()
        while True:
            tail = stmt[pos:]
            if tail.startswith("("):
                break
            nm = re.match(r"(" + NAME_TOKEN + r")(\s*\([^)]*\))?", tail)
            if not nm or nm.group(1).lower() in SQL_STOP:
                break
            names.append(nm.group(1))
            pos += nm.end()
            al = re.match(r"\s+(?:as\s+)?([A-Za-z_]\w*)", stmt[pos:], re.IGNORECASE)
            if al and al.group(1).lower() not in SQL_STOP:
                pos += al.end()
            comma = re.match(r"\s*,\s*", stmt[pos:])
            if not comma:
                break
            pos += comma.end()
    return names


# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #


def build_programs(
    source_dir: Path = SOURCE_DIR, data_dir: Path = DATA_DIR
) -> list[dict[str, object]]:
    data_files = (
        {p.name.lower(): p.name for p in data_dir.iterdir() if p.is_file()}
        if data_dir.exists()
        else {}
    )
    rows: list[dict[str, object]] = []
    shared_formats: set[str] = set()
    for prefix, filename in SOURCES:
        text = read_source(source_dir / filename)
        cleaned = clean(text)
        if prefix == "cd":
            segs = segment_create_datasets(prefix, filename, text, cleaned)
        else:
            segs = segment_tagged(prefix, filename, text, cleaned)
        ctx = Context(format_names=set(shared_formats))
        analyzer = Analyzer(ctx, data_files, cleaned.datalines_lines)
        clines = cleaned.text.split("\n")
        # Global statements before the first program (LIBNAME, OPTIONS) set context.
        if segs:
            analyzer.analyze(
                "\n".join(clines[: segs[0].start_line - 1]),
                1,
                Segment("", "", filename, "", "", 1, 1),
            )
        for seg in segs:
            code = "\n".join(clines[seg.start_line - 1 : seg.end_line])
            row: dict[str, object] = {
                "key": seg.key,
                "program_id": seg.program_id,
                "source_file": seg.source_file,
                "chapter": seg.chapter,
                "tag": seg.tag,
                "start_line": seg.start_line,
                "end_line": seg.end_line,
            }
            row.update(analyzer.analyze(code, seg.start_line, seg))
            rows.append(row)
        # Formats stored in Learn by Create_Datasets.sas are visible to later files.
        shared_formats |= ctx.format_names
    return rows


def _split(value: object) -> list[str]:
    return [v for v in str(value).split(LIST_SEP) if v]


def build_datasets(
    programs: list[dict[str, object]], data_dir: Path = DATA_DIR
) -> list[dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}

    def entry(name: str, kind: str, path: str = "") -> dict[str, object]:
        e = entries.setdefault(
            name,
            {
                "name": name,
                "kind": kind,
                "path": path,
                "exists": "",
                "producers": [],
                "consumers": [],
                "notes": [],
            },
        )
        return e

    for p in programs:
        key = str(p["key"])
        for ds in _split(p["datasets_written"]):
            if ds.startswith("learn."):
                entry(ds, "learn")["producers"].append(key)  # type: ignore[union-attr]
        for ds in _split(p["datasets_required"]):
            kind = _dataset_kind(ds)
            if kind == "work" or "&" in ds:
                continue
            entry(ds, kind)["consumers"].append(key)  # type: ignore[union-attr]
        for f in _split(p["files_read"]):
            e = entry(
                f,
                "data_file" if f.startswith("Data/") else "external_file",
                f if f.startswith("Data/") else "",
            )
            e["consumers"].append(key)  # type: ignore[union-attr]

    # Work datasets produced by Create_Datasets.sas and needed by other programs.
    cd_work: dict[str, list[str]] = {}
    for p in programs:
        if str(p["key"]).startswith("cd:"):
            for ds in _split(p["datasets_written"]):
                if _dataset_kind(ds) == "work":
                    cd_work.setdefault(ds, []).append(str(p["key"]))
    for p in programs:
        if str(p["key"]).startswith("cd:"):
            continue
        for ds in _split(p["datasets_required"]):
            if ds in cd_work:
                e = entry(ds, "work_shared")
                e["producers"] = cd_work[ds]
                e["consumers"].append(str(p["key"]))  # type: ignore[union-attr]
                e["notes"] = ["temporary (WORK) dataset built by Create_Datasets.sas"]

    if data_dir.exists():
        for f in sorted(data_dir.iterdir()):
            if f.is_file() and f.name.lower() != "readme.md":
                entry(f"Data/{f.name}", "data_file", f"Data/{f.name}")

    rows = []
    for name in sorted(
        entries, key=lambda n: (_KIND_ORDER.get(str(entries[n]["kind"]), 9), n.lower())
    ):
        e = entries[name]
        notes = list(e["notes"])  # type: ignore[arg-type]
        if e["kind"] == "learn" and not e["producers"]:
            notes.append("no producer found in the sources")
        if len(e["producers"]) > 1:  # type: ignore[arg-type]
            notes.append("written by more than one program")
        if e["kind"] == "data_file":
            e["exists"] = int((data_dir / str(e["path"])[len("Data/") :]).exists())
            if not e["consumers"]:
                notes.append("not referenced by any program")
        elif e["kind"] == "external_file":
            e["exists"] = 0
            notes.append("referenced but not present in Data/")
        elif e["kind"] == "sashelp":
            notes.append("SAS-supplied sample library")
        elif e["kind"] == "excel_sheet":
            notes.append("worksheet read through an Excel LIBNAME engine")
        rows.append(
            {
                **e,
                "producers": LIST_SEP.join(dict.fromkeys(e["producers"])),  # type: ignore[arg-type]
                "consumers": LIST_SEP.join(dict.fromkeys(e["consumers"])),  # type: ignore[arg-type]
                "notes": "; ".join(notes),
            }
        )
    return rows


_KIND_ORDER = {
    "learn": 0,
    "work_shared": 1,
    "sashelp": 2,
    "excel_sheet": 3,
    "other_lib": 4,
    "data_file": 5,
    "external_file": 6,
}


def _dataset_kind(ds: str) -> str:
    if "." not in ds:
        return "work"
    lib = ds.split(".", 1)[0]
    if lib == "learn":
        return "learn"
    if lib == "sashelp":
        return "sashelp"
    if ds.endswith(("'n", '"n')):
        return "excel_sheet"
    return "other_lib"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument(
        "--check", action="store_true", help="fail if the checked-in CSVs are stale"
    )
    args = ap.parse_args(argv)

    programs = build_programs()
    datasets = build_datasets(programs)
    if args.check:
        import io

        stale = []
        for name, fields, rows in (
            ("programs.csv", PROGRAM_FIELDS, programs),
            ("datasets.csv", DATASET_FIELDS, datasets),
        ):
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})
            target = args.out_dir / name
            if (
                not target.exists()
                or target.read_text(encoding="utf-8") != buf.getvalue()
            ):
                stale.append(name)
        if stale:
            print("stale: " + ", ".join(stale), file=sys.stderr)
            return 1
        return 0
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "programs.csv", PROGRAM_FIELDS, programs)
    write_csv(args.out_dir / "datasets.csv", DATASET_FIELDS, datasets)
    by_src: dict[str, int] = {}
    for p in programs:
        by_src[str(p["source_file"])] = by_src.get(str(p["source_file"]), 0) + 1
    for src, n in by_src.items():
        print(f"{n:4d} programs  {src}")
    kinds: dict[str, int] = {}
    for d in datasets:
        kinds[str(d["kind"])] = kinds.get(str(d["kind"]), 0) + 1
    print("datasets: " + ", ".join(f"{k}={v}" for k, v in kinds.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
