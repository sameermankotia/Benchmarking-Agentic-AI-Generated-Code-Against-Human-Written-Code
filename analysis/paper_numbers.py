"""Compute every number the paper reports, from the committed artifacts.

The paper quotes medians and ranges over the five generation runs of each
configuration, ratios between a configuration and its human baseline, counts of
runs that differ significantly from that baseline, and a handful of generation
facts (model calls, cost, wall-clock, agent steps). None of those is a stage
output: each is an aggregation over the per-subject JSON in ``results/``, over
the oracle's JUnit reports, or over the frozen generation traces.

This module is where that aggregation happens, so that no number in the paper
is computed by hand. It writes one file:

    results/paper_numbers.json

keyed by paper element -- ``table_repo_stats``, ``rq1_correctness``, ...,
``generation``, ``claims`` -- with the figure, its range over the runs, and the
inputs it came from. ``--check`` recomputes and compares against the committed
file instead of writing it, which is how the replication package verifies that
the shipped numbers are the ones its own code produces.

Reads, and nothing else:

* ``results/{repo_stats,correctness,complexity,smells,security,duplication,
  significance}/<subject>.json`` -- the stage outputs
* ``results/correctness/<subject>.junit.xml`` -- per-case pass/fail, needed for
  the failures that recur across every run of a configuration
* ``generation/runs/MANIFEST.json`` and the frozen traces under
  ``generation/runs/`` -- per-run cost, model calls, wall-clock, agent steps
* the subjects themselves, for per-file line counts (the size-matched
  Maintainability Index control)

Stdlib only: it must run even where the analysis toolchain is not installed.

Usage:
    python -m analysis.paper_numbers            # write results/paper_numbers.json
    python -m analysis.paper_numbers --check    # verify the committed file
    python -m analysis.paper_numbers --print    # human-readable summary
"""

from __future__ import annotations

import argparse
import ast
import gzip
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from . import common

OUT_PATH = common.RESULTS_DIR / "paper_numbers.json"
GENERATION_DIR = common.REPO_ROOT / "generation" / "runs"
RUN_SUFFIX = re.compile(r"_run\d+$")

#: Each agentic configuration and the human baseline it is compared against.
PAIR_BASELINE = {"flask": "flask", "django": "django"}

#: The maturity reference point (paper §III-B3): structural metrics only.
MATURITY_ID = "flask_0_1"


# --------------------------------------------------------------------------- #
# Small aggregation helpers                                                   #
# --------------------------------------------------------------------------- #

def _round(value, digits: int = 2):
    return None if value is None else round(float(value), digits)


def mr(values: list[float], digits: int = 2) -> dict | None:
    """Median with the observed range -- the paper's ``median [min, max]``."""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return {"median": _round(common.median(vals), digits),
            "min": _round(min(vals), digits),
            "max": _round(max(vals), digits),
            "n": len(vals)}


def ratio(agentic, human, digits: int = 2):
    """Agentic / human, guarding a zero baseline."""
    if agentic is None or human in (None, 0):
        return None
    return _round(agentic / human, digits)


