"""Read per-subject result JSON and render the paper tables as CSV.

Outputs (under results/tables/):
  table_repo_stats.csv    structural characteristics (all subjects)
  table_correctness.csv   RQ1 per-category pass rates (per oracle pair)
  table_complexity.csv    RQ2 CC + CogC summary
  table_maintainability.csv RQ3 MI + pylint smell density
  table_security.csv      RQ4 finding density, severity, CWE mix
  table_duplication.csv   RQ5 duplication summary
  summary.csv             one row per subject, headline numbers for every RQ
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from . import common

TABLES_DIR = common.RESULTS_DIR / "tables"


def _subjects_with(dimension: str) -> list[common.Subject]:
    return [s for s in common.load_subjects()
            if common.read_result(dimension, s.id) is not None]


def _write_csv(name: str, header: list[str], rows: list[list]) -> Path:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    path = TABLES_DIR / name
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"[aggregate] wrote {path.relative_to(common.REPO_ROOT)}")
    return path


def table_repo_stats() -> None:
    subs = _subjects_with("repo_stats")
    if not subs:
        return
    header = ["attribute"] + [s.label for s in subs]
    fields = [
        ("Language", "language"),
        ("Lines of Code (LOC)", "loc"),
        ("Source Files", "source_files"),
        ("Functions / Methods", "functions"),
        ("Classes", "classes"),
        ("Avg. Function Length (lines)", "avg_function_length"),
        ("Test Files", "test_files"),
        ("Comment Density (%)", "comment_density_pct"),
        ("Docstring Coverage (%)", "docstring_coverage_pct"),
    ]
    data = {s.id: common.read_result("repo_stats", s.id) for s in subs}
    rows = [[label] + [data[s.id][key] for s in subs] for label, key in fields]
    _write_csv("table_repo_stats.csv", header, rows)


def table_correctness() -> None:
    subs = _subjects_with("correctness")
    for pair in ("flask", "django"):
        psubs = [s for s in subs if s.pair == pair]
        if not psubs:
            continue
        data = {s.id: common.read_result("correctness", s.id) for s in psubs}
        # union of categories, preserving first-seen order
        cats: list[str] = []
        for s in psubs:
            for c in data[s.id]["categories"]:
                if c not in cats:
                    cats.append(c)
        header = ["category", "N"] + [s.label for s in psubs]
        rows = []
        for c in cats:
            n = next((data[s.id]["categories"][c]["n"] for s in psubs
                      if c in data[s.id]["categories"]), 0)
            row = [c, n]
            for s in psubs:
                cell = data[s.id]["categories"].get(c)
                row.append(f"{cell['passed']} ({cell['pass_rate']}%)" if cell else "-")
            rows.append(row)
        total_row = ["Total", sum(data[psubs[0].id]["categories"][c]["n"] for c in cats
                                  if c in data[psubs[0].id]["categories"])]
        for s in psubs:
            d = data[s.id]
            total_row.append(f"{d['passed']} ({d['pass_rate']}%)")
        rows.append(total_row)
        _write_csv(f"table_correctness_{pair}.csv", header, rows)


def table_complexity() -> None:
    subs = _subjects_with("complexity")
    if not subs:
        return
    header = ["metric"] + [s.label for s in subs]
    data = {s.id: common.read_result("complexity", s.id) for s in subs}
    rows = [
        ["Mean CC"] + [data[s.id]["cc"]["mean"] for s in subs],
        ["Median CC"] + [data[s.id]["cc"]["median"] for s in subs],
        ["Max CC (single function)"] + [data[s.id]["cc"]["max"] for s in subs],
        ["Functions with CC > 10 (%)"] + [data[s.id]["cc"]["pct_over_threshold"] for s in subs],
        ["Mean CogC"] + [data[s.id]["cogc"]["mean"] for s in subs],
        ["Median CogC"] + [data[s.id]["cogc"]["median"] for s in subs],
        ["Max CogC (single function)"] + [data[s.id]["cogc"]["max"] for s in subs],
        ["Functions with CogC > 15 (%)"] + [data[s.id]["cogc"]["pct_over_threshold"] for s in subs],
    ]
    _write_csv("table_complexity.csv", header, rows)


def table_maintainability() -> None:
    subs = [s for s in common.load_subjects()
            if common.read_result("complexity", s.id) or common.read_result("smells", s.id)]
    if not subs:
        return
    header = ["metric"] + [s.label for s in subs]

    def mi(sid, key):
        r = common.read_result("complexity", sid)
        return r["mi"][key] if r else "-"

    def sm(sid, key):
        r = common.read_result("smells", sid)
        return r[key] if r else "-"

    rows = [
        ["Mean Maintainability Index"] + [mi(s.id, "mean") for s in subs],
        ["Files with MI < 65 (%)"] + [mi(s.id, "pct_below_threshold") for s in subs],
        ["pylint findings"] + [sm(s.id, "total_findings") for s in subs],
        ["pylint findings / 100 LOC"] + [sm(s.id, "per_100_loc") for s in subs],
    ]
    _write_csv("table_maintainability.csv", header, rows)


def table_security() -> None:
    subs = _subjects_with("security")
    if not subs:
        return
    header = ["metric"] + [s.label for s in subs]
    data = {s.id: common.read_result("security", s.id) for s in subs}
    rows = [
        ["Total findings (>= medium conf.)"] + [data[s.id]["total_findings"] for s in subs],
        ["Findings / kLOC"] + [data[s.id]["density_per_kloc"] for s in subs],
        ["High severity"] + [data[s.id]["by_severity"].get("HIGH", 0) for s in subs],
        ["Medium severity"] + [data[s.id]["by_severity"].get("MEDIUM", 0) for s in subs],
        ["Low severity"] + [data[s.id]["by_severity"].get("LOW", 0) for s in subs],
    ]
    cwes: list[str] = []
    for s in subs:
        for c in data[s.id]["by_cwe"]:
            if c not in cwes:
                cwes.append(c)
    for c in cwes:
        rows.append([f"  {c}"] + [data[s.id]["by_cwe"].get(c, 0) for s in subs])
    _write_csv("table_security.csv", header, rows)


def table_duplication() -> None:
    subs = _subjects_with("duplication")
    if not subs:
        return
    header = ["metric"] + [s.label for s in subs]
    data = {s.id: common.read_result("duplication", s.id) for s in subs}
    rows = [
        ["Duplicated blocks"] + [data[s.id]["duplicated_blocks"] for s in subs],
        ["Duplicated LOC"] + [data[s.id]["duplicated_loc"] for s in subs],
        ["Duplicated LOC (% of total)"] + [data[s.id]["duplicated_pct"] for s in subs],
        ["Max block size (tokens)"] + [data[s.id]["max_block_tokens"] for s in subs],
    ]
    _write_csv("table_duplication.csv", header, rows)


def summary() -> None:
    subs = common.load_subjects()
    header = ["subject", "label", "kind", "pair", "loc", "correctness_pct",
              "mean_cc", "mean_cogc", "mean_mi", "smells_per_100loc",
              "sec_per_kloc", "dup_pct"]
    rows = []
    any_data = False
    for s in subs:
        stats = common.read_result("repo_stats", s.id)
        corr = common.read_result("correctness", s.id)
        cx = common.read_result("complexity", s.id)
        sm = common.read_result("smells", s.id)
        sec = common.read_result("security", s.id)
        dup = common.read_result("duplication", s.id)
        if not any([stats, corr, cx, sm, sec, dup]):
            continue
        any_data = True
        rows.append([
            s.id, s.label, s.kind, s.pair,
            stats["loc"] if stats else "-",
            corr["pass_rate"] if corr else "-",
            cx["cc"]["mean"] if cx else "-",
            cx["cogc"]["mean"] if cx else "-",
            cx["mi"]["mean"] if cx else "-",
            sm["per_100_loc"] if sm else "-",
            sec["density_per_kloc"] if sec else "-",
            dup["duplicated_pct"] if dup else "-",
        ])
    if any_data:
        _write_csv("summary.csv", header, rows)


def run() -> None:
    table_repo_stats()
    table_correctness()
    table_complexity()
    table_maintainability()
    table_security()
    table_duplication()
    summary()


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    run()
