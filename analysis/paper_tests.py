"""The per-run significance tests exactly as the paper reports them.

``analysis/significance.py`` writes one JSON file per agentic run with the
tests it has always run (Mann-Whitney U on CC, CogC, MI and per-file
duplication; Fisher's exact on oracle pass/fail and Bandit severity bands).
The paper reports a different, larger set, summarised as "k/5 higher" or
"k/5 lower" per configuration. This module computes that set from the
committed per-subject results and writes ``results/paper_tests.json``.

Tests (two-sided, alpha = 0.05, each agentic run against the human baseline of
its own pair; paper Section III-D6):

* Mann-Whitney U on per-block CC, per-function CogC and per-file MI, with the
  paper's effect size ``r = 2*U_A / (n_A * n_H) - 1`` (``r > 0``: agentic values
  tend to be larger). Note that ``significance.py`` reports the opposite sign
  (``rank_biserial = 1 - 2U/(n n)``).
* Fisher's exact test on the share of blocks with CC > 10, of functions with
  CogC > 15, of files with MI < 65 (Radon's 0-100 scale), and on oracle
  pass/fail totals (descriptive: oracle cases are not independent).
* The exact conditional binomial test of equal Poisson rates, with LOC as the
  exposure, for pylint messages (all, and non-cosmetic), Bandit findings and
  CPD blocks.
* The size-matched MI comparison: agentic files pooled over the five runs
  against the human files no larger (in LOC) than the largest agentic file,
  Mann-Whitney U, descriptive because files of different runs are pooled.

Cosmetic pylint messages are the layout and naming symbols in ``COSMETIC``.

    python -m analysis.paper_tests            # write results/paper_tests.json
    python -m analysis.paper_tests --check    # verify the committed file
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys

from . import common
from . import paper_numbers as pn

OUT_PATH = common.RESULTS_DIR / "paper_tests.json"
ALPHA = 0.05

#: pylint symbols that concern layout and naming only and that a formatter or
#: a rename fixes (paper Section III-D3).
COSMETIC = frozenset({
    "trailing-whitespace", "line-too-long", "missing-final-newline",
    "trailing-newlines", "mixed-line-endings", "superfluous-parens",
    "bad-indentation", "wrong-import-order", "ungrouped-imports",
    "wrong-import-position", "multiple-imports", "multiple-statements",
    "invalid-name",
})


def _stats():
    try:
        from scipy import stats
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("scipy is required (requirements-analysis.txt)") from exc
    return stats


def _loc(inv, sid):
    return inv.result(sid, "repo_stats")["loc"]


def _records(inv, sid, key):
    return [r[key] for r in inv.result(sid, "complexity")[key]["records"]]


def _mi(inv, sid):
    return [f["mi"] for f in inv.result(sid, "complexity")["mi"]["files"]
            if f["mi"] is not None]


def _pylint(inv, sid):
    res = inv.result(sid, "smells")
    total = res["total_findings"]
    symbols = res.get("symbols") or res.get("top_symbols") or {}
    cosmetic = sum(v for k, v in symbols.items() if k in COSMETIC)
    return total, cosmetic


def _rate_p(xa, na, xh, nh):
    """Exact conditional binomial test of equal Poisson rates."""
    n = xa + xh
    if n == 0:
        return 1.0
    return float(_stats().binomtest(xa, n, na / (na + nh)).pvalue)


def _summary(directions, pvalues):
    """'k/5 higher', 'k/5 lower', or 'k/5' when nothing rejects."""
    sig = [d for d, p in zip(directions, pvalues) if p < ALPHA]
    k = f"{len(sig)}/{len(pvalues)}"
    if not sig:
        return k
    if all(d > 0 for d in sig):
        return f"{k} higher"
    if all(d < 0 for d in sig):
        return f"{k} lower"
    return f"{k} mixed"


def _per_run(runs, fn):
    rows = [fn(s) for s in runs]
    return {
        "summary": _summary([r["direction"] for r in rows],
                            [r["p"] for r in rows]),
        "runs": dict(zip(runs, rows)),
    }


def compute(inv) -> dict:
    stats = _stats()
    out: dict = {"_meta": {"alpha": ALPHA, "cosmetic_symbols": sorted(COSMETIC)},
                 "baselines": {}, "configurations": {}}

    for base in sorted({inv.baseline_of(c) for c in inv.configs}):
        total, cosm = _pylint(inv, base)
        out["baselines"][base] = {
            "pylint_per_100_loc": round(100 * total / _loc(inv, base), 2),
            "non_cosmetic_per_100_loc": round(100 * (total - cosm) / _loc(inv, base), 2),
            "cosmetic_share_pct": round(100 * cosm / total, 1) if total else None,
        }

    if "flask_0_1" in inv.subjects:   # maturity reference point (Table XI)
        total, cosm = _pylint(inv, "flask_0_1")
        out["baselines"]["flask_0_1"] = {
            "pylint_per_100_loc": round(100 * total / _loc(inv, "flask_0_1"), 2),
            "non_cosmetic_per_100_loc": round(
                100 * (total - cosm) / _loc(inv, "flask_0_1"), 2),
            "cosmetic_share_pct": round(100 * cosm / total, 1) if total else None,
        }

    for cfg in sorted(inv.configs):
        runs = inv.configs[cfg]
        b = inv.baseline_of(cfg)
        res: dict = {"baseline": b}

        def mw(get):
            def one(s):
                a, h = get(s), get(b)
                t = stats.mannwhitneyu(a, h, alternative="two-sided")
                r = 2 * t.statistic / (len(a) * len(h)) - 1
                return {"p": float(t.pvalue), "r": round(float(r), 3),
                        "direction": r}
            d = _per_run(runs, one)
            d["median_r"] = round(statistics.median(
                v["r"] for v in d["runs"].values()), 2)
            return d

        res["cc_mannwhitney"] = mw(lambda s: _records(inv, s, "cc"))
        res["cogc_mannwhitney"] = mw(lambda s: _records(inv, s, "cogc"))
        res["mi_mannwhitney"] = mw(lambda s: _mi(inv, s))

        def share(get, pred):
            def one(s):
                a, h = get(s), get(b)
                xa, xh = sum(map(pred, a)), sum(map(pred, h))
                p = stats.fisher_exact([[xa, len(a) - xa], [xh, len(h) - xh]])[1]
                return {"p": float(p), "agentic": [xa, len(a)],
                        "human": [xh, len(h)],
                        "direction": xa / len(a) - xh / len(h)}
            return _per_run(runs, one)

        res["cc_over_10_fisher"] = share(lambda s: _records(inv, s, "cc"),
                                         lambda v: v > 10)
        res["cogc_over_15_fisher"] = share(lambda s: _records(inv, s, "cogc"),
                                           lambda v: v > 15)
        res["mi_below_65_fisher"] = share(lambda s: _mi(inv, s),
                                          lambda v: v < 65)

        def oracle(s):
            a, h = inv.result(s, "correctness"), inv.result(b, "correctness")
            p = stats.fisher_exact([[a["passed"], a["total"] - a["passed"]],
                                    [h["passed"], h["total"] - h["passed"]]])[1]
            return {"p": float(p), "direction": a["passed"] / a["total"]
                    - h["passed"] / h["total"]}
        res["oracle_total_fisher"] = _per_run(runs, oracle)

        def rate(count):
            def one(s):
                xa, xh, na, nh = count(s), count(b), _loc(inv, s), _loc(inv, b)
                return {"p": _rate_p(xa, na, xh, nh), "counts": [xa, xh],
                        "loc": [na, nh], "direction": xa / na - xh / nh}
            return _per_run(runs, one)

        res["pylint_all_rate"] = rate(lambda s: _pylint(inv, s)[0])
        res["pylint_non_cosmetic_rate"] = rate(
            lambda s: _pylint(inv, s)[0] - _pylint(inv, s)[1])
        res["bandit_rate"] = rate(
            lambda s: inv.result(s, "security")["total_findings"])
        res["cpd_block_rate"] = rate(
            lambda s: inv.result(s, "duplication")["duplicated_blocks"])

        per100 = [100 * (_pylint(inv, s)[0] - _pylint(inv, s)[1]) / _loc(inv, s)
                  for s in runs]
        tot = sum(_pylint(inv, s)[0] for s in runs)
        cos = sum(_pylint(inv, s)[1] for s in runs)
        res["non_cosmetic_per_100_loc"] = {
            "median": round(statistics.median(per100), 2),
            "min": round(min(per100), 2), "max": round(max(per100), 2)}
        res["cosmetic_share_pooled_pct"] = round(100 * cos / tot, 1) if tot else None

        agentic = [p for s in runs for p in pn._mi_with_loc(inv, s)]
        cap = max(loc for loc, _ in agentic)
        human = [mi for loc, mi in pn._mi_with_loc(inv, b) if loc <= cap]
        am = [mi for _, mi in agentic]
        res["size_matched_mi"] = {
            "file_size_cap_loc": cap,
            "human_median_mi": round(statistics.median(human), 1),
            "agentic_median_mi": round(statistics.median(am), 1),
            "human_files": len(human), "agentic_files": len(am),
            "p_descriptive": round(float(stats.mannwhitneyu(
                am, human, alternative="two-sided").pvalue), 2),
        }
        out["configurations"][cfg] = res

    # drop the internal sort key from the stored rows
    for cfg in out["configurations"].values():
        for test in cfg.values():
            if isinstance(test, dict) and "runs" in test:
                for row in test["runs"].values():
                    row.pop("direction", None)
                    row["p"] = round(row["p"], 4)
    return out


def run(_subjects=None) -> None:
    payload = compute(pn.Inventory())
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"[paper_tests] wrote {OUT_PATH.relative_to(common.REPO_ROOT)}")
    for cfg, res in payload["configurations"].items():
        print(f"  {cfg:18} CC {res['cc_mannwhitney']['summary']:10} "
              f"pylint {res['pylint_all_rate']['summary']:11} "
              f"non-cosmetic {res['pylint_non_cosmetic_rate']['summary']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="recompute and compare with the committed file")
    args = ap.parse_args()
    if not args.check:
        run()
        return 0
    fresh = json.loads(json.dumps(compute(pn.Inventory()), sort_keys=True))
    committed = json.loads(OUT_PATH.read_text())
    if fresh != committed:
        print("[paper_tests] MISMATCH with the committed results/paper_tests.json")
        return 1
    print("[paper_tests] committed file matches results/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
