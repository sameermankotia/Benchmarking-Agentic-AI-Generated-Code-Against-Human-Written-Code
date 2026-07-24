# Agentic vs. Human Benchmark — Replication Package

Analysis harness for *Benchmarking Agentic AI-Generated Code Against
Human-Written Code: A Multi-Dimensional Study on GitHub Repositories.*

It runs one deterministic pipeline over every study subject and produces the
paper's tables as CSV. Five quality dimensions, five research questions:

| RQ  | Dimension               | Tool(s)                         | Module                     |
|-----|-------------------------|---------------------------------|----------------------------|
| RQ1 | Functional correctness  | pytest (oracle suites)          | `analysis/correctness.py`  |
| RQ2 | Complexity (CC + CogC)  | Radon + complexipy              | `analysis/complexity.py`   |
| RQ3 | Maintainability         | Radon (MI) + pylint             | `analysis/complexity.py`, `analysis/smells.py` |
| RQ4 | Security density        | Bandit (+ CWE mapping)          | `analysis/security.py`     |
| RQ5 | Code duplication        | CPD (PMD)                       | `analysis/duplication.py`  |

Every dimension above is also tested for statistical significance against
the matched human baseline in the same pair — Mann-Whitney U for the
per-function/per-file distributions (RQ2, RQ3, RQ5) and Fisher's exact for
the pass/fail and severity counts (RQ1, RQ4) — by `analysis/significance.py`
(see "Statistical testing" below).

## Layout

```
subjects/subjects.json   subject registry (paths, kind, oracle, availability)
subjects/<id>/           frozen snapshots (git submodules / mounted read-only)
oracle/flask, oracle/django   specification-derived oracle suites + conftest
analysis/                one module per stage + common helpers + aggregator
run_all.py               orchestrator (`make all` calls this)
results/<dimension>/     per-subject result JSON (includes results/significance/)
results/tables/          aggregated CSV tables (the paper tables)
Dockerfile, Makefile     hermetic execution (paper §3.6)
```

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt      # CPD/PMD via Docker only
make all                                       # all subjects, all stages
make all SUBJECTS="flask swe_flask"            # subset
make complexity                                # one stage
make significance                              # Mann-Whitney U / Fisher's exact
make tables                                    # re-aggregate existing JSON
```

Fully reproducible run (installs PMD/CPD + a JRE):

```bash
make docker && make docker-run   # mounts subjects/ ro, results/ rw
```

## What is wired in this checkout

The two **human baselines** are cloned at their pinned tags and marked
`available` in the registry, and both oracle suites are complete, so the
pipeline runs end-to-end today:

```bash
pip install -r requirements-analysis.txt
pip install -e subjects/flask -e subjects/django   # brings in transitive deps
make all SUBJECTS="flask django"
```

Sanity check: each oracle passes **100%** against its own reference baseline
(Flask 133/133, Django 97/97) — a correct oracle must not fail on the
implementation it was specified against. Structural metrics, security, and
smells populate `results/tables/`. Duplication requires PMD/CPD (Java) and is
therefore produced only in the Docker path.

The four **agentic subjects** are registered but `available: false`: they are the
output of specific SWE-agent / OpenHands generation runs (§3.2.3–3.2.6) and
cannot be reproduced from this repo. Drop a generated snapshot under
`subjects/<id>/`, flip `available` to `true`, and it joins every table.

## Adding subjects

Drop the frozen source under `subjects/<id>/`, add an entry to
`subjects/subjects.json` with its source `path`, `kind` (`human`/`agentic`),
`pair`, `oracle`, and set `available: true`. Use `include` to restrict a subject
to sub-packages (Django uses `["urls", "views"]`). Missing or unavailable
subjects are skipped with a note — the pipeline always emits whatever tables the
present data supports.

## How each metric is computed

- **Complexity** — Radon's API gives per-function cyclomatic complexity and
  per-file Maintainability Index (`multi=True`, comment-aware); complexipy gives
  per-function cognitive complexity. Thresholds match the paper: CC > 10,
  CogC > 15, MI < 65.
- **Security** — Bandit's full default plugin set, filtered to Medium-confidence
  or higher, normalised per 100 LOC (same convention as the pylint density
  below), with test-ids mapped to CWE classes (§3.5.4). Findings also carry
  their raw Bandit test-id, so `analysis/aggregate.py` can render the
  Bandit-ID -> CWE breakdown (`table_cwe_<pair>.csv`, paper Table 6)
  independently of the collapsed per-CWE counts in `table_security.csv`.
- **Smells** — pylint JSON reporter; F/I categories dropped (§3.5.3); reported
  as totals, per-100-LOC density, and C/R/W/E breakdown.
- **Duplication** — CPD with a 50-token minimum; duplicated blocks, duplicated
  LOC, duplicated fraction, largest block in tokens, and a per-file duplicated
  LOC / duplicated-% breakdown (feeds the file-level significance test below).
- **Correctness** — each oracle suite runs against a subject through the
  canonical `sut` import (see `oracle/conftest.py`); JUnit XML is bucketed into
  the paper's behavioural categories by test-file stem.

### Statistical testing

`analysis/significance.py` runs after the five dimension stages and tests
each **agentic** subject against the **human baseline in its own pair**
(SWE-agent/OpenHands-Flask vs. Flask; SWE-agent-Django vs. the Django
module):

- **Mann-Whitney U** (two-sided) on the per-function CC and CogC
  distributions (RQ2) and the per-file MI and duplicated-LOC-%
  distributions (RQ3, RQ5) — complexity and duplication are right-skewed, so
  a rank-based test is more appropriate than a *t*-test. Effect size is
  reported as rank-biserial correlation (Kerby 2014's simple-difference
  formula, `r = 1 - 2U/(n_agentic * n_human)`); `r > 0` means the agentic
  distribution skews higher (worse, for CC/CogC/duplication) or lower
  (worse, for MI) than the human baseline.
- **Fisher's exact test** (two-sided) on the oracle pass/fail 2x2 tables, per
  behavioural category and overall (RQ1), and on the Bandit severity-band 2x2
  tables (RQ4), since several cells have small counts and a chi-square
  approximation would be unreliable there.

All tests use alpha = 0.05. Results are written to
`results/significance/<agentic_id>.json` and folded back into Tables 3
(complexity), 4 (maintainability/MI), 5 (security), and 7 (duplication) as
added p-value / effect-size rows, and into Table 2 (correctness) as added
per-category p-value columns, by `analysis/aggregate.py`. A cell reads
`ref.` for the human baseline itself (nothing to test it against) and `-`
where the upstream dimension data wasn't available.

Run it standalone with `make significance` once `make complexity`,
`make correctness`, `make security`, and `make duplication` have produced
their JSON for both a pair's human baseline and at least one agentic
subject in that pair.

### Cross-repository consistency

`analysis/aggregate.py` also renders one `table_quality_gap_<agentic_id>.csv`
per agentic subject (paper Tables 8-9): oracle pass rate, mean CC, mean
CogC, mean MI, security findings/100 LOC, and duplicated LOC%, each as
human-baseline value, agentic value, and a delta (percentage points for the
pass rate, MI points for MI, relative % otherwise) — the same format used to
argue that quality gaps are consistent in direction and magnitude across
both repository pairs and both agentic systems.

Determinism: identical inputs + pinned tools (`requirements-analysis.txt`,
pinned PMD in the Dockerfile) yield numerically identical `results/`.