def _pick(d: dict, *path, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


# --------------------------------------------------------------------------- #
# Subject / configuration inventory                                           #
# --------------------------------------------------------------------------- #

class Inventory:
    """The study's subjects, grouped into the paper's configurations."""

    DIMENSIONS = ("repo_stats", "correctness", "complexity", "smells",
                  "security", "duplication")

    def __init__(self) -> None:
        self.subjects = {s.id: s for s in common.load_subjects()
                         if s.is_present()}
        self.results: dict[str, dict[str, dict]] = {}
        for sid in self.subjects:
            self.results[sid] = {
                dim: common.read_result(dim, sid) for dim in self.DIMENSIONS}
            self.results[sid]["significance"] = common.read_result(
                "significance", sid)

        self.configs: dict[str, list[str]] = {}
        for sid, subject in self.subjects.items():
            if subject.kind != "agentic":
                continue
            self.configs.setdefault(RUN_SUFFIX.sub("", sid), []).append(sid)
        for runs in self.configs.values():
            runs.sort()

        self.generation = self._load_generation()

    @staticmethod
    def _load_generation() -> dict:
        path = GENERATION_DIR / "MANIFEST.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    # --- lookups ----------------------------------------------------------- #

    def result(self, sid: str, dimension: str) -> dict:
        return self.results.get(sid, {}).get(dimension) or {}

    def baseline_of(self, config: str) -> str:
        pair = self.subjects[self.configs[config][0]].pair
        return PAIR_BASELINE[pair]

    def across(self, config: str, fn) -> list:
        """`fn` applied to every run of `config`, in run order."""
        return [fn(sid) for sid in self.configs[config]]

    def config_meta(self, config: str) -> dict:
        runs = self.configs[config]
        declared = next((c for c in self.generation.get("configurations", [])
                         if c.get("id") == config), {})
        return {
            "runs": runs,
            "n_runs": len(runs),
            "label": declared.get("label") or self.subjects[runs[0]].label,
            "agent": declared.get("agent"),
            "model": declared.get("model"),
            "spec": declared.get("spec") or self.subjects[runs[0]].pair,
            "pair": self.subjects[runs[0]].pair,
            "baseline": self.baseline_of(config),
        }


# --------------------------------------------------------------------------- #
# Table 2 -- structural characteristics of the subjects                       #
# --------------------------------------------------------------------------- #

REPO_STAT_ROWS = ("loc", "source_files", "functions", "classes",
                  "avg_function_length", "comment_density_pct",
                  "docstring_coverage_pct")


def _files_outside_scope(subject: common.Subject) -> int:
    """Python files the agent left outside the measured package.

    The analysis scope is the framework package the agent created; the example
    applications, ad-hoc test files and debugging scripts it left beside that
    package are excluded (paper §III-B7). This counts what was excluded, which
    is the only way the paper's figure for it can be checked.
    """
    in_scope = set(subject.python_files())
    skip = {"__pycache__", ".git"}
    return sum(1 for path in subject.root.rglob("*.py")
               if not skip & set(path.parts) and path not in in_scope)


def table_repo_stats(inv: Inventory) -> dict:
    out: dict = {"human": {}, "agentic": {}, "size_ratio": {}}
    for sid, subject in inv.subjects.items():
        if subject.kind != "human":
            continue
        stats = inv.result(sid, "repo_stats")
        out["human"][sid] = {row: stats.get(row) for row in REPO_STAT_ROWS}
    for config in inv.configs:
        out["agentic"][config] = {
            row: mr(inv.across(config,
                               lambda s, r=row: inv.result(s, "repo_stats").get(r)), 1)
            for row in REPO_STAT_ROWS}
        outside = {sid: _files_outside_scope(inv.subjects[sid])
                   for sid in inv.configs[config]}
        out["agentic"][config]["files_outside_scope"] = dict(
            mr(list(outside.values()), 1) or {}, per_run=outside)
        base_loc = inv.result(inv.baseline_of(config), "repo_stats").get("loc")
        ratios = inv.across(
            config,
            lambda s, b=base_loc: ratio(b, inv.result(s, "repo_stats").get("loc"), 1))
        out["size_ratio"][config] = {
            "baseline": inv.baseline_of(config),
            "baseline_loc": base_loc,
            "times_smaller": mr([r for r in ratios if r is not None], 1),
        }
    smaller = [v["times_smaller"] for v in out["size_ratio"].values()
               if v["times_smaller"]]
    out["size_ratio"]["across_configurations"] = {
        "times_smaller_min": _round(min(s["min"] for s in smaller), 1) if smaller else None,
        "times_smaller_max": _round(max(s["max"] for s in smaller), 1) if smaller else None,
        "times_smaller_median_min": _round(min(s["median"] for s in smaller), 1) if smaller else None,
        "times_smaller_median_max": _round(max(s["median"] for s in smaller), 1) if smaller else None,
    }
    return out


# --------------------------------------------------------------------------- #
# RQ1 -- functional correctness                                               #
# --------------------------------------------------------------------------- #

def _junit_cases(subject_id: str) -> dict[str, bool]:
    """``{case name: passed}`` from one subject's JUnit report."""
    path = common.RESULTS_DIR / "correctness" / f"{subject_id}.junit.xml"
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    cases: dict[str, bool] = {}
    for suite in (root.findall("testsuite") or [root]):
        for case in suite.findall("testcase"):
            stem = Path(case.get("file") or "").stem
            name = f"{stem}::{case.get('name')}" if stem else case.get("name", "")
            failed = (case.find("failure") is not None
                      or case.find("error") is not None
                      or case.find("skipped") is not None)
            cases[name] = not failed
    return cases


def rq1_correctness(inv: Inventory) -> dict:
    out: dict = {"suite_size": {}, "human": {}, "agentic": {}}
    out["suite_composition"] = {}
    for sid, subject in inv.subjects.items():
        res = inv.result(sid, "correctness")
        if not res:
            continue
        if subject.oracle:
            out["suite_size"][subject.oracle] = res.get("total")
            # Cases per behavioural category: a property of the suite, so it is
            # read off the pair's own baseline and is the same for every
            # subject of that pair.
            if subject.kind == "human":
                out["suite_composition"][subject.oracle] = {
                    cat: c["n"] for cat, c in sorted(
                        (res.get("categories") or {}).items())}
        if subject.kind == "human":
            out["human"][sid] = {
                "passed": res.get("passed"), "total": res.get("total"),
                "skipped": res.get("skipped"), "pass_rate_pct": res.get("pass_rate"),
                "categories": {k: v.get("pass_rate")
                               for k, v in (res.get("categories") or {}).items()},
            }

    for config in inv.configs:
        rates = inv.across(config, lambda s: inv.result(s, "correctness").get("pass_rate"))
        passed = inv.across(config, lambda s: inv.result(s, "correctness").get("passed"))
        totals = {inv.result(s, "correctness").get("total")
                  for s in inv.configs[config]}
        baseline = inv.baseline_of(config)
        base_rate = inv.result(baseline, "correctness").get("pass_rate")
        categories = sorted({
            cat for s in inv.configs[config]
            for cat in (inv.result(s, "correctness").get("categories") or {})})
        cases = {s: _junit_cases(s) for s in inv.configs[config]}
        always_failing = sorted(
            name for name in set().union(*(set(c) for c in cases.values()))
            if all(not per_run.get(name, False) for per_run in cases.values()))
        out["agentic"][config] = {
            "pass_rate_pct": mr(rates, 1),
            "passed_cases": mr(passed, 1),
            "suite_size": sorted(t for t in totals if t is not None),
            "per_run_pass_rate_pct": dict(zip(inv.configs[config], rates)),
            "baseline": baseline,
            "baseline_pass_rate_pct": base_rate,
            "median_deficit_pp": _round(
                (mr(rates, 1) or {}).get("median", 0) - (base_rate or 0), 1),
            "per_category_pass_rate_pct": {
                cat: mr(inv.across(
                    config,
                    lambda s, c=cat: _pick(inv.result(s, "correctness"),
                                           "categories", c, "pass_rate")), 1)
                for cat in categories},
            "cases_failing_in_every_run": always_failing,
            "n_cases_failing_in_every_run": len(always_failing),
            "runs_differing_from_baseline": sum(
                1 for s in inv.configs[config]
                if _pick(inv.result(s, "significance"), "correctness", "Total",
                         "significant") is True),
        }

    return out


# --------------------------------------------------------------------------- #
# RQ2 -- complexity                                                           #
# --------------------------------------------------------------------------- #

def _complexity_row(res: dict) -> dict:
    return {
        "mean_cc": _pick(res, "cc", "mean"),
        "median_cc": _pick(res, "cc", "median"),
        "max_cc": _pick(res, "cc", "max"),
        "pct_cc_over_threshold": _pick(res, "cc", "pct_over_threshold"),
        "mean_cogc": _pick(res, "cogc", "mean"),
        "median_cogc": _pick(res, "cogc", "median"),
        "max_cogc": _pick(res, "cogc", "max"),
        "pct_cogc_over_threshold": _pick(res, "cogc", "pct_over_threshold"),
        "n_functions_cc": _pick(res, "cc", "n"),
        "n_functions_cogc": _pick(res, "cogc", "n"),
    }


def rq2_complexity(inv: Inventory) -> dict:
    out: dict = {"human": {}, "agentic": {}, "thresholds": {}}
    for sid, subject in inv.subjects.items():
        res = inv.result(sid, "complexity")
        if not res:
            continue
        out["thresholds"] = {"cc": _pick(res, "cc", "threshold"),
                             "cogc": _pick(res, "cogc", "threshold")}
        if subject.kind == "human":
            out["human"][sid] = _complexity_row(res)
    for config in inv.configs:
        baseline = inv.baseline_of(config)
        base = _complexity_row(inv.result(baseline, "complexity"))
        rows = inv.across(config, lambda s: _complexity_row(inv.result(s, "complexity")))
        agg = {key: mr([r[key] for r in rows], 2) for key in base}
        out["agentic"][config] = dict(
            agg,
            baseline=baseline,
            relative_to_baseline_pct={
                key: (None if base[key] in (None, 0) or agg[key] is None
                      else _round(100.0 * (agg[key]["median"] - base[key]) / base[key], 1))
                for key in ("mean_cc", "mean_cogc")},
            runs_differing_from_baseline={
                metric: sum(
                    1 for s in inv.configs[config]
                    if _pick(inv.result(s, "significance"), "complexity", metric,
                             "significant") is True)
                for metric in ("cc", "cogc")},
        )
    return out


# --------------------------------------------------------------------------- #
# RQ3 -- maintainability (MI, size-matched MI, code smells)                   #
# --------------------------------------------------------------------------- #

#: LOC bands for the size-matched Maintainability Index control.
MI_BANDS = ((0, 50), (50, 100), (100, 200), (200, 400), (400, None))


def _file_loc(subject: common.Subject) -> dict[str, int]:
    """Per-file SLOC over the subject's analysis scope, keyed as results/ keys it."""
    out = {}
    for path in subject.python_files():
        rel = path.relative_to(subject.root).as_posix()
        out[rel] = common.loc_for_file(path).loc
    return out


def _mi_with_loc(inv: Inventory, sid: str) -> list[tuple[int, float]]:
    mi_files = _pick(inv.result(sid, "complexity"), "mi", "files", default=[]) or []
    locs = _file_loc(inv.subjects[sid])
    return [(locs[f["file"]], f["mi"]) for f in mi_files if f["file"] in locs]


def _band_label(lo, hi) -> str:
    return f"{lo}-{hi}" if hi is not None else f"{lo}+"


def size_matched_mi(inv: Inventory, config: str) -> dict:
    """Compare MI only between files of comparable size.

    Radon computes the Maintainability Index per file, and its formula falls
    with file length, so a repository of small files scores higher than a
    repository of large ones whatever either contains. The control is therefore
    to compare like with like, in two ways:

    * ``matched``: the human baseline is restricted to the files whose SLOC
      falls inside the range spanned by the configuration's own files, and the
      two medians are compared on that common footing;
    * ``bands``: both are reported per LOC band, so the comparison can be read
      at every size rather than only in aggregate.

    This is the package's definition of the control; it is stated here because
    the paper's text describes the comparison, not its implementation.
    """
    baseline = inv.baseline_of(config)
    human = _mi_with_loc(inv, baseline)
    agentic = [pair for sid in inv.configs[config] for pair in _mi_with_loc(inv, sid)]
    if not human or not agentic:
        return {}
    lo = min(loc for loc, _ in agentic)
    hi = max(loc for loc, _ in agentic)
    matched_human = [mi for loc, mi in human if lo <= loc <= hi]
    bands = {}
    for band_lo, band_hi in MI_BANDS:
        def inside(pairs):
            return [mi for loc, mi in pairs
                    if loc >= band_lo and (band_hi is None or loc < band_hi)]
        a, h = inside(agentic), inside(human)
        bands[_band_label(band_lo, band_hi)] = {
            "agentic_median_mi": _round(common.median(a), 1) if a else None,
            "agentic_files": len(a),
            "human_median_mi": _round(common.median(h), 1) if h else None,
            "human_files": len(h),
        }
    return {
        "baseline": baseline,
        "agentic_file_loc_range": [lo, hi],
        "agentic_files": len(agentic),
        "agentic_median_mi": _round(common.median([mi for _, mi in agentic]), 1),
        "human_files_all": len(human),
        "human_median_mi_all": _round(common.median([mi for _, mi in human]), 1),
        "human_files_in_range": len(matched_human),
        "human_median_mi_in_range": (_round(common.median(matched_human), 1)
                                     if matched_human else None),
        "median_mi_gap_matched": (
            _round(common.median([mi for _, mi in agentic]) - common.median(matched_human), 1)
            if matched_human else None),
        "bands": bands,
    }


def _smells_row(res: dict) -> dict:
    total = res.get("total_findings")
    symbols = res.get("top_symbols") or {}
    whitespace = sum(v for k, v in symbols.items()
                     if k in ("trailing-whitespace", "trailing-newlines",
                              "missing-final-newline", "line-too-long",
                              "superfluous-parens", "bad-indentation",
                              "mixed-line-endings", "unnecessary-semicolon"))
    cosmetic_only = symbols.get("trailing-whitespace", 0)
    return {
        "total_findings": total,
        "per_100_loc": res.get("per_100_loc"),
        "by_category": res.get("by_category") or {},
        "trailing_whitespace": cosmetic_only,
        "trailing_whitespace_share_pct": (
            _round(100.0 * cosmetic_only / total, 1) if total else None),
        "whitespace_family": whitespace,
        "whitespace_family_share_pct": (
            _round(100.0 * whitespace / total, 1) if total else None),
        "non_cosmetic_per_100_loc": (
            _round((res.get("per_100_loc") or 0) * (total - cosmetic_only) / total, 2)
            if total else None),
    }


def rq3_maintainability(inv: Inventory) -> dict:
    out: dict = {"human": {}, "agentic": {}}
    for sid, subject in inv.subjects.items():
        if subject.kind != "human":
            continue
        cx, sm = inv.result(sid, "complexity"), inv.result(sid, "smells")
        out["human"][sid] = {
            "mean_mi": _pick(cx, "mi", "mean"),
            "median_mi": _pick(cx, "mi", "median"),
            "min_mi": _pick(cx, "mi", "min"),
            "pct_mi_below_threshold": _pick(cx, "mi", "pct_below_threshold"),
            "smells": _smells_row(sm),
        }
    for config in inv.configs:
        baseline = inv.baseline_of(config)
        base_density = _pick(inv.result(baseline, "smells"), "per_100_loc")
        rows = inv.across(config, lambda s: _smells_row(inv.result(s, "smells")))
        out["agentic"][config] = {
            "baseline": baseline,
            "mean_mi": mr(inv.across(config, lambda s: _pick(
                inv.result(s, "complexity"), "mi", "mean")), 1),
            "median_mi": mr(inv.across(config, lambda s: _pick(
                inv.result(s, "complexity"), "mi", "median")), 1),
            "pct_mi_below_threshold": mr(inv.across(config, lambda s: _pick(
                inv.result(s, "complexity"), "mi", "pct_below_threshold")), 1),
            "runs_differing_from_baseline_mi": sum(
                1 for s in inv.configs[config]
                if _pick(inv.result(s, "significance"), "maintainability", "mi",
                         "significant") is True),
            "size_matched_mi": size_matched_mi(inv, config),
            "smells_per_100_loc": mr([r["per_100_loc"] for r in rows], 2),
            "smells_total": mr([r["total_findings"] for r in rows], 1),
            "smells_ratio_to_baseline_at_median": ratio(
                (mr([r["per_100_loc"] for r in rows], 2) or {}).get("median"),
                base_density, 1),
            "trailing_whitespace_share_pct": mr(
                [r["trailing_whitespace_share_pct"] for r in rows], 1),
            "non_cosmetic_per_100_loc": mr(
                [r["non_cosmetic_per_100_loc"] for r in rows], 2),
        }
    ratios = [v["smells_ratio_to_baseline_at_median"]
              for v in out["agentic"].values()
              if v["smells_ratio_to_baseline_at_median"]]
    out["smells_ratio_across_configurations"] = {
        "min": _round(min(ratios), 1) if ratios else None,
        "max": _round(max(ratios), 1) if ratios else None,
    }
    return out


# --------------------------------------------------------------------------- #
# RQ4 -- security findings                                                    #
# --------------------------------------------------------------------------- #

def _autoescape_state(subject: common.Subject) -> str:
    """Whether this subject turns Jinja2's autoescaping on: on | off | absent.

    Bandit does not flag this, and the oracle cannot: a subject whose rendering
    fails outright emits no markup to escape, so the oracle's autoescaping case
    passes vacuously. The default is read where it is set -- at the Jinja2
    ``Environment`` construction, which is off unless ``autoescape`` is passed.
    A subject that never builds an environment has no templating at all, which
    is a different finding and is reported as ``absent``.
    """
    on = off = 0
    for path in subject.python_files():
        try:
            tree = ast.parse(path.read_bytes())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else getattr(func, "id", ""))
            if name != "Environment":
                continue
            keyword = next((kw for kw in node.keywords
                            if kw.arg == "autoescape"), None)
            disabled = (keyword is None
                        or (isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is False))
            if disabled:
                off += 1
            else:
                on += 1
    if not on and not off:
        return "absent"
    return "off" if off else "on"


