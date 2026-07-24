"""Read per-subject result JSON and render the paper tables as CSV.

Outputs (under results/tables/):
  table_repo_stats.csv         structural characteristics (all subjects)
  table_correctness_<pair>.csv RQ1 per-category pass rates + Fisher's exact p
                                (paper Table 2)
  table_complexity.csv         RQ2 CC + CogC summary + Mann-Whitney p /
                                rank-biserial r (paper Table 3)
  table_maintainability.csv    RQ3 MI + pylint smell density + Mann-Whitney
                                p / rank-biserial r on MI (paper Table 4)
  table_security.csv           RQ4 finding density, severity, CWE mix +
                                Fisher's exact p per severity (paper Table 5)
  table_cwe_<pair>.csv         RQ4 Bandit-ID -> CWE breakdown (paper Table 6)
  table_duplication.csv        RQ5 duplication summary + Mann-Whitney p /
                                rank-biserial r (paper Table 7)
  table_quality_gap_<id>.csv   cross-dimension delta, one agentic subject vs.
                                its pair's human baseline (paper Tables 8-9)
  summary.csv                  one row per subject, headline numbers for
                                every RQ

Statistical tests (Mann-Whitney U for per-function/per-file distributions,
Fisher's exact for pass/fail and severity counts; both two-sided, alpha =
0.05) are produced by ``analysis/significance.py`` and read from
``results/significance/<agentic_id>.json``; a cell reads "ref." for the human
baseline itself and "-" where no upstream data was available for the test.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import common, security as security_mod

TABLES_DIR = common.RESULTS_DIR / "tables"


def _subjects_with(dimension: str) -> list[common.Subject]:
    return [s for s in common.load_subjects()
            if common.read_result(dimension, s.id) is not None]


def _write_csv(name: str, header: list[str], rows: list[list]) -> Path:
    import csv
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    path = TABLES_DIR / name
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"[aggregate] wrote {path.relative_to(common.REPO_ROOT)}")
    return path


# --------------------------------------------------------------------------- #
# Significance lookup / formatting helpers                                    #
# --------------------------------------------------------------------------- #

def _fmt_p(p) -> str:
    if p is None:
        return "-"
    if p < 0.0001:
        return "<0.0001"
    return f"{p:.4f}"


def _fmt_r(r) -> str:
    return "-" if r is None else f"{r:+.3f}"


def _sig(subject_id: str) -> dict | None:
    return common.read_result("significance", subject_id)


def _sig_cell(subject: common.Subject, dim: str, metric: str, field: str, fmt) -> str:
    """One cell of a significance row: 'ref.' for the human baseline itself,
    '-' if no test could be run, else the formatted p / effect size."""
    if subject.kind == "human":
        return "ref."
    sig = _sig(subject.id)
    if not sig or dim not in sig or metric not in sig[dim]:
        return "-"
    return fmt(sig[dim][metric].get(field))


# --------------------------------------------------------------------------- #
# Paper Table: Structural characteristics                                     #
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# Paper Table 2: Oracle correctness + Fisher's exact                          #
# --------------------------------------------------------------------------- #

def table_correctness() -> None:
    subs = _subjects_with("correctness")
    for pair in ("flask", "django"):
        psubs = [s for s in subs if s.pair == pair]
        if not psubs:
            continue
        data = {s.id: common.read_result("correctness", s.id) for s in psubs}
        cats: list[str] = []
        for s in psubs:
            for c in data[s.id]["categories"]:
                if c not in cats:
                    cats.append(c)

        human = next((s for s in psubs if s.kind == "human"), None)
        agentic_list = [s for s in psubs if s.kind == "agentic"]
        p_cols = [f"Fisher's exact p ({s.label} vs. {human.label})" for s in agentic_list] if human else []
        header = ["category", "N"] + [s.label for s in psubs] + p_cols

        def p_cells(category_key: str) -> list[str]:
            if not human:
                return []
            out = []
            for s in agentic_list:
                sig = _sig(s.id)
                cell = (sig or {}).get("correctness", {}).get(category_key)
                out.append(_fmt_p(cell["p"]) if cell else "-")
            return out

        rows = []
        for c in cats:
            n = next((data[s.id]["categories"][c]["n"] for s in psubs
                      if c in data[s.id]["categories"]), 0)
            row = [c, n]
            for s in psubs:
                cell = data[s.id]["categories"].get(c)
                row.append(f"{cell['passed']} ({cell['pass_rate']}%)" if cell else "-")
            row += p_cells(c)
            rows.append(row)

        total_row = ["Total", sum(data[psubs[0].id]["categories"][c]["n"] for c in cats
                                  if c in data[psubs[0].id]["categories"])]
        for s in psubs:
            d = data[s.id]
            total_row.append(f"{d['passed']} ({d['pass_rate']}%)")
        total_row += p_cells("Total")
        rows.append(total_row)
        _write_csv(f"table_correctness_{pair}.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Table 3: Complexity + Mann-Whitney                                    #
# --------------------------------------------------------------------------- #

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
        ["Mann-Whitney U p (CC vs. human baseline)"]
            + [_sig_cell(s, "complexity", "cc", "p", _fmt_p) for s in subs],
        ["Rank-biserial r (CC)"]
            + [_sig_cell(s, "complexity", "cc", "rank_biserial", _fmt_r) for s in subs],
        ["Mean CogC"] + [data[s.id]["cogc"]["mean"] for s in subs],
        ["Median CogC"] + [data[s.id]["cogc"]["median"] for s in subs],
        ["Max CogC (single function)"] + [data[s.id]["cogc"]["max"] for s in subs],
        ["Functions with CogC > 15 (%)"] + [data[s.id]["cogc"]["pct_over_threshold"] for s in subs],
        ["Mann-Whitney U p (CogC vs. human baseline)"]
            + [_sig_cell(s, "complexity", "cogc", "p", _fmt_p) for s in subs],
        ["Rank-biserial r (CogC)"]
            + [_sig_cell(s, "complexity", "cogc", "rank_biserial", _fmt_r) for s in subs],
    ]
    _write_csv("table_complexity.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Table 4: Maintainability Index + pylint + Mann-Whitney on MI          #
# --------------------------------------------------------------------------- #

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

    def sm_cat(sid, cat):
        r = common.read_result("smells", sid)
        return r["by_category"].get(cat, 0) if r else "-"

    rows = [
        ["Mean Maintainability Index"] + [mi(s.id, "mean") for s in subs],
        ["Median Maintainability Index"] + [mi(s.id, "median") for s in subs],
        ["Files with MI < 65 (%)"] + [mi(s.id, "pct_below_threshold") for s in subs],
        ["Min file MI"] + [mi(s.id, "min") for s in subs],
        ["Mann-Whitney U p (MI vs. human baseline)"]
            + [_sig_cell(s, "maintainability", "mi", "p", _fmt_p) for s in subs],
        ["Rank-biserial r (MI)"]
            + [_sig_cell(s, "maintainability", "mi", "rank_biserial", _fmt_r) for s in subs],
        ["Total pylint findings"] + [sm(s.id, "total_findings") for s in subs],
        ["Convention violations (C)"] + [sm_cat(s.id, "convention") for s in subs],
        ["Refactoring suggestions (R)"] + [sm_cat(s.id, "refactor") for s in subs],
        ["Warnings (W)"] + [sm_cat(s.id, "warning") for s in subs],
        ["Error-category findings (E)"] + [sm_cat(s.id, "error") for s in subs],
        ["Findings / 100 LOC"] + [sm(s.id, "per_100_loc") for s in subs],
    ]
    _write_csv("table_maintainability.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Table 5: Security findings by severity + Fisher's exact               #
# --------------------------------------------------------------------------- #

def table_security() -> None:
    subs = _subjects_with("security")
    if not subs:
        return
    header = ["metric"] + [s.label for s in subs]
    data = {s.id: common.read_result("security", s.id) for s in subs}
    rows = [
        ["Total findings (>= medium conf.)"] + [data[s.id]["total_findings"] for s in subs],
        ["Findings / 100 LOC"] + [data[s.id]["density_per_100_loc"] for s in subs],
        ["High severity"] + [data[s.id]["by_severity"].get("HIGH", 0) for s in subs],
        ["Fisher's exact p (High vs. human baseline)"]
            + [_sig_cell(s, "security", "HIGH", "p", _fmt_p) for s in subs],
        ["Medium severity"] + [data[s.id]["by_severity"].get("MEDIUM", 0) for s in subs],
        ["Fisher's exact p (Medium vs. human baseline)"]
            + [_sig_cell(s, "security", "MEDIUM", "p", _fmt_p) for s in subs],
        ["Low severity"] + [data[s.id]["by_severity"].get("LOW", 0) for s in subs],
        ["Fisher's exact p (Low vs. human baseline)"]
            + [_sig_cell(s, "security", "LOW", "p", _fmt_p) for s in subs],
    ]
    cwes: list[str] = []
    for s in subs:
        for c in data[s.id]["by_cwe"]:
            if c not in cwes:
                cwes.append(c)
    for c in cwes:
        rows.append([f"  {c}"] + [data[s.id]["by_cwe"].get(c, 0) for s in subs])
    _write_csv("table_security.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Table 6: Bandit-ID -> CWE classification, per pair                    #
# --------------------------------------------------------------------------- #

def table_cwe() -> None:
    subs = _subjects_with("security")
    # Canonical ordering follows the paper's Table 6; anything else observed
    # (a CWE this study didn't call out by name) is appended after.
    canonical_order = ["CWE-78", "CWE-617", "CWE-259", "CWE-330",
                        "CWE-327", "CWE-295", "CWE-89"]
    for pair in ("flask", "django"):
        psubs = [s for s in subs if s.pair == pair]
        if not psubs:
            continue
        data = {s.id: common.read_result("security", s.id) for s in psubs}

        ids_by_cwe: dict[str, set[str]] = {}
        for s in psubs:
            for f in data[s.id]["findings"]:
                if f["test_id"] in security_mod.CWE_MAP:
                    ids_by_cwe.setdefault(f["cwe"], set()).add(f["test_id"])
        mapped_cwes = set(ids_by_cwe)

        def count(sid: str, cwe: str) -> int:
            return sum(1 for f in data[sid]["findings"] if f["cwe"] == cwe)

        def other_count(sid: str) -> int:
            return sum(1 for f in data[sid]["findings"]
                       if (f["cwe"] or "unmapped") not in mapped_cwes)

        ordered = [c for c in canonical_order if c in ids_by_cwe]
        ordered += sorted(c for c in ids_by_cwe if c not in canonical_order)

        header = ["Bandit ID", "CWE"] + [s.label for s in psubs]
        rows = []
        for cwe in ordered:
            bandit_ids = "/".join(sorted(ids_by_cwe[cwe]))
            rows.append([bandit_ids, cwe] + [count(s.id, cwe) for s in psubs])
        rows.append(["Other", "Various"] + [other_count(s.id) for s in psubs])
        rows.append(["Total", ""] + [data[s.id]["total_findings"] for s in psubs])
        _write_csv(f"table_cwe_{pair}.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Table 7: Duplication + Mann-Whitney                                   #
# --------------------------------------------------------------------------- #

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
        ["Mann-Whitney U p (Duplicated % vs. human baseline, per-file)"]
            + [_sig_cell(s, "duplication", "duplicated_pct", "p", _fmt_p) for s in subs],
        ["Rank-biserial r (Duplicated %)"]
            + [_sig_cell(s, "duplication", "duplicated_pct", "rank_biserial", _fmt_r) for s in subs],
        ["Max block size (tokens)"] + [data[s.id]["max_block_tokens"] for s in subs],
    ]
    _write_csv("table_duplication.csv", header, rows)


# --------------------------------------------------------------------------- #
# Paper Tables 8-9: cross-repository quality-gap summary                      #
# --------------------------------------------------------------------------- #

def _pct_delta(agentic: float, human: float) -> str:
    if not human:
        return "-"
    return f"{100.0 * (agentic - human) / human:+.0f}%"


def _pt_delta(agentic: float, human: float, unit: str) -> str:
    return f"{(agentic - human):+.1f} {unit}"


def table_quality_gap() -> None:
    subs = common.load_subjects()
    by_pair: dict[str, list[common.Subject]] = {}
    for s in subs:
        by_pair.setdefault(s.pair, []).append(s)

    for pair, members in by_pair.items():
        humans = [s for s in members if s.kind == "human" and s.is_present()]
        if not humans:
            continue
        human = humans[0]
        h_corr = common.read_result("correctness", human.id)
        h_cx = common.read_result("complexity", human.id)
        h_sec = common.read_result("security", human.id)
        h_dup = common.read_result("duplication", human.id)
        if not all([h_corr, h_cx, h_sec, h_dup]):
            continue

        for agentic in members:
            if agentic.kind != "agentic" or not agentic.is_present():
                continue
            a_corr = common.read_result("correctness", agentic.id)
            a_cx = common.read_result("complexity", agentic.id)
            a_sec = common.read_result("security", agentic.id)
            a_dup = common.read_result("duplication", agentic.id)
            if not all([a_corr, a_cx, a_sec, a_dup]):
                continue

            header = ["Dimension", human.label, agentic.label, "Delta"]
            rows = [
                ["Oracle pass rate (%)", h_corr["pass_rate"], a_corr["pass_rate"],
                 _pt_delta(a_corr["pass_rate"], h_corr["pass_rate"], "pp")],
                ["Mean CC", h_cx["cc"]["mean"], a_cx["cc"]["mean"],
                 _pct_delta(a_cx["cc"]["mean"], h_cx["cc"]["mean"])],
                ["Mean CogC", h_cx["cogc"]["mean"], a_cx["cogc"]["mean"],
                 _pct_delta(a_cx["cogc"]["mean"], h_cx["cogc"]["mean"])],
                ["Mean MI", h_cx["mi"]["mean"], a_cx["mi"]["mean"],
                 _pt_delta(a_cx["mi"]["mean"], h_cx["mi"]["mean"], "pts")],
                ["Security findings / 100 LOC", h_sec["density_per_100_loc"], a_sec["density_per_100_loc"],
                 _pct_delta(a_sec["density_per_100_loc"], h_sec["density_per_100_loc"])],
                ["Duplicated LOC (%)", h_dup["duplicated_pct"], a_dup["duplicated_pct"],
                 _pct_delta(a_dup["duplicated_pct"], h_dup["duplicated_pct"])],
            ]
            _write_csv(f"table_quality_gap_{agentic.id}.csv", header, rows)


# --------------------------------------------------------------------------- #
# Headline summary                                                            #
# --------------------------------------------------------------------------- #

def summary() -> None:
    subs = common.load_subjects()
    header = ["subject", "label", "kind", "pair", "loc", "correctness_pct",
              "mean_cc", "mean_cogc", "mean_mi", "smells_per_100loc",
              "sec_per_100loc", "dup_pct"]
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
            sec["density_per_100_loc"] if sec else "-",
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
    table_cwe()
    table_duplication()
    table_quality_gap()
    summary()


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    run()
