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
                              (not in this checkout: needs a registered agentic subject)
results/tables/               aggregated CSV tables          (committed)
logs/                         frozen pipeline run transcripts (committed)
docs/manuscript-audit.md      manuscript claims vs. measured values
docs/oracle-binding.tex       Section III-D1 text (resolves its authortodo)
requirements-analysis.txt     pinned analysis toolchain
requirements-subjects.txt     pinned runtime deps of the baseline snapshots
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

The two **human baselines** and the **maturity control** are cloned at their
pinned tags (`snapshots/MANIFEST.txt`) and marked `available` in the registry,
and both oracle suites execute end-to-end today -- but see the discrepancy
note below: the committed oracle files are a partial stand-in for the suite
that produced the manuscript's numbers:

```bash
pip install -r requirements-analysis.txt
pip install -r requirements-subjects.txt           # the subjects' own runtime deps
make all SUBJECTS="flask django flask_0_1"
```

`requirements-subjects.txt` is not optional. Without the subjects' runtime
dependencies on the path, pylint cannot resolve their imports and reports 63
spurious `import-error` findings for Flask alone, and the oracle cannot import
any subject at all. The Docker image installs it too.

Each oracle passes **100%** against its own reference baseline (Flask 133/133,
Django 97/97 parametrised cases): the suite is derived from the written
specification, and the reference implementation is the one that specification
describes, so a passing score is the expected sanity result. The committed
`logs/oracle-flask-verbose.log` and `logs/oracle-django-verbose.log` list every
case. Complexity, maintainability, security, and smells populate
`results/tables/` from the same run; `logs/` holds that run's console output and
`logs/environment.txt` records the exact interpreter and tool versions.

> **⚠ Open discrepancy with the manuscript, not yet resolved.** The oracle
> files under `oracle/flask/` and `oracle/django/` are explicitly documented,
> in their own `README.md`, as a partial stand-in: "*the full case set ... is
> distributed separately in the replication package.*" That fuller case set
> has never been added to this repository. What ships here is 119 Flask / 85
> Django test **functions** (133 / 97 after `pytest` parametrisation), and it
> passes 100% against both human baselines. The manuscript reports 120 / 85
> **cases** with the human baseline passing 90.8% / 92.4%, including specific
> per-category failures (e.g. Flask App Context 19/22, Blueprints 13/20) that
> this suite does not reproduce, because it is not the suite that produced
> those numbers. Until the actual full oracle suite is added, `results/` and
> every table in this package reflect the placeholder suite, not the
> manuscript's Table 3/Table 1 (variance) figures — do not cite one for the
> other.
>
> **It is also not portable.** `oracle/flask/conftest.py` builds the
> application with `sut_module.Flask(__name__)`, and 8 of the 12 symbols the
> Flask suite reaches through the SUT handle (`Flask`, `url_for`, `abort`,
> `jsonify`, `redirect`, `make_response`, `render_template_string`, `Response`)
> are Flask API names the specification never mentions. Against an agentic
> subject that named its application class anything else, those cases error
> instead of reporting a behavioural result, so the suite cannot produce a
> valid RQ1 number for the agentic subjects until a name-resolution layer is
> added. See `docs/manuscript-audit.md` §5.

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

`flask_0_1` (registered `available: true`, no oracle) is the initial public
release of Flask — a human-authored first draft, matched to the agentic subjects
on development maturity. It is a **structural reference point only** (RQ2–RQ5);
it predates Blueprints and other specified behaviours, so it is not
oracle-evaluated. Its `flask.py` uses two Python-2-only `except X, e:` clauses
that don't parse under Python 3; both are mechanically rewritten to
`except X as e:` before analysis (`snapshots/flask-0.1-patch.md`).

> **⚠ Open discrepancy with the manuscript.** Measured against the pinned
> toolchain, Flask 0.1's Maintainability Index (40.6) is *lower* than Flask
> 3.0.3's (64.1) — the opposite of Table 11's claim that the first draft
> "scores better than the mature release on every structural metric." Its LOC
> (249 SLOC / 663 physical lines in the single `flask.py`) is also well under
> the manuscript's reported 1,284. This package reports the real, reproduced
> number; it does not match the manuscript's maturity-control table.

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
  code-smell subsection), and `cyclic-import` (R0401) excluded as an
  order-dependent whole-import-graph message rather than a per-file smell (see
  "Determinism"); reported as totals, per-100-LOC density, and C/R/W/E
  breakdown. The subjects' runtime dependencies must be installed, or pylint
  reports an `import-error` per unresolved module and the density measures the
  analysis environment instead of the code.
- **Duplication** — CPD with a 50-token minimum; duplicated blocks, duplicated
  LOC, duplicated fraction, largest block in tokens, and a per-file duplicated
  LOC / duplicated-% breakdown (feeds the file-level significance test below).
  Requires PMD + a JRE, so it is produced only in the Docker path; the
  committed `results/duplication/` came from that path (PMD 7.0.0, see
  `logs/environment.txt`).
- **Correctness** — each oracle suite runs against a subject through the
  canonical `sut` import (see `oracle/conftest.py`); JUnit XML is bucketed into
  the paper's behavioural categories by test-file stem. Skipped cases count as
  *not evaluated*, never as failures: the pass rate is computed over executed
  cases, and a subject whose cases all skipped (typically an import failure)
  raises instead of being scored 0%, which would otherwise be
  indistinguishable from a subject that implemented nothing.

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

## Determinism

Verified, not just asserted: two independent `make all` runs of the pinned
image over the same mounted snapshots produce **byte-identical** `results/` --
every JSON and every CSV. The two JUnit XML reports differ only in their
per-test `time`, `timestamp`, and container `hostname` attributes; stripped of
those three they hash identically.

Reaching that required excluding pylint's `cyclic-import` (R0401), which is a
whole-import-graph message rather than a per-file smell and whose count varies
between identical runs (measured: Flask 276/277/276/276, Django 387/387/388/388
over four runs). It is excluded at the invocation and again when tallying; see
`analysis/smells.py`. **The paper's code-smell subsection needs a sentence
recording this exclusion.**

All of `results/` and `logs/` now comes from one path, `make docker &&
make docker-run`. Earlier committed results came from a host virtualenv whose
versions had drifted from the pins (complexipy 6.0.1, pylint 4.0.6, pytest
9.1.1 rather than 0.4.0 / 3.1.0 / 8.1.1); `logs/environment.txt` records this
and the exact resolved versions. CC, CogC, MI, security, repo-stats and
duplication are identical under both complexipy majors -- only the
pylint-derived smell counts moved (Flask 6.5 -> 6.36, Django 10.99 -> 10.91 per
100 LOC). See `docs/manuscript-audit.md` §6.