def jinja2_autoescaping(inv: Inventory) -> dict:
    """Per-run Jinja2 autoescaping state, over the runs whose spec names Jinja2."""
    states = {}
    for config, runs in sorted(inv.configs.items()):
        if inv.subjects[runs[0]].pair != "flask":
            continue          # only the Flask specification names Jinja2
        for sid in runs:
            states[sid] = _autoescape_state(inv.subjects[sid])
    if not states:
        return {}
    return {
        "per_run": states,
        "runs_examined": len(states),
        "runs_with_autoescaping_off": sum(1 for v in states.values() if v == "off"),
        "runs_with_autoescaping_on": sum(1 for v in states.values() if v == "on"),
        "runs_without_templating": sum(1 for v in states.values() if v == "absent"),
    }


def rq4_security(inv: Inventory) -> dict:
    out: dict = {"human": {}, "agentic": {}, "min_confidence": None,
                 "jinja2_autoescaping": jinja2_autoescaping(inv)}
    for sid, subject in inv.subjects.items():
        res = inv.result(sid, "security")
        if not res:
            continue
        out["min_confidence"] = res.get("min_confidence")
        if subject.kind == "human":
            out["human"][sid] = {
                "total_findings": res.get("total_findings"),
                "density_per_100_loc": res.get("density_per_100_loc"),
                "by_severity": res.get("by_severity") or {},
                "by_cwe": res.get("by_cwe") or {},
            }
    for config in inv.configs:
        baseline = inv.baseline_of(config)
        cwes: dict[str, int] = {}
        for sid in inv.configs[config]:
            for cwe, n in (inv.result(sid, "security").get("by_cwe") or {}).items():
                cwes[cwe] = cwes.get(cwe, 0) + n
        out["agentic"][config] = {
            "baseline": baseline,
            "baseline_density_per_100_loc": inv.result(
                baseline, "security").get("density_per_100_loc"),
            "density_per_100_loc": mr(inv.across(config, lambda s: inv.result(
                s, "security").get("density_per_100_loc")), 2),
            "total_findings": mr(inv.across(config, lambda s: inv.result(
                s, "security").get("total_findings")), 1),
            "runs_with_any_finding": sum(
                1 for s in inv.configs[config]
                if (inv.result(s, "security").get("total_findings") or 0) > 0),
            "findings_by_cwe_across_runs": dict(sorted(cwes.items())),
            "runs_differing_from_baseline_by_severity": {
                sev: sum(1 for s in inv.configs[config]
                         if _pick(inv.result(s, "significance"), "security", sev,
                                  "significant") is True)
                for sev in ("HIGH", "MEDIUM", "LOW")},
        }
    return out


