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

## Layout

```
subjects/subjects.json   subject registry (paths, kind, oracle, availability)
subjects/<id>/           frozen snapshots (git submodules / mounted read-only)
oracle/flask, oracle/django   specification-derived oracle suites + conftest
analysis/                one module per stage + common helpers + aggregator
run_all.py               orchestrator (`make all` calls this)
results/<dimension>/     per-subject result JSON
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
  or higher, normalised per kLOC, with test-ids mapped to CWE classes
  (§3.5.4).
- **Smells** — pylint JSON reporter; F/I categories dropped (§3.5.3); reported
  as totals, per-100-LOC density, and C/R/W/E breakdown.
- **Duplication** — CPD with a 50-token minimum; duplicated blocks, duplicated
  LOC, duplicated fraction, and largest block in tokens.
- **Correctness** — each oracle suite runs against a subject through the
  canonical `sut` import (see `oracle/conftest.py`); JUnit XML is bucketed into
  the paper's behavioural categories by test-file stem.

Determinism: identical inputs + pinned tools (`requirements-analysis.txt`,
pinned PMD in the Dockerfile) yield numerically identical `results/`.
