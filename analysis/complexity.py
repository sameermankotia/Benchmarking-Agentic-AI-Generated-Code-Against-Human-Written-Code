"""RQ2 (cyclomatic + cognitive complexity) and the MI half of RQ3.

Cyclomatic complexity and the Maintainability Index come from Radon's Python
API; cognitive complexity comes from ``complexipy`` (SonarSource algorithm).
Per-function and per-file records are retained so the aggregator can compute
means, medians, maxima, and threshold-exceedance fractions.

Thresholds follow the paper: CC > 10 (McCabe refactor threshold),
CogC > 15, MI < 65 (unmaintainable).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import common

CC_THRESHOLD = 10
COGC_THRESHOLD = 15
MI_THRESHOLD = 65


def _cc_records(path: Path) -> list[dict]:
    """Per-function cyclomatic complexity via radon."""
    from radon.complexity import cc_visit

    try:
        blocks = cc_visit(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, Exception):  # radon raises bare exceptions on bad input
        return []
    out = []
    for b in blocks:
        out.append({
            "name": getattr(b, "fullname", b.name),
            "lineno": b.lineno,
            "cc": b.complexity,
        })
    return out


def _mi_score(path: Path) -> float | None:
    """File-level Maintainability Index (multi=True → comment-aware variant)."""
    from radon.metrics import mi_visit

    try:
        return round(mi_visit(path.read_text(encoding="utf-8", errors="replace"), True), 2)
    except Exception:
        return None


def _cogc_records(path: Path) -> list[dict]:
    """Per-function cognitive complexity via complexipy."""
    try:
        from complexipy import file_complexity
    except ImportError:
        return []
    try:
        fc = file_complexity(str(path))
    except Exception:
        return []
    out = []
    for fn in getattr(fc, "functions", []):
        out.append({
            "name": fn.name,
            "lineno": getattr(fn, "line_start", getattr(fn, "line", 0)),
            "cogc": fn.complexity,
        })
    return out


def analyze(subject: common.Subject) -> dict:
    cc_all: list[dict] = []
    cogc_all: list[dict] = []
    mi_files: list[dict] = []

    for f in subject.python_files():
        rel = str(f.relative_to(subject.root))
        for rec in _cc_records(f):
            rec["file"] = rel
            cc_all.append(rec)
        for rec in _cogc_records(f):
            rec["file"] = rel
            cogc_all.append(rec)
        mi = _mi_score(f)
        if mi is not None:
            mi_files.append({"file": rel, "mi": mi})

    cc_vals = [r["cc"] for r in cc_all]
    cogc_vals = [r["cogc"] for r in cogc_all]
    mi_vals = [r["mi"] for r in mi_files]

    return {
        "subject": subject.id,
        "label": subject.label,
        "cc": {
            "n": len(cc_vals),
            "mean": round(common.mean(cc_vals), 1),
            "median": round(common.median(cc_vals), 1),
            "max": max(cc_vals) if cc_vals else 0,
            "pct_over_threshold": common.pct(
                sum(1 for v in cc_vals if v > CC_THRESHOLD), len(cc_vals)),
            "threshold": CC_THRESHOLD,
            "records": cc_all,
        },
        "cogc": {
            "n": len(cogc_vals),
            "mean": round(common.mean(cogc_vals), 1),
            "median": round(common.median(cogc_vals), 1),
            "max": max(cogc_vals) if cogc_vals else 0,
            "pct_over_threshold": common.pct(
                sum(1 for v in cogc_vals if v > COGC_THRESHOLD), len(cogc_vals)),
            "threshold": COGC_THRESHOLD,
            "records": cogc_all,
        },
        "mi": {
            "n": len(mi_vals),
            "mean": round(common.mean(mi_vals), 1),
            "median": round(common.median(mi_vals), 1),
            "min": round(min(mi_vals), 1) if mi_vals else 0.0,
            "pct_below_threshold": common.pct(
                sum(1 for v in mi_vals if v < MI_THRESHOLD), len(mi_vals)),
            "threshold": MI_THRESHOLD,
            "files": mi_files,
        },
    }


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[complexity] SKIP {subject.id}: snapshot not present")
            continue
        payload = analyze(subject)
        common.write_result("complexity", subject.id, payload)
        print(f"[complexity] {subject.id}: mean CC={payload['cc']['mean']} "
              f"mean CogC={payload['cogc']['mean']} mean MI={payload['mi']['mean']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