# --------------------------------------------------------------------------- #
# RQ5 -- duplication                                                          #
# --------------------------------------------------------------------------- #

def rq5_duplication(inv: Inventory) -> dict:
    out: dict = {"human": {}, "agentic": {}, "min_tokens": None}
    for sid, subject in inv.subjects.items():
        res = inv.result(sid, "duplication")
        if not res:
            continue
        out["min_tokens"] = res.get("min_tokens")
        if subject.kind == "human":
            out["human"][sid] = {
                "duplicated_pct": res.get("duplicated_pct"),
                "duplicated_loc": res.get("duplicated_loc"),
                "duplicated_blocks": res.get("duplicated_blocks"),
                "max_block_tokens": res.get("max_block_tokens"),
            }
    runs_with_duplication = []
    for config in inv.configs:
        baseline = inv.baseline_of(config)
        with_dup = [s for s in inv.configs[config]
                    if (inv.result(s, "duplication").get("duplicated_pct") or 0) > 0]
        runs_with_duplication.extend(with_dup)
        out["agentic"][config] = {
            "baseline": baseline,
            "baseline_duplicated_pct": inv.result(
                baseline, "duplication").get("duplicated_pct"),
            "duplicated_pct": mr(inv.across(config, lambda s: inv.result(
                s, "duplication").get("duplicated_pct")), 2),
            "duplicated_blocks": mr(inv.across(config, lambda s: inv.result(
                s, "duplication").get("duplicated_blocks")), 1),
            "runs_with_any_duplication": len(with_dup),
            "runs_differing_from_baseline": sum(
                1 for s in inv.configs[config]
                if _pick(inv.result(s, "significance"), "duplication",
                         "duplicated_pct", "significant") is True),
        }
    out["runs_with_any_duplication"] = sorted(runs_with_duplication)
    out["n_runs_with_any_duplication"] = len(runs_with_duplication)
    out["n_agentic_runs"] = sum(len(r) for r in inv.configs.values())
    return out


