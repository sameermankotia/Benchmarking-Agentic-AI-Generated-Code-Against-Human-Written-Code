"""Shared helpers: subject discovery, file collection, LOC accounting, I/O.

Kept dependency-free (stdlib only) so the orchestrator and the aggregation
step run even when the heavier analysis tools are not installed.
"""

from __future__ import annotations

import ast
import json
import os
import tokenize
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
REGISTRY_PATH = REPO_ROOT / "subjects" / "subjects.json"


@dataclass
class Subject:
    id: str
    label: str
    kind: str  # "human" | "agentic"
    pair: str  # "flask" | "django"
    path: str
    snapshot: str = ""
    oracle: str = ""
    available: bool = True
    include: list[str] = field(default_factory=list)

    @property
    def root(self) -> Path:
        return (REPO_ROOT / self.path).resolve()

    def is_present(self) -> bool:
        return self.available and self.root.exists()

    def target_paths(self) -> list[Path]:
        """Top-level paths to hand to directory-scanning tools (Bandit, CPD).

        Honours the ``include`` sub-path filter so these tools scan exactly the
        same scope as the AST-based metrics (which use ``python_files``). For a
        subject with no filter this is just the root.
        """
        if self.include:
            return [self.root / inc for inc in self.include
                    if (self.root / inc).exists()]
        return [self.root]

    def python_files(self) -> list[Path]:
        """All ``.py`` files under the subject root, deterministically ordered.

        Honours the ``include`` sub-path filter (used to restrict Django to its
        ``urls/`` and ``views/`` packages) and skips vendored / test-cache dirs.
        """
        if not self.root.exists():
            return []
        skip_dirs = {"__pycache__", ".git", ".tox", "build", "dist", ".mypy_cache"}
        files: list[Path] = []
        for path in sorted(self.root.rglob("*.py")):
            if any(part in skip_dirs for part in path.parts):
                continue
            if self.include:
                rel = path.relative_to(self.root)
                if not any(rel.parts and rel.parts[0] == inc for inc in self.include):
                    continue
            files.append(path)
        return files


def load_subjects(only: Iterable[str] | None = None) -> list[Subject]:
    data = json.loads(REGISTRY_PATH.read_text())
    subjects = [Subject(**{k: v for k, v in s.items() if not k.startswith("_")})
                for s in data["subjects"]]
    if only:
        wanted = set(only)
        subjects = [s for s in subjects if s.id in wanted]
    return subjects


# --------------------------------------------------------------------------- #
# LOC / comment / docstring accounting (used by repo_stats and MI reporting)  #
# --------------------------------------------------------------------------- #

@dataclass
class LocStats:
    loc: int = 0            # physical source lines excluding blanks + comment-only
    blank: int = 0
    comment_lines: int = 0  # lines that are comment-only
    total: int = 0          # every physical line

    @property
    def comment_density(self) -> float:
        denom = self.loc + self.comment_lines
        return round(100.0 * self.comment_lines / denom, 1) if denom else 0.0


def loc_for_file(path: Path) -> LocStats:
    """Count SLOC / blank / comment lines using Python's own tokenizer.

    A line is 'comment' if it holds a COMMENT token and no other code; 'blank'
    if empty/whitespace; otherwise it counts as source.
    """
    src = path.read_bytes()
    stats = LocStats()
    lines = src.splitlines()
    stats.total = len(lines)

    comment_only: set[int] = set()
    code_lines: set[int] = set()
    try:
        for tok in tokenize.tokenize(BytesIO(src).readline):
            if tok.type == tokenize.COMMENT:
                comment_only.add(tok.start[0])
            elif tok.type in (tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING,
                              tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
                continue
            else:
                code_lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Fall back to a naive count for files the tokenizer chokes on.
        for i, raw in enumerate(lines, 1):
            s = raw.decode("utf-8", "replace").strip()
            if not s:
                stats.blank += 1
            elif s.startswith("#"):
                stats.comment_lines += 1
            else:
                stats.loc += 1
        return stats

    comment_only -= code_lines  # a line with code + trailing comment is code
    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            stats.blank += 1
        elif i in comment_only:
            stats.comment_lines += 1
        elif i in code_lines:
            stats.loc += 1
        else:
            stats.blank += 1
    return stats


@dataclass
class DefCounts:
    functions: int = 0
    classes: int = 0
    documented: int = 0        # functions/methods/classes with a docstring
    documentable: int = 0


def def_counts_for_file(path: Path) -> DefCounts:
    counts = DefCounts()
    try:
        tree = ast.parse(path.read_bytes())
    except SyntaxError:
        return counts
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts.functions += 1
            counts.documentable += 1
            if ast.get_docstring(node):
                counts.documented += 1
        elif isinstance(node, ast.ClassDef):
            counts.classes += 1
            counts.documentable += 1
            if ast.get_docstring(node):
                counts.documented += 1
    return counts


# --------------------------------------------------------------------------- #
# Result I/O                                                                   #
# --------------------------------------------------------------------------- #

def write_result(dimension: str, subject_id: str, payload: dict) -> Path:
    out_dir = RESULTS_DIR / dimension
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{subject_id}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return out_path


def read_result(dimension: str, subject_id: str) -> dict | None:
    path = RESULTS_DIR / dimension / f"{subject_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def pct(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0
