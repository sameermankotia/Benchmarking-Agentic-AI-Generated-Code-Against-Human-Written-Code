# Agentic vs. Human Benchmark — Replication Package

Analysis harness and frozen artifact for *Structural Quality and Security in
Agentic Software Engineering: A Multi-Dimensional Empirical Evaluation.*

It runs one deterministic pipeline over all 18 study subjects, renders the
paper's tables as CSV, and computes every number the paper quotes into a single
figure set. Five quality dimensions, five research questions:

| RQ  | Dimension               | Tool(s)                         | Module                     |
|-----|-------------------------|---------------------------------|----------------------------|
| RQ1 | Functional correctness  | pytest (oracle suites)          | `analysis/correctness.py`  |
| RQ2 | Complexity (CC + CogC)  | Radon + complexipy              | `analysis/complexity.py`   |
| RQ3 | Maintainability         | Radon (MI) + pylint             | `analysis/complexity.py`, `analysis/smells.py` |
| RQ4 | Security density        | Bandit (+ CWE mapping)          | `analysis/security.py`     |
| RQ5 | Code duplication        | CPD (PMD)                       | `analysis/duplication.py`  |

Every dimension is also tested for statistical significance against the
human baseline of the same pair. The tests the paper reports (Mann-Whitney U,
Fisher's exact, and an exact rate test with LOC exposure) are computed by
`analysis/paper_tests.py`; see "Statistical testing".

## Layout

```
subjects/subjects.json        subject registry (paths, kind, oracle, analysis scope)
subjects/<id>/                frozen snapshots: 15 agentic runs committed,
                              3 human baselines cloned at their pinned tags
snapshots/MANIFEST.txt        every subject's commit, scope, and generation budget
oracle/wsgi.py                PEP 3333 driver (all behavioural assertions)
oracle/api.py                 declared construction surface (role resolution)
oracle/flask, oracle/django   specification-derived oracle suites + conftest
oracle/BINDING-DEFECTS.md     every binding defect found while scoring, and its cost
generation/                   the generation harness, specs, and frozen agent traces
analysis/                     one module per stage + significance + aggregator
analysis/paper_numbers.py     the figure set: medians, ranges, ratios, generation facts
analysis/paper_tests.py       the per-run significance tests the paper reports
run_all.py                    orchestrator (`make all` calls this)
results/<dimension>/          per-subject result JSON        (committed)
results/significance/         Mann-Whitney U / Fisher's exact per agentic run
results/tables/               aggregated CSV tables          (committed)
results/paper_numbers.json    medians, ranges, ratios, generation facts (committed)
results/paper_tests.json      per-run tests and "k/5" counts as in the paper (committed)
logs/                         frozen pipeline run transcripts (committed)
requirements-analysis.txt     pinned analysis toolchain
requirements-subjects.txt     pinned runtime deps of the baseline snapshots
Dockerfile, Makefile          hermetic execution
LICENSE, CITATION.cff         MIT license; how to cite
```

`results/` and `logs/` are committed frozen: the package ships the raw numbers
the paper reports, not just the code that produces them. Re-running the
pipeline overwrites them in place. The release the paper cites is tagged
`v1.0-ieee-access`.

## Quick start

The fully reproducible path, and the only one that produces the duplication
numbers (CPD needs PMD and a JRE):

```bash
make docker && make docker-run     # mounts subjects/ ro, results/ rw
```

Without Docker, on Python 3.11:

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt -r requirements-subjects.txt
make all                           # every stage, every subject; RQ5 skips
make all SUBJECTS="flask swe_flask_run01"
make complexity                    # one stage
make significance                  # Mann-Whitney U / Fisher's exact
make tables                        # re-aggregate existing JSON
make paper-numbers                 # rebuild results/paper_numbers.json
make check-paper-numbers           # verify the committed figure set
make paper-tests                   # rebuild results/paper_tests.json
make check-paper-tests             # verify the committed test results
```

`requirements-subjects.txt` is not optional. Without the subjects' runtime
dependencies on the path, pylint cannot resolve their imports and reports 63
spurious `import-error` findings for Flask alone, and the oracle cannot import
any subject at all. The Docker image installs it too.

## The subjects

**Human baselines.** The `src/flask/` core package of `pallets/flask` at
`3.0.3`, and the `django/urls/` + `django/views/` packages of `django/django`
at `5.0.6`. Both are cloned, not vendored; `snapshots/MANIFEST.txt` has the
commit SHAs and the clone commands.

**Maturity reference point.** `flask_0_1`, the first public release of Flask —
a human-written first draft, matched to the agentic subjects on development
maturity, and a structural reference point only (RQ2–RQ5): it predates
Blueprints and other specified behaviours, so it is not oracle-evaluated. Its
`flask.py` uses two Python-2-only `except X, e:` clauses that do not parse
under Python 3; both are mechanically rewritten to `except X as e:` before
analysis (`snapshots/flask-0.1-patch.md`). Measured, it has lower complexity
(CC 1.7 vs. 2.8, CogC 0.8 vs. 2.1) and less duplication (0.0% vs. 3.4%) than
the mature release, but a lower Maintainability Index (40.6 vs. 64.1) and
higher smell and security densities (15.66 vs. 6.36, and 0.40 vs. 0.26 per 100
LOC) — so maturity is ruled out as an explanation for the complexity and
duplication results and remains a live confound for the other three. Radon
computes MI per file, so this single-module subject contributes one file-level
value and its mean equals its median.

**Agentic subjects.** All 15 are committed under `subjects/*_run*/`, with their
traces under `generation/runs/`: they are the output of stochastic runs against
hosted models and cannot be regenerated identically, so they are the one part
of this package that is shipped rather than reproduced.

| config            | agent + model                                   | spec pair | runs |
|-------------------|-------------------------------------------------|-----------|-----:|
| `swe_flask`       | SWE-agent 1.0.0 + `anthropic/claude-sonnet-4`   | flask     | 5 |
| `openhands_flask` | OpenHands 0.14.0 + `gpt-4o-2024-11-20`          | flask     | 5 |
| `swe_django`      | SWE-agent 1.0.0 + `anthropic/claude-sonnet-4`   | django    | 5 |

Each run started from a new Git repository whose single commit holds two
files: the specification as `SPECIFICATION.md` and a skeleton `pyproject.toml`
declaring `jinja2`, `werkzeug` and `pytest` (none of them installed). The same
specification file is also the agent's task: SWE-agent receives it as the issue
text of its first prompt, OpenHands as its first user message. Each run had 90
minutes, a 500 step budget, temperature 0.2, and a $10 cost cap. A step is one
model call that issues one tool call: the budget is SWE-agent's
`per_instance_call_limit` and OpenHands' `MAX_ITERATIONS`, and in every
SWE-agent trajectory the number of model calls equals the number of tool calls.
SWE-agent runs with its default configuration, which is written for resolving
issues in an existing repository (and tells the agent not to install packages).
Two departures from the paper's stated design, both disclosed in it: Claude was
reached through OpenRouter, which does not expose the dated snapshot
identifier, so the snapshot actually served is not recorded; and the $10 cap is
additional to the paper's wall-clock and step budgets, and bound on
`swe_flask_run03` and `swe_django_run05`. Two of the five OpenHands traces
(`openhands_flask_run01`, `openhands_flask_run02`) were not captured.

**Analysis scope.** For the human baselines, the measured package (which
contains no tests). For each agentic run, the framework package the agent
created, declared as `include` in the registry. Example applications, ad-hoc
test files and debugging scripts left beside that package are excluded, so
every subject is measured on its implementation code only: SWE-agent left 1 to
15 such files per run, OpenHands 0 to 1.

## The oracle suites are portable

Both suites stand on two layers:

- `oracle/wsgi.py` drives each subject over its **WSGI interface**, which the
  specification does fix ("must pass a WSGI compliance check"), so every
  behavioural assertion reads a status line, a response header, or a response
  body.
- `oracle/api.py` resolves the small **declared construction surface** — the
  application class, route registration, blueprint class and registration,
  response class, template renderer, the request attributes, and
  variable-segment syntax — from a subject's `api_map` in the registry, then
  from conventional candidate names, then by raising an error that names the
  unresolved role. An unresolved role is a loud failure, never a silent zero.

`grep` the suites for `Flask`, `django`, `test_client`, `url_for`, `jsonify`
or `HttpResponse`: no matches. An agentic subject that names things differently
declares them once in `subjects.json`; no test body changes.

Each suite passes **100%** against its own reference baseline (Flask 140/140,
Django 104/104 parametrised cases, no skips). That is a construct check, not a
finding: the reference implementation is the thing the specification describes,
so passing is the expected result. `logs/oracle-flask-verbose.log` and
`logs/oracle-django-verbose.log` list every case.

A specification-derived oracle can also fail a *working* framework over a
convention the specification never fixes. Every time that happened while the 15
agentic subjects were scored is recorded in
[`oracle/BINDING-DEFECTS.md`](oracle/BINDING-DEFECTS.md): nine defects (eight
in the oracle's binding, one in the analysis stage's scope filter), what each
cost, and what was changed. Both baselines held at 100% through all nine. That
shows no fix narrowed what the oracle accepts; it does not prove that a widened
binding can never accept behaviour outside the specification. The same file
lists the known conventions that were left unfixed and reported as bounds in
the paper (string templates, plain string returns from views).

## The paper's figure set

The paper quotes medians over the five runs of each configuration, ranges,
ratios to a baseline, counts of runs that differ significantly, and a handful
of generation facts. None of those is a stage output, so none of them is read
off a table by hand:

`results/paper_numbers.json` is keyed by paper element — `table_repo_stats`,
`rq1_correctness` … `rq5_duplication`, `maturity_reference_point`,
`generation`, `claims` — and each entry carries the figure, its range over the
runs, and the inputs it came from. It aggregates the per-subject JSON, the
oracle's JUnit reports (for the cases that fail in every run of a
configuration), the frozen generation traces (per-run cost, model calls,
wall-clock, agent steps), and the subjects themselves (per-file line counts).
Three things it measures that no stage does:

- **the size-matched Maintainability Index.** Radon's MI falls with file
  length, so a repository of small files scores higher whatever it contains.
  Here the baseline is restricted to the files whose SLOC falls inside the range
  the configuration's own files span, and the comparison is also reported per
  LOC band. The variant the paper reports (human files no larger than the
  largest agentic file, with a descriptive Mann-Whitney test) is computed by
  `analysis/paper_tests.py`.
- **Jinja2 autoescaping**, read at the `Environment` construction. Eight of the
  ten Flask-specification runs create a Jinja2 environment and five of those
  eight leave autoescaping off. Bandit flags all five (B701); the oracle sees
  only one of them, because a subject whose rendering fails emits no markup to
  escape, so its autoescaping case passes vacuously.
- **the files each agent left outside the measured package.**

`make all` runs this and then `analysis/paper_tests.py` as its last stages,
so the committed figure set and test results always come from the committed
`results/`.

## Adding subjects

Drop the frozen source under `subjects/<id>/`, add an entry to
`subjects/subjects.json` with its source `path`, `kind` (`human`/`agentic`),
`pair`, `oracle` (empty for a structural-only reference), and set
`available: true`. Use `include` to restrict a subject to the package being
measured (Django uses `["urls", "views"]`; each agentic run names its framework
package). The three `available: false` entries are the configuration rows,
whose runs are the `*_run0N` subjects. Missing or unavailable subjects are
skipped with a note — the pipeline always emits whatever tables the present
data supports.

## How each metric is computed

- **Complexity** — Radon's `cc_visit` gives one cyclomatic complexity value
  per block: every function, method and class. Class blocks are included in all
  CC statistics; Radon folds nested functions into the function that encloses
  them, so Flask 3.0.3 has 380 blocks (334 functions and methods plus 46
  classes) against the 362 functions that `repo_stats` counts. complexipy gives
  per-function cognitive complexity. Radon's per-file Maintainability Index uses
  `multi=True` (multi-line strings count as comments), logical lines of code,
  a cap at 100, and the value 100 for a file with zero Halstead volume (Radon
  counts only unary, binary, Boolean, comparison and augmented-assignment
  operators). Thresholds match the paper: CC > 10, CogC > 15, and MI < 65 on
  Radon's 0 to 100 scale (a reference line, not Coleman et al.'s threshold,
  which is 65 on the original 171-point scale, about 38 on Radon's).
- **Security** — Bandit's full default plugin set, filtered to Medium
  confidence or higher, normalised per 100 LOC, with test-ids mapped to CWE
  classes (Cotroneo et al.'s mapping; see the paper's security-tool
  subsection). Findings also carry their raw Bandit test-id, so
  `analysis/aggregate.py` can render the Bandit-ID → CWE breakdown
  (`table_cwe_<pair>.csv`) independently of the collapsed per-CWE counts in
  `table_security.csv`.
- **Smells** — pylint JSON reporter; F/I categories dropped (see the paper's
  code-smell subsection), and `cyclic-import` (R0401) excluded as an
  order-dependent whole-import-graph message rather than a per-file smell (see
  "Determinism"); reported as totals, per-100-LOC density, C/R/W/E
  breakdown, the 15 most frequent symbols, and the full per-symbol counts
  (`symbols`). The cosmetic / non-cosmetic split the paper reports uses the
  layout and naming symbols listed in `analysis/paper_tests.py` (`COSMETIC`).
  `analysis/paper_numbers.py` also reports a narrower trailing-whitespace-only
  split (`trailing_whitespace_share_pct`, `non_cosmetic_per_100_loc` there),
  which is not the one in the paper.
- **Duplication** — CPD with a 50-token minimum; duplicated blocks, duplicated
  LOC, duplicated fraction, largest block in tokens, and a per-file breakdown
  (which feeds the file-level significance test). Requires PMD + a JRE, so it
  is produced only in the Docker path.
- **Correctness** — each oracle suite runs against a subject through the
  canonical `sut` import (see `oracle/conftest.py`); JUnit XML is bucketed into
  the paper's behavioural categories by test-file stem. Skipped cases count as
  *not evaluated*, never as failures: the pass rate is computed over executed
  cases, and a subject whose cases all skipped (typically an import failure)
  raises instead of being scored 0%, which would otherwise be
  indistinguishable from a subject that implemented nothing. No subject in this
  study had a skipped case.

### Statistical testing

Every test compares one **agentic** run with the **human baseline of its own
pair**, two-sided, at alpha = 0.05. Runs are not pooled; the paper reports,
per configuration, in how many of the five runs a test rejects and in which
direction ("5/5 higher").

**What the paper reports: `analysis/paper_tests.py`** (`make paper-tests`,
output `results/paper_tests.json`):

- **Mann-Whitney U** on per-block CC, per-function CogC and per-file MI, with
  effect size `r = 2*U_A/(n_A*n_H) - 1`, where `U_A` is the statistic of the
  agentic sample, so `r > 0` means the agentic values tend to be larger.
- **Fisher's exact test** on the share of blocks with CC > 10, of functions
  with CogC > 15, of files with MI < 65, and on oracle pass/fail totals. Oracle
  cases are not independent (one defect can fail many cases), so the RQ1
  results are descriptive.
- **Exact conditional binomial test of equal Poisson rates**, with LOC as the
  exposure, for pylint messages (all, and non-cosmetic), Bandit findings and
  CPD blocks.
- **Size-matched MI**: agentic files pooled over the five runs against the
  human files no larger than the largest agentic file; Mann-Whitney U,
  descriptive because files of different runs are pooled.

**Earlier per-run tests: `analysis/significance.py`** (`make significance`,
output `results/significance/<run_id>.json`). This stage predates the paper's
final test set and is kept because `analysis/aggregate.py` folds its p-values
into the CSV tables. It runs Mann-Whitney U on CC, CogC, per-file MI and
per-file duplicated-LOC %, and Fisher's exact on oracle pass/fail (per category
and overall) and on Bandit severity bands. Its effect size is
`rank_biserial = 1 - 2U/(n_agentic*n_human)`, the **opposite sign** of the
paper's `r`. `results/paper_numbers.json` counts rejecting runs from this
stage for the tests the two have in common, and those counts agree with
`results/paper_tests.json`.

### Cross-repository consistency

`analysis/aggregate.py` also renders one `table_quality_gap_<run_id>.csv` per
agentic run: oracle pass rate, mean CC, mean CogC, mean MI, security
findings/100 LOC, and duplicated LOC%, each as human-baseline value, agentic
value, and a delta (percentage points for the pass rate, MI points for MI,
relative % otherwise).

## Determinism

Verified, not asserted: two independent `make all` runs of the pinned image
over the same mounted snapshots produce **byte-identical** `results/` — every
JSON, including `paper_numbers.json`, and every CSV. The 17 JUnit XML reports
are the one exception, and differ only in (a) the per-test `time`, `timestamp`
and container `hostname` attributes and (b) the CPython object addresses pytest
embeds in the failure text of a failing case; normalising both, all 17 hash
identically.

Reaching that required two things. pylint's `cyclic-import` (R0401) is a
whole-import-graph message whose count varies between identical runs (measured:
Flask 276/277/276/276, Django 387/387/388/388 over four runs); it is excluded at
the invocation and again when tallying (`analysis/smells.py`).
`results/paper_numbers.json` carries no generation timestamp; the run's date is
in `logs/environment.txt` instead.

All of `results/` and `logs/` comes from one path, `make docker &&
make docker-run`, for all 18 subjects. `logs/environment.txt` records the image,
the interpreter, the resolved tool versions, PMD and JRE versions, and the
determinism check.