# --------------------------------------------------------------------------- #
# The maturity reference point (Flask 0.1)                                    #
# --------------------------------------------------------------------------- #

def maturity(inv: Inventory) -> dict:
    if MATURITY_ID not in inv.subjects:
        return {}
    rows = {}
    for sid in (MATURITY_ID, "flask"):
        cx = inv.result(sid, "complexity")
        rows[sid] = {
            "loc": inv.result(sid, "repo_stats").get("loc"),
            "source_files": inv.result(sid, "repo_stats").get("source_files"),
            "mean_cc": _pick(cx, "cc", "mean"),
            "mean_cogc": _pick(cx, "cogc", "mean"),
            "mean_mi": _pick(cx, "mi", "mean"),
            "smells_per_100_loc": inv.result(sid, "smells").get("per_100_loc"),
            "security_per_100_loc": inv.result(
                sid, "security").get("density_per_100_loc"),
            "duplicated_pct": inv.result(sid, "duplication").get("duplicated_pct"),
        }
    better = {}
    lower_is_better = {"mean_cc", "mean_cogc", "smells_per_100_loc",
                       "security_per_100_loc", "duplicated_pct"}
    for metric in ("mean_cc", "mean_cogc", "mean_mi", "smells_per_100_loc",
                   "security_per_100_loc", "duplicated_pct"):
        draft, mature = rows[MATURITY_ID][metric], rows["flask"][metric]
        if draft is None or mature is None:
            better[metric] = None
        elif metric in lower_is_better:
            better[metric] = draft < mature
        else:
            better[metric] = draft > mature
    return {
        "first_draft": MATURITY_ID,
        "mature_release": "flask",
        "values": rows,
        "first_draft_better": better,
        "metrics_where_first_draft_is_better": sum(1 for v in better.values() if v),
        "metrics_compared": len(better),
        "note": ("Radon computes MI per file, so the single-module first draft "
                 "contributes one file-level value and its mean equals its "
                 "median."),
    }


