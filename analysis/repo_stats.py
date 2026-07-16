"""Stage-3 structural characteristics (paper Table: 'Structural Characteristics').

Computes, per subject: LOC, source-file count, function/method count, class
count, average function length, test-file count, comment density, and docstring
coverage. Stdlib only.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from . import common


def _is_test_file(path: Path) -> bool:
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py") or "test" in path.parts


def _function_lengths(path: Path) -> list[int]:
    try:
        tree = ast.parse(path.read_bytes())
    except SyntaxError:
        return []
    lengths: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", None)
            if end is not None:
                lengths.append(end - node.lineno + 1)
    return lengths


def analyze(subject: common.Subject) -> dict:
    files = subject.python_files()
    source_files = [f for f in files if not _is_test_file(f)]
    test_files = [f for f in files if _is_test_file(f)]

    loc = comment_lines = 0
    functions = classes = documented = documentable = 0
    lengths: list[int] = []

    for f in source_files:
        ls = common.loc_for_file(f)
        loc += ls.loc
        comment_lines += ls.comment_lines
        dc = common.def_counts_for_file(f)
        functions += dc.functions
        classes += dc.classes
        documented += dc.documented
        documentable += dc.documentable
        lengths.extend(_function_lengths(f))

    denom = loc + comment_lines
    return {
        "subject": subject.id,
        "label": subject.label,
        "kind": subject.kind,
        "language": "Python",
        "loc": loc,
        "source_files": len(source_files),
        "functions": functions,
        "classes": classes,
        "avg_function_length": round(common.mean([float(x) for x in lengths]), 1),
        "test_files": len(test_files),
        "comment_density_pct": round(100.0 * comment_lines / denom, 1) if denom else 0.0,
        "docstring_coverage_pct": common.pct(documented, documentable),
    }


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[repo_stats] SKIP {subject.id}: snapshot not present")
            continue
        payload = analyze(subject)
        common.write_result("repo_stats", subject.id, payload)
        print(f"[repo_stats] {subject.id}: {payload['loc']} LOC, "
              f"{payload['functions']} fns, MI-inputs ready")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
