"""RQ4 security vulnerability density via Bandit.

Runs Bandit's CLI with the full default plugin set, keeps Medium-confidence or
higher findings (paper §3.5.4), normalises by LOC, and maps Bandit test IDs to
CWE classes following Cotroneo et al.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from . import common

# Bandit test-id -> CWE, per paper §3.5.4.
CWE_MAP = {
    "B101": "CWE-617",   # assert used
    "B105": "CWE-259",   # hardcoded password string
    "B106": "CWE-259",   # hardcoded password funcarg
    "B107": "CWE-259",   # hardcoded password default
    "B311": "CWE-330",   # insecure random
    "B602": "CWE-78",    # subprocess shell=True
    "B608": "CWE-89",    # SQL injection
}

CONFIDENCE_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
MIN_CONFIDENCE = "MEDIUM"


def _run_bandit(targets: list[Path]) -> dict:
    cmd = ["bandit", "-r", *[str(t) for t in targets], "-f", "json", "-q"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # Bandit exits 1 when it finds issues; JSON is still on stdout.
    if not proc.stdout.strip():
        raise RuntimeError(f"bandit produced no output: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def analyze(subject: common.Subject, total_loc: int) -> dict:
    report = _run_bandit(subject.target_paths())
    kept: list[dict] = []
    for r in report.get("results", []):
        if CONFIDENCE_RANK.get(r["issue_confidence"].upper(), 0) < CONFIDENCE_RANK[MIN_CONFIDENCE]:
            continue
        test_id = r["test_id"]
        cwe = CWE_MAP.get(test_id)
        if cwe is None:
            raw_id = (r.get("issue_cwe") or {}).get("id")
            cwe = f"CWE-{raw_id}" if raw_id is not None else None
        kept.append({
            "test_id": test_id,
            "cwe": cwe,
            "severity": r["issue_severity"].upper(),
            "confidence": r["issue_confidence"].upper(),
            "file": r["filename"],
            "line": r["line_number"],
            "text": r["issue_text"],
        })

    by_severity: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_cwe: dict[str, int] = {}
    for f in kept:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
        cwe = f["cwe"] or "unmapped"
        by_cwe[cwe] = by_cwe.get(cwe, 0) + 1

    loc = total_loc or 1
    return {
        "subject": subject.id,
        "label": subject.label,
        "total_findings": len(kept),
        "density_per_kloc": round(1000.0 * len(kept) / loc, 2),
        "by_severity": by_severity,
        "by_cwe": dict(sorted(by_cwe.items(), key=lambda kv: -kv[1])),
        "findings": kept,
        "min_confidence": MIN_CONFIDENCE,
    }


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[security] SKIP {subject.id}: snapshot not present")
            continue
        stats = common.read_result("repo_stats", subject.id)
        loc = stats["loc"] if stats else sum(
            common.loc_for_file(f).loc for f in subject.python_files())
        payload = analyze(subject, loc)
        common.write_result("security", subject.id, payload)
        print(f"[security] {subject.id}: {payload['total_findings']} findings "
              f"({payload['density_per_kloc']}/kLOC)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