# --------------------------------------------------------------------------- #
# Generation facts (cost, model calls, wall-clock, agent steps)               #
# --------------------------------------------------------------------------- #

def _sweagent_stats(run_id: str) -> dict:
    """Model calls and cost for one SWE-agent run, from its frozen trajectory."""
    trajs = sorted((GENERATION_DIR / run_id).glob("*/*.traj.gz"))
    if not trajs:
        return {}
    with gzip.open(trajs[0]) as fh:
        traj = json.load(fh)
    stats = _pick(traj, "info", "model_stats", default={}) or {}
    return {
        "model_calls": stats.get("api_calls"),
        "cost_usd": _round(stats.get("instance_cost"), 2),
        "tokens_sent": stats.get("tokens_sent"),
        "exit_status": _pick(traj, "info", "exit_status"),
        "trajectory_steps": len(traj.get("trajectory") or []),
    }


STEP_RE = re.compile(rb"STEP (\d+)")
OPENHANDS_TS = re.compile(rb"(\d{2}:\d{2}:\d{2}) - ")


def _openhands_steps(run_id: str) -> dict:
    """Agent steps and wall-clock for one OpenHands run, from its stderr."""
    log = GENERATION_DIR / run_id / "stderr.log"
    if not log.exists():
        return {"trace_captured": False}
    raw = log.read_bytes()
    steps = [int(m.group(1)) for m in STEP_RE.finditer(raw)]
    if not steps:
        return {"trace_captured": False}
    stamps = [m.group(1).decode() for m in OPENHANDS_TS.finditer(raw)]
    # The prompt itself is written to stdout, the event log to stderr.
    stdout = GENERATION_DIR / run_id / "stdout.log"
    prompted = stdout.exists() and b"Request user input" in stdout.read_bytes()
    return {"trace_captured": True,
            "agent_steps": max(steps) + 1,       # OpenHands numbers steps from 0
            "trace_wall_seconds": _span_seconds(stamps, "%H:%M:%S"),
            "asked_for_user_input": prompted}


SWEAGENT_TS = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}")


def _span_seconds(stamps: list[str], fmt: str) -> float | None:
    """Seconds between the first and last timestamp, or None if there are none."""
    if not stamps:
        return None
    first = datetime.strptime(stamps[0], fmt)
    last = datetime.strptime(stamps[-1], fmt)
    return _round((last - first).total_seconds(), 1)


def _sweagent_wall_seconds(run_id: str) -> float | None:
    """Wall-clock for one SWE-agent run, from the timestamps in its own log.

    generation/runs/MANIFEST.json recorded the wall-clock of the last
    configuration generated and not of the earlier ten runs, so it is
    reconstructed here from the run's info log, which brackets the whole run
    from "Starting environment" to "Done". Where the manifest does carry the
    value the two agree to within the two seconds of harness overhead the
    manifest additionally includes, which is what makes the reconstruction
    usable for the runs it omits.
    """
    logs = sorted((GENERATION_DIR / run_id).glob("*/*.info.log.gz"))
    if not logs:
        return None
    stamps = []
    with gzip.open(logs[0], "rt", errors="replace") as fh:
        for line in fh:
            match = SWEAGENT_TS.match(line)
            if match:
                stamps.append(match.group(1))
    return _span_seconds(stamps, "%Y-%m-%d %H:%M:%S")


def generation(inv: Inventory) -> dict:
    manifest = inv.generation
    if not manifest:
        return {}
    by_id = {r["run_id"]: r for r in manifest.get("runs", [])}
    out: dict = {"budget": manifest.get("budget", {}),
                 "generated_utc": manifest.get("generated_utc"),
                 "runs": {}, "per_configuration": {}}
    for config, runs in inv.configs.items():
        meta = inv.config_meta(config)
        rows = {}
        for sid in runs:
            record = by_id.get(sid, {})
            row = {
                "agent": record.get("agent") or meta["agent"],
                "model": record.get("model") or meta["model"],
                "exit_status": record.get("exit_status"),
                # The manifest records the full SHA for the runs it covers;
                # the registry's snapshot string carries the short one for all.
                "commit": (record.get("commit")
                           or inv.subjects[sid].snapshot.rpartition("@ ")[2]
                           or None),
                "files_written": record.get("files_written"),
            }
            row.update(_sweagent_stats(sid) if (row["agent"] == "swe-agent")
                       else _openhands_steps(sid))
            # The manifest's own wall-clock where it has one, the run's log
            # otherwise (see `_sweagent_wall_seconds`).
            traced = (_sweagent_wall_seconds(sid) if row["agent"] == "swe-agent"
                      else row.pop("trace_wall_seconds", None))
            row["wall_seconds"] = record.get("wall_seconds") or traced
            row["wall_seconds_source"] = (
                "generation manifest" if record.get("wall_seconds")
                else ("run log" if traced else None))
            row["wall_seconds_from_run_log"] = traced
            rows[sid] = row
        out["runs"].update(rows)
        values = list(rows.values())
        budget_calls = (manifest.get("budget") or {}).get("tool_calls")
        calls = mr([v.get("model_calls") for v in values], 1)
        out["per_configuration"][config] = {
            "agent": meta["agent"], "model": meta["model"], "spec": meta["spec"],
            "wall_seconds": mr([v.get("wall_seconds") for v in values], 1),
            "wall_minutes": mr([v["wall_seconds"] / 60.0 for v in values
                                if v.get("wall_seconds") is not None], 1),
            "model_calls": calls,
            "model_calls_pct_of_tool_call_budget": (
                _round(100.0 * calls["max"] / budget_calls, 1)
                if calls and budget_calls else None),
            "cost_usd": mr([v.get("cost_usd") for v in values], 2),
            "agent_steps": mr([v.get("agent_steps") for v in values], 1),
            "traces_captured": sum(1 for v in values
                                   if v.get("trace_captured") is not False),
            "runs_pausing_for_user_input": sum(
                1 for v in values if v.get("asked_for_user_input")) or None,
            "exit_statuses": sorted({v["exit_status"] for v in values
                                     if v.get("exit_status")}),
        }
    costs = [v.get("cost_usd") for v in out["runs"].values() if v.get("cost_usd")]
    out["total_cost_usd"] = _round(sum(costs), 2) if costs else None
    return out


