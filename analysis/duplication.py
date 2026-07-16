"""RQ5 code duplication via CPD (Copy-Paste Detector, PMD toolkit).

Runs CPD with a 50-token minimum (paper §3.5.6), parses its XML report, and
reports duplicated-block count, total duplicated LOC, duplicated fraction of
total LOC, and the largest single duplicated block in tokens.

CPD ships in two CLI shapes; both are attempted:
  PMD 7:  pmd cpd --minimum-tokens 50 --language python --dir <root> --format xml
  PMD 6:  cpd --minimum-tokens 50 --language python --files <root> --format xml
"""

from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from . import common

MIN_TOKENS = 50


def _cpd_commands(targets: list[Path]) -> list[list[str]]:
    v7 = ["pmd", "cpd", "--minimum-tokens", str(MIN_TOKENS),
          "--language", "python", "--format", "xml"]
    for t in targets:
        v7 += ["--dir", str(t)]
    v6 = ["cpd", "--minimum-tokens", str(MIN_TOKENS),
          "--language", "python", "--format", "xml"]
    for t in targets:
        v6 += ["--files", str(t)]
    return [v7, v6]


def _run_cpd(targets: list[Path]) -> str:
    last_err = ""
    for cmd in _cpd_commands(targets):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            last_err = f"{cmd[0]} not found on PATH"
            continue
        # CPD exits 4 when duplicates are found; XML is still emitted.
        if proc.stdout.strip().startswith("<?xml") or "<pmd-cpd" in proc.stdout:
            return proc.stdout
        last_err = proc.stderr.strip() or f"exit {proc.returncode}"
    raise RuntimeError(f"CPD unavailable or failed: {last_err}")


def _parse(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    blocks = root.findall("duplication")
    total_dup_lines = 0
    max_tokens = 0
    parsed = []
    for d in blocks:
        lines = int(d.get("lines", "0"))
        tokens = int(d.get("tokens", "0"))
        occurrences = d.findall("file")
        # Each duplicated block spans `lines` lines and recurs in every listed
        # location; count the redundant copies (occurrences - 1) toward waste.
        redundant_copies = max(len(occurrences) - 1, 1)
        total_dup_lines += lines * redundant_copies
        max_tokens = max(max_tokens, tokens)
        parsed.append({
            "lines": lines,
            "tokens": tokens,
            "occurrences": [
                {"path": f.get("path"), "line": int(f.get("line", "0"))}
                for f in occurrences
            ],
        })
    return {
        "duplicated_blocks": len(blocks),
        "duplicated_loc": total_dup_lines,
        "max_block_tokens": max_tokens,
        "blocks": parsed,
    }


def analyze(subject: common.Subject, total_loc: int) -> dict:
    result = _parse(_run_cpd(subject.target_paths()))
    loc = total_loc or 1
    result.update({
        "subject": subject.id,
        "label": subject.label,
        "duplicated_pct": round(100.0 * result["duplicated_loc"] / loc, 1),
        "min_tokens": MIN_TOKENS,
    })
    return result


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[duplication] SKIP {subject.id}: snapshot not present")
            continue
        stats = common.read_result("repo_stats", subject.id)
        loc = stats["loc"] if stats else sum(
            common.loc_for_file(f).loc for f in subject.python_files())
        try:
            payload = analyze(subject, loc)
        except RuntimeError as e:
            print(f"[duplication] SKIP {subject.id}: {e}")
            continue
        common.write_result("duplication", subject.id, payload)
        print(f"[duplication] {subject.id}: {payload['duplicated_blocks']} blocks, "
              f"{payload['duplicated_pct']}% duplicated")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
