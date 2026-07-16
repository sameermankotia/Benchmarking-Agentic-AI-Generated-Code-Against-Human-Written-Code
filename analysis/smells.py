"""RQ3 code-smell counts via pylint.

Runs pylint with the default plugin set and its JSON reporter, drops F-category
(fatal) findings that stem from the isolated analysis environment (paper
§3.5.3), and reports totals, per-100-LOC density, and C/R/W/E category
breakdown.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from . import common

# pylint message-id first letter -> category.
CATEGORY = {"C": "convention", "R": "refactor", "W": "warning",
            "E": "error", "F": "fatal", "I": "info"}
DROP_CATEGORIES = {"fatal", "info"}


def _run_pylint(files: list[Path]) -> list[dict]:
    if not files:
        return []
    cmd = ["pylint", "--output-format=json", "--score=n", *map(str, files)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if not proc.stdout.strip():
        # pylint prints nothing only when it crashed before analysis.
        if proc.returncode not in (0,):
            raise RuntimeError(f"pylint failed: {proc.stderr.strip()}")
        return []
    return json.loads(proc.stdout)


def analyze(subject: common.Subject, total_loc: int) -> dict:
    messages = _run_pylint(subject.python_files())
    by_category: dict[str, int] = {c: 0 for c in ("convention", "refactor", "warning", "error")}
    by_symbol: dict[str, int] = {}
    kept = 0
    for m in messages:
        letter = m.get("message-id", "C0")[0]
        cat = CATEGORY.get(letter, "convention")
        if cat in DROP_CATEGORIES:
            continue
        kept += 1
        by_category[cat] = by_category.get(cat, 0) + 1
        sym = m.get("symbol", "unknown")
        by_symbol[sym] = by_symbol.get(sym, 0) + 1

    loc = total_loc or 1
    top = dict(sorted(by_symbol.items(), key=lambda kv: -kv[1])[:15])
    return {
        "subject": subject.id,
        "label": subject.label,
        "total_findings": kept,
        "per_100_loc": round(100.0 * kept / loc, 2),
        "by_category": by_category,
        "top_symbols": top,
    }


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[smells] SKIP {subject.id}: snapshot not present")
            continue
        stats = common.read_result("repo_stats", subject.id)
        loc = stats["loc"] if stats else sum(
            common.loc_for_file(f).loc for f in subject.python_files())
        payload = analyze(subject, loc)
        common.write_result("smells", subject.id, payload)
        print(f"[smells] {subject.id}: {payload['total_findings']} findings "
              f"({payload['per_100_loc']}/100 LOC)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
