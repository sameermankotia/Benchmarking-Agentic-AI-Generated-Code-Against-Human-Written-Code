#!/usr/bin/env python3
"""Drive every analysis stage in order, aggregate the paper tables, and
compute the paper's figure set.

Usage:
    python run_all.py                         # all subjects, all stages
    python run_all.py --subjects flask swe_flask
    python run_all.py --stages repo_stats complexity aggregate
    python run_all.py --stages paper_numbers       # just the paper's figure set

Stages run in dependency order: repo_stats first (its LOC feeds the density
metrics), then the five dimensions, then significance (Mann-Whitney U /
Fisher's exact against each pair's human baseline, requiring the five
dimensions' per-subject JSON to already exist), then aggregate, then
paper_numbers (the medians, ranges and ratios the paper quotes, read back from
the aggregated per-subject JSON). Missing
snapshots or uninstalled external tools are reported and skipped, not fatal —
the pipeline always produces whatever tables the available data supports.
"""

from __future__ import annotations

import argparse
import sys
import time

from analysis import (aggregate, complexity, correctness, duplication,
                      paper_numbers, repo_stats, security, significance,
                      smells)

STAGES = {
    "repo_stats": repo_stats.run,
    "correctness": correctness.run,
    "complexity": complexity.run,
    "smells": smells.run,
    "security": security.run,
    "duplication": duplication.run,
    "significance": significance.run,
}
ORDER = ["repo_stats", "correctness", "complexity", "smells",
         "security", "duplication", "significance"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subjects", nargs="*", default=None,
                    help="subject ids to analyze (default: all)")
    ap.add_argument("--stages", nargs="*", default=None,
                    help="stages to run (default: all + aggregate + paper_numbers)")
    args = ap.parse_args()

    stages = args.stages or (ORDER + ["aggregate", "paper_numbers"])
    for stage in stages:
        if stage == "aggregate":
            print("\n=== aggregate ===")
            aggregate.run()
            continue
        if stage == "paper_numbers":
            print("\n=== paper_numbers ===")
            paper_numbers.run()
            continue
        if stage not in STAGES:
            print(f"unknown stage: {stage}", file=sys.stderr)
            return 2
        print(f"\n=== {stage} ===")
        t0 = time.monotonic()
        try:
            STAGES[stage](args.subjects)
        except Exception as e:  # a broken stage must not sink the whole run
            print(f"[{stage}] ERROR: {e}", file=sys.stderr)
        else:
            print(f"[{stage}] done in {time.monotonic() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