# --------------------------------------------------------------------------- #
# The abstract's numeric claims, each with the figure that supports it        #
# --------------------------------------------------------------------------- #

def claims(sections: dict) -> dict:
    repo, rq1 = sections["table_repo_stats"], sections["rq1_correctness"]
    rq2, rq3 = sections["rq2_complexity"], sections["rq3_maintainability"]
    rq4, rq5 = sections["rq4_security"], sections["rq5_duplication"]
    across = repo["size_ratio"]["across_configurations"]

    def median_of(section: str, config: str, key: str):
        return _pick(sections[section], "agentic", config, key, "median")

    out = {
        "median_oracle_pass_rate_pct": {
            config: median_of("rq1_correctness", config, "pass_rate_pct")
            for config in rq1["agentic"]},
        "baseline_oracle_pass_rate_pct": {
            sid: row["pass_rate_pct"] for sid, row in rq1["human"].items()},
        "agentic_repositories_times_smaller": {
            "min": across["times_smaller_min"], "max": across["times_smaller_max"],
            "at_median_min": across["times_smaller_median_min"],
            "at_median_max": across["times_smaller_median_max"]},
        "mean_cc_relative_to_baseline_pct": {
            config: _pick(rq2, "agentic", config, "relative_to_baseline_pct", "mean_cc")
            for config in rq2["agentic"]},
        "mean_cogc_relative_to_baseline_pct": {
            config: _pick(rq2, "agentic", config, "relative_to_baseline_pct", "mean_cogc")
            for config in rq2["agentic"]},
        "mean_mi_gap_points": {
            config: (None if median_of("rq3_maintainability", config, "mean_mi") is None
                     else _round(median_of("rq3_maintainability", config, "mean_mi")
                                 - _pick(rq3, "human",
                                         _pick(rq3, "agentic", config, "baseline"),
                                         "mean_mi"), 1))
            for config in rq3["agentic"]},
        "mean_mi_gap_points_size_matched": {
            config: _pick(rq3, "agentic", config, "size_matched_mi",
                          "median_mi_gap_matched")
            for config in rq3["agentic"]},
        "pylint_density_ratio_to_baseline_at_median": {
            "per_configuration": {
                config: _pick(rq3, "agentic", config,
                              "smells_ratio_to_baseline_at_median")
                for config in rq3["agentic"]},
            "range": rq3["smells_ratio_across_configurations"]},
        "trailing_whitespace_share_pct_at_median": {
            config: median_of("rq3_maintainability", config,
                              "trailing_whitespace_share_pct")
            for config in rq3["agentic"]},
        "security_density_per_100_loc_median": {
            config: median_of("rq4_security", config, "density_per_100_loc")
            for config in rq4["agentic"]},
        "security_density_ratio_to_baseline_at_median": {
            config: ratio(median_of("rq4_security", config, "density_per_100_loc"),
                          _pick(rq4, "agentic", config,
                                "baseline_density_per_100_loc"), 1)
            for config in rq4["agentic"]},
        "duplicated_pct_median": {
            config: median_of("rq5_duplication", config, "duplicated_pct")
            for config in rq5["agentic"]},
        "runs_with_any_duplication": {
            "n": rq5["n_runs_with_any_duplication"],
            "of": rq5["n_agentic_runs"], "runs": rq5["runs_with_any_duplication"]},
    }
    if rq4.get("jinja2_autoescaping"):
        out["flask_spec_runs_with_autoescaping_off"] = {
            "n": rq4["jinja2_autoescaping"]["runs_with_autoescaping_off"],
            "of": rq4["jinja2_autoescaping"]["runs_examined"]}
    gen = sections.get("generation") or {}
    if gen:
        swe = [v for v in gen["per_configuration"].values()
               if v["agent"] == "swe-agent"]
        oh = [v for v in gen["per_configuration"].values()
              if v["agent"] == "openhands"]
        out["generation"] = {
            "swe_agent_wall_minutes_by_spec": {
                v["spec"]: {"min": v["wall_minutes"]["min"],
                            "max": v["wall_minutes"]["max"]}
                for v in swe if v["wall_minutes"]},
            "swe_agent_model_calls": {
                "min": min((v["model_calls"]["min"] for v in swe if v["model_calls"]),
                           default=None),
                "max": max((v["model_calls"]["max"] for v in swe if v["model_calls"]),
                           default=None)},
            "swe_agent_cost_usd": {
                "min": min((v["cost_usd"]["min"] for v in swe if v["cost_usd"]),
                           default=None),
                "max": max((v["cost_usd"]["max"] for v in swe if v["cost_usd"]),
                           default=None)},
            "openhands_wall_seconds": {
                "min": min((v["wall_seconds"]["min"] for v in oh if v["wall_seconds"]),
                           default=None),
                "max": max((v["wall_seconds"]["max"] for v in oh if v["wall_seconds"]),
                           default=None)},
            "openhands_agent_steps": {
                "min": min((v["agent_steps"]["min"] for v in oh if v["agent_steps"]),
                           default=None),
                "max": max((v["agent_steps"]["max"] for v in oh if v["agent_steps"]),
                           default=None)},
        }
    return out


