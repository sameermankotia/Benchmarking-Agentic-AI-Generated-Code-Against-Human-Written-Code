"""Statistical significance testing (paper "Statistical Testing").

Complexity scores are right-skewed, so a rank-based test is more appropriate
than a t-test: we run a two-sided Mann-Whitney U test on the per-function
cyclomatic complexity (CC) and cognitive complexity (CogC) distributions,
comparing each agentic subject's function-level scores against the matched
human baseline's function-level scores in the same pair. For Maintainability
Index and duplication percentage, which are measured per file, we apply the
same Mann-Whitney U test at the file level.

For the oracle pass/fail counts (per behavioural category and overall) and
the Bandit severity counts, several cells have small counts, so we use
Fisher's exact test rather than a chi-square test.

Effect sizes are reported alongside p-values as rank-biserial correlation for
the Mann-Whitney tests, using Kerby's (2014) simple-difference formula:

    r = 1 - 2 * U / (n_agentic * n_human)

where U is the Mann-Whitney U statistic associated with the *agentic* sample
(the first argument passed to the test). r > 0 means the agentic sample is
stochastically larger than the human baseline (e.g. higher complexity); r < 0
means the reverse. r is bounded in [-1, 1].

All tests are two-sided with alpha = 0.05.

Every comparison is pairwise: one agentic subject against the human baseline
in its own ``pair`` (paper §III-B). A subject with no present human baseline
in its pair, or with no upstream result JSON for a given dimension, is
skipped for that dimension only; every other dimension for that subject still
gets tested.
"""

from __future__ import annotations

import argparse
import math

from . import common

ALPHA = 0.05
SEVERITIES = ("HIGH", "MEDIUM", "LOW")


def _require_scipy():
    try:
        import scipy.stats  # noqa: F401
        return scipy.stats
    except ImportError as e:
        raise RuntimeError(
            "scipy is required for significance testing "
            "(pip install -r requirements-analysis.txt)") from e


def _clean(x: float) -> float | None:
    """JSON has no representation for inf/nan; Fisher's odds ratio can hit both."""
    if x is None or math.isnan(x) or math.isinf(x):
        return None
    return x


def mannwhitney(agentic: list[float], human: list[float]) -> dict:
    """Two-sided Mann-Whitney U test + rank-biserial effect size.

    ``agentic`` is always the first sample so ``rank_biserial`` has a
    consistent sign: positive means the agentic distribution skews higher.
    """
    n1, n2 = len(agentic), len(human)
    if n1 < 1 or n2 < 1:
        return {"test": "mannwhitney", "n_agentic": n1, "n_human": n2,
                "u": None, "p": None, "rank_biserial": None, "significant": None}
    scipy_stats = _require_scipy()
    result = scipy_stats.mannwhitneyu(agentic, human, alternative="two-sided")
    u, p = float(result.statistic), float(result.pvalue)
    r = 1.0 - (2.0 * u) / (n1 * n2)
    return {
        "test": "mannwhitney",
        "n_agentic": n1,
        "n_human": n2,
        "u": round(u, 2),
        "p": _clean(p),
        "rank_biserial": round(r, 3),
        "significant": bool(p < ALPHA) if not math.isnan(p) else None,
    }


def fisher(agentic_success: int, agentic_failure: int,
           human_success: int, human_failure: int) -> dict:
    """Two-sided Fisher's exact test on a 2x2 (agentic vs. human) table."""
    scipy_stats = _require_scipy()
    table = [[agentic_success, agentic_failure], [human_success, human_failure]]
    odds_ratio, p = scipy_stats.fisher_exact(table, alternative="two-sided")
    return {
        "test": "fisher_exact",
        "table": table,
        "odds_ratio": _clean(round(float(odds_ratio), 3) if not math.isinf(odds_ratio) else float(odds_ratio)),
        "p": _clean(float(p)),
        "significant": bool(p < ALPHA),
    }


# --------------------------------------------------------------------------- #
# Per-dimension comparisons                                                   #
# --------------------------------------------------------------------------- #

def compare_complexity(agentic_cx: dict, human_cx: dict) -> dict:
    a_cc = [r["cc"] for r in agentic_cx["cc"]["records"]]
    h_cc = [r["cc"] for r in human_cx["cc"]["records"]]
    a_cogc = [r["cogc"] for r in agentic_cx["cogc"]["records"]]
    h_cogc = [r["cogc"] for r in human_cx["cogc"]["records"]]
    return {
        "cc": mannwhitney(a_cc, h_cc),
        "cogc": mannwhitney(a_cogc, h_cogc),
    }


