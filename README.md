# Agentic vs. Human Benchmark — Replication Package

Analysis harness for *Structural Quality and Security in Agentic Software
Engineering: A Multi-Dimensional Empirical Evaluation.*

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
subjects/subjects.json        subject registry (paths, kind, oracle, availability)
subjects/<id>/                frozen snapshots (cloned locally; git-ignored)
snapshots/MANIFEST.txt        upstream tags + commit SHAs for every snapshot
oracle/flask, oracle/django   specification-derived oracle suites + conftest
analysis/                     one module per stage + significance + aggregator
run_all.py                    orchestrator (`make all` calls this)
results/<dimension>/          per-subject result JSON        (committed)
results/significance/         Mann-Whitney U / Fisher's exact per agentic subject
results/tables/               aggregated CSV tables          (committed)
logs/                         frozen pipeline run transcripts (committed)
Dockerfile, Makefile          hermetic execution
LICENSE, CITATION.cff         MIT license; how to cite
```

`results/` and `logs/` are committed frozen: the package ships the raw numbers
the paper reports, not just the code that produces them. Re-running the pipeline
overwrites them in place.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt      # CPD/PMD via Docker only
make all                                       # all present subjects, all stages
make all SUBJECTS="flask swe_flask"            # subset
make complexity                                # one stage
make significance                              # Mann-Whitney U / Fisher's exact
make tables                                    # re-aggregate existing JSON
```

Fully reproducible run (installs PMD/CPD + a JRE, and is the only path that
produces the duplication numbers):

```bash
make docker && make docker-run   # mounts subjects/ ro, results/ rw
```

## What is wired in this checkout

The two **human baselines** are cloned at their pinned tags
(`snapshots/MANIFEST.txt`) and marked `available` in the registry, and both
oracle suites are complete, so the pipeline runs end-to-end today:

```bash
pip install -r requirements-analysis.txt
pip install -e subjects/flask -e subjects/django   # brings in transitive deps
make all SUBJECTS="flask django"
```

Each oracle passes **100%** against its own reference baseline (Flask 133/133,
Django 97/97 parametrised cases): the suite is derived from the written
specification, and the reference implementation is the one that specification
describes, so a passing score is the expected sanity result. The committed
`logs/oracle-flask-verbose.log` and `logs/oracle-django-verbose.log` list every
case. Complexity, maintainability, security, and smells populate
`results/tables/` from the same run; `logs/` holds that run's console output and
`logs/environment.txt` records the exact interpreter and tool versions.

> **Note on case counts.** The oracle *source* defines 119 Flask and 85 Django
> test functions; `pytest` parametrisation expands these to 133 and 97 cases,
> which is what `results/` and the tables report. Cite whichever the paper
> uses consistently.

### Agentic subjects

Three agentic subjects are registered `available: false`:

| id                | agent + model                          | spec pair |
|-------------------|----------------------------------------|-----------|
| `swe_flask`       | SWE-agent 1.0.0 + Claude Sonnet 4      | flask     |
| `openhands_flask` | OpenHands 0.14.0 + GPT-4o              | flask     |
| `swe_django`      | SWE-agent 1.0.0 + Claude Sonnet 4      | django    |

Each was generated in a fixed budget from a natural-language spec only, five
times per configuration (15 runs). Those snapshots, their agent traces, and
their raw measurement outputs are distributed in the **generation bundle**, not
in this harness — they are the output of specific generation runs and are not
reproducible from this repo. Drop a frozen snapshot under `subjects/<id>/`,
flip `available` to `true`, and it joins every table.

### Maturity control

`flask_0_1` (registered `available: false`, no oracle) is the initial public
release of Flask — a human-authored first draft, matched to the agentic subjects
on development maturity. It is a **structural reference point only** (RQ2–RQ5);
it predates Blueprints and other specified behaviours, so it is not
oracle-evaluated. Clone it per `snapshots/MANIFEST.txt` and set `available: true`.

### Run variance

The paper's run-variance table reports each agentic metric as a median [min, max]
over the five generation runs of that configuration. This harness scores one
snapshot per registry entry, so the run-to-run spread is assembled in the
generation bundle across the five per-configuration snapshots. Significance
testing (below) does run here, against whichever agentic snapshot is registered.

## Adding subjects

Drop the frozen source under `subjects/<id>/`, add an entry to
`subjects/subjects.json` with its source `path`, `kind` (`human`/`agentic`),
`pair`, `oracle` (empty for a structural-only reference), and set
`available: true`. Use `include` to restrict a subject to sub-packages (Django
uses `["urls", "views"]`). Missing or unavailable subjects are skipped with a
note — the pipeline always emits whatever tables the present data supports.

## How each metric is computed

- **Complexity** — Radon's API gives per-function cyclomatic complexity and
  per-file Maintainability Index (`multi=True`, comment-aware); complexipy gives
  per-function cognitive complexity. Thresholds match the paper: CC > 10,
  CogC > 15, MI < 65.
- **Security** — Bandit's full default plugin set, filtered to Medium-confidence
  or higher, normalised per 100 LOC (same convention as the pylint density
  below), with test-ids mapped to CWE classes (Cotroneo et al.'s mapping; see
  the paper's security-tool subsection). Findings also carry their raw Bandit
  test-id, so `analysis/aggregate.py` can render the Bandit-ID -> CWE breakdown
  (`table_cwe_<pair>.csv`) independently of the collapsed per-CWE counts in
  `table_security.csv`.
- **Smells** — pylint JSON reporter; F/I categories dropped (see the paper's
  code-smell subsection); reported as totals, per-100-LOC density, and C/R/W/E
  breakdown.
- **Duplication** — CPD with a 50-token minimum; duplicated blocks, duplicated
  LOC, duplicated fraction, largest block in tokens, and a per-file duplicated
  LOC / duplicated-% breakdown (feeds the file-level significance test below).
  Requires PMD + a JRE, so it is produced only in the Docker path.
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
pinned PMD in the Dockerfile) yield numerically identical `results/`. The
interpreter and resolved tool versions behind the committed `results/` are in
`logs/environment.txt`.