# --------------------------------------------------------------------------- #
# Assembly                                                                    #
# --------------------------------------------------------------------------- #

def _harness_commit() -> str | None:
    """The harness commit, if it can be known.

    The hermetic image does not carry .git (see .dockerignore), so the value is
    null on the path that produces the committed artifact unless the caller
    passes HARNESS_COMMIT; logs/environment.txt records the commit for that
    run either way. The field is excluded from ``--check`` for the same reason.
    """
    declared = os.environ.get("HARNESS_COMMIT", "").strip()
    if declared:
        return declared
    try:
        out = subprocess.run(["git", "-C", str(common.REPO_ROOT), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def _toolchain() -> dict:
    versions = {}
    path = common.REPO_ROOT / "requirements-analysis.txt"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "==" in line:
                name, _, version = line.partition("==")
                versions[name.strip()] = version.strip()
    return versions


def compute(*, with_commit: bool = True) -> dict:
    inv = Inventory()
    missing = {sid: [d for d in Inventory.DIMENSIONS
                     if not inv.results[sid][d] and not (
                         d == "correctness" and not inv.subjects[sid].oracle)]
               for sid in inv.subjects}
    missing = {sid: dims for sid, dims in missing.items() if dims}

    sections = {
        "table_repo_stats": table_repo_stats(inv),
        "rq1_correctness": rq1_correctness(inv),
        "rq2_complexity": rq2_complexity(inv),
        "rq3_maintainability": rq3_maintainability(inv),
        "rq4_security": rq4_security(inv),
        "rq5_duplication": rq5_duplication(inv),
        "maturity_reference_point": maturity(inv),
        "generation": generation(inv),
    }
    sections["claims"] = claims(sections)
    # Deliberately no timestamp: results/ must stay byte-identical between two
    # runs of the pinned image (see README, "Determinism"), and the run's date
    # is recorded in logs/environment.txt instead.
    meta = {
        "toolchain": _toolchain(),
        "subjects_measured": sorted(inv.subjects),
        "configurations": {c: inv.config_meta(c) for c in sorted(inv.configs)},
        "incomplete_subjects": missing,
    }
    if with_commit:
        meta["harness_commit"] = _harness_commit()
    return {"_meta": meta, **sections}


def _strip_volatile(payload: dict) -> dict:
    """The payload without the fields that legitimately change between runs."""
    copy = json.loads(json.dumps(payload))
    copy.get("_meta", {}).pop("harness_commit", None)
    return copy


def _print_summary(payload: dict) -> None:
    claim = payload["claims"]
    print("oracle pass rate (median %):")
    for config, value in claim["median_oracle_pass_rate_pct"].items():
        print(f"  {config:<20} {value}")
    for sid, value in claim["baseline_oracle_pass_rate_pct"].items():
        print(f"  {sid:<20} {value}  (baseline)")
    print("\npylint density vs. baseline at the median run:")
    for config, value in claim[
            "pylint_density_ratio_to_baseline_at_median"]["per_configuration"].items():
        print(f"  {config:<20} {value}x")
    rng = claim["pylint_density_ratio_to_baseline_at_median"]["range"]
    print(f"  range                {rng['min']}x to {rng['max']}x")
    print("\nrepositories smaller than their baseline: "
          f"{claim['agentic_repositories_times_smaller']['min']}x to "
          f"{claim['agentic_repositories_times_smaller']['max']}x")
    dup = claim["runs_with_any_duplication"]
    print(f"runs with any duplication: {dup['n']} of {dup['of']} {dup['runs']}")
    if "flask_spec_runs_with_autoescaping_off" in claim:
        off = claim["flask_spec_runs_with_autoescaping_off"]
        print(f"Flask-spec runs with Jinja2 autoescaping off: {off['n']} of {off['of']}")


def run(check: bool = False, show: bool = False) -> int:
    payload = compute()
    if show:
        _print_summary(payload)
        return 0
    if check:
        if not OUT_PATH.exists():
            print(f"[paper_numbers] {OUT_PATH.relative_to(common.REPO_ROOT)} "
                  f"is missing; run `make paper-numbers`", file=sys.stderr)
            return 1
        committed = json.loads(OUT_PATH.read_text())
        if _strip_volatile(committed) != _strip_volatile(payload):
            print("[paper_numbers] the committed numbers do not match what the "
                  "current results/ produce; run `make paper-numbers`",
                  file=sys.stderr)
            return 1
        print(f"[paper_numbers] {OUT_PATH.relative_to(common.REPO_ROOT)} matches "
              f"results/ ({len(payload['_meta']['subjects_measured'])} subjects)")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    print(f"[paper_numbers] wrote {OUT_PATH.relative_to(common.REPO_ROOT)} "
          f"({len(payload['_meta']['subjects_measured'])} subjects, "
          f"{len(payload['_meta']['configurations'])} configurations) at {stamp}")
    if payload["_meta"]["incomplete_subjects"]:
        for sid, dims in payload["_meta"]["incomplete_subjects"].items():
            print(f"[paper_numbers] WARNING {sid}: no result for "
                  f"{', '.join(dims)}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify the committed JSON instead of rewriting it")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print a human-readable summary and exit")
    args = ap.parse_args()
    return run(check=args.check, show=args.show)


if __name__ == "__main__":
    raise SystemExit(main())