def compare_maintainability(agentic_cx: dict, human_cx: dict) -> dict:
    a_mi = [f["mi"] for f in agentic_cx["mi"]["files"]]
    h_mi = [f["mi"] for f in human_cx["mi"]["files"]]
    return {"mi": mannwhitney(a_mi, h_mi)}


def compare_duplication(agentic_dup: dict, human_dup: dict) -> dict:
    a_pct = [f["duplicated_pct"] for f in agentic_dup.get("files", []) if f["loc"] > 0]
    h_pct = [f["duplicated_pct"] for f in human_dup.get("files", []) if f["loc"] > 0]
    return {"duplicated_pct": mannwhitney(a_pct, h_pct)}


def compare_correctness(agentic_corr: dict, human_corr: dict) -> dict:
    out: dict[str, dict] = {}
    a_cats, h_cats = agentic_corr["categories"], human_corr["categories"]
    for cat in sorted(set(a_cats) & set(h_cats)):
        a, h = a_cats[cat], h_cats[cat]
        out[cat] = fisher(a["passed"], a["n"] - a["passed"],
                           h["passed"], h["n"] - h["passed"])
    out["Total"] = fisher(agentic_corr["passed"], agentic_corr["total"] - agentic_corr["passed"],
                           human_corr["passed"], human_corr["total"] - human_corr["passed"])
    return out


def compare_security(agentic_sec: dict, human_sec: dict) -> dict:
    out: dict[str, dict] = {}
    a_total, h_total = agentic_sec["total_findings"], human_sec["total_findings"]
    for sev in SEVERITIES:
        a_n = agentic_sec["by_severity"].get(sev, 0)
        h_n = human_sec["by_severity"].get(sev, 0)
        out[sev] = fisher(a_n, a_total - a_n, h_n, h_total - h_n)
    return out


def compare_pair(agentic: common.Subject, human: common.Subject) -> dict:
    payload: dict = {
        "agentic": agentic.id,
        "agentic_label": agentic.label,
        "human": human.id,
        "human_label": human.label,
        "pair": agentic.pair,
        "alpha": ALPHA,
    }

    cx_a, cx_h = common.read_result("complexity", agentic.id), common.read_result("complexity", human.id)
    if cx_a and cx_h:
        payload["complexity"] = compare_complexity(cx_a, cx_h)
        payload["maintainability"] = compare_maintainability(cx_a, cx_h)

    dup_a, dup_h = common.read_result("duplication", agentic.id), common.read_result("duplication", human.id)
    if dup_a and dup_h:
        payload["duplication"] = compare_duplication(dup_a, dup_h)

    corr_a, corr_h = common.read_result("correctness", agentic.id), common.read_result("correctness", human.id)
    if corr_a and corr_h:
        payload["correctness"] = compare_correctness(corr_a, corr_h)

    sec_a, sec_h = common.read_result("security", agentic.id), common.read_result("security", human.id)
    if sec_a and sec_h:
        payload["security"] = compare_security(sec_a, sec_h)

    if len(payload) <= 6:  # only the metadata keys were ever added
        raise RuntimeError(
            f"no upstream results for {agentic.id} and/or {human.id}; "
            "run the dimension stages first")
    return payload


def run(subject_ids: list[str] | None = None) -> None:
    all_subjects = common.load_subjects()
    by_pair: dict[str, list[common.Subject]] = {}
    for s in all_subjects:
        by_pair.setdefault(s.pair, []).append(s)

    wanted = set(subject_ids) if subject_ids else None
    ran_any = False
    for pair, members in by_pair.items():
        humans = [s for s in members if s.kind == "human" and s.is_present()]
        if not humans:
            print(f"[significance] SKIP pair '{pair}': no present human baseline")
            continue
        human = humans[0]
        for agentic in members:
            if agentic.kind != "agentic" or not agentic.is_present():
                continue
            if wanted and agentic.id not in wanted:
                continue
            try:
                payload = compare_pair(agentic, human)
            except RuntimeError as e:
                print(f"[significance] SKIP {agentic.id}: {e}")
                continue
            common.write_result("significance", agentic.id, payload)
            ran_any = True
            cc = payload.get("complexity", {}).get("cc", {})
            mi = payload.get("maintainability", {}).get("mi", {})
            print(f"[significance] {agentic.id} vs {human.id}: "
                  f"CC p={cc.get('p')} r={cc.get('rank_biserial')}  "
                  f"MI p={mi.get('p')} r={mi.get('rank_biserial')}")
    if not ran_any:
        print("[significance] SKIP: no agentic/human pair had results for any dimension")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
