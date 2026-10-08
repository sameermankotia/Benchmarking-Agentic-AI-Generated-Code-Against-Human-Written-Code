# Manuscript vs. measured data — audit

Every number in this file was produced by this harness, from the pinned
snapshots in `snapshots/MANIFEST.txt` and the pinned toolchain in
`requirements-analysis.txt` / `Dockerfile`, and is reproducible with:

```bash
make docker && make docker-run                    # all stages incl. RQ5
docker run --rm -v "$PWD/subjects:/work/subjects:ro" \
  -v "$PWD/results:/work/results" agentic-benchmark make duplication
```

"Manuscript" refers to *Structural Quality and Security in Agentic Software
Engineering: A Multi-Dimensional Empirical Evaluation* (revised draft, abstract
through Section III-D). Numbers quoted from it are the **human-baseline**
columns, which are the only columns this package can check — see
§4 below for the agentic columns.

Audit date: 2026-10-08. All numbers below come from the hermetic Docker image,
which is now the single provenance for `results/` — see §6 for the four harness
defects that had to be fixed before the package could reproduce itself, and for
the three measured values that changed as a result.

---

## 1. Table 1 (run variance), human-baseline column

| Metric | Flask: draft | Flask: measured | Django: draft | Django: measured |
|---|---|---|---|---|
| Oracle pass rate (%) | 90.8 | **100.0** (133/133) | 91.8 (78/85) | **100.0** (97/97) |
| Mean CC | 3.2 | **2.8** | 3.4 | **2.8** |
| Mean CogC | 6.1 | **2.1** | 6.3 | **2.7** |
| Mean MI | 71.4 | **64.1** | 72.1 | **75.1** |
| Security findings / 100 LOC | 0.29 | **0.26** | 0.26 | **0.03** |
| Duplicated LOC (%) | 3.1 | **3.4** | 2.9 | **1.0** |

Sources: `results/tables/summary.csv`, `table_complexity.csv`,
`table_maintainability.csv`, `table_security.csv`, `table_duplication.csv`.

Notes:

- **Mean CogC is the largest gap** (~3x on both baselines). complexipy 0.4.0
  implements the SonarSource cognitive-complexity algorithm; a value near 6 for
  Flask's core would require a different tool, a different version, or a
  different aggregation (e.g. a per-file rather than per-function mean).
- **Django security density is off by an order of magnitude** (0.26 vs. 0.03).
  Bandit finds exactly one medium-or-higher-confidence issue in
  `django/urls/` + `django/views/` (CWE-502). The draft's 0.26/100 LOC would
  imply roughly nine findings.
- **Django MI moves in the opposite direction**: measured Django (75.1) is
  *more* maintainable than measured Flask (64.1), while the draft has them
  nearly equal and both higher.
- **Flask duplication is the closest match in the whole table** (3.1 vs. 3.4).

## 2. Table 2 (structural characteristics), human-baseline columns

| Attribute | Flask: draft | Flask: measured | Django: draft | Django: measured |
|---|---|---|---|---|
| Lines of code | 3,847 | **4,243** | 4,213 | **3,520** |
| Source files | 18 | **24** | 21 | **28** |
| Functions / methods | 214 | **362** | 231 | **296** |
| Classes | 31 | **47** | 39 | **69** |
| LOC per function | 18.0 | **18.4** | 18.2 | **14.0** |
| Test files | 42 | 0 (see below) | 38 | 0 (see below) |
| Comment density (%) | 18.4 | **12.7** | 19.1 | **5.8** |
| Docstring coverage (%) | 72.0 | **60.6** | 74.2 | **53.4** |

Source: `results/tables/table_repo_stats.csv`, `results/repo_stats/*.json`.

The **test-file counts are not a contradiction**: the harness counts files
inside the analysis scope (`src/flask/`, `django/urls/` + `django/views/`), and
neither scope contains tests. The draft is evidently counting the upstream
repository's `tests/` tree. If the draft keeps that row, it needs a footnote
saying the count is repository-wide while every other row in the column is
scope-limited — otherwise the row is measuring a different population than its
neighbours.

The remaining rows are the same scope the rest of the paper uses, and they do
not reproduce. Note that LOC, files, functions, and classes are all *higher*
than the draft for Flask but the LOC figure is *lower* for Django, so this is
not a single consistent offset (e.g. not comments-excluded vs. comments-included).

## 3. Maturity reference point (Flask 0.1)

The abstract and Section III-B3 claim the human-written first draft "scores
better than the mature release on every structural metric," and that the
maturity effect therefore runs opposite to the agentic gap. Measured, that
holds for three of six structural metrics and reverses for the other three:

| Metric | Flask 0.1 | Flask 3.0.3 | First draft better? |
|---|---|---|---|
| Mean CC | 1.7 | 2.8 | yes |
| Mean CogC | 0.8 | 2.1 | yes |
| Duplicated LOC (%) | 0.0 | 3.4 | yes |
| Mean MI | **40.6** | **64.1** | **no** |
| pylint findings / 100 LOC | **15.66** | **6.36** | **no** |
| Security findings / 100 LOC | **0.40** | **0.26** | **no** |

Its size also does not match: measured **249 SLOC** (663 physical lines in the
single pre-package `flask.py`) against the draft's reported 1,284.

The claim that survives the data is narrower and still useful: *on complexity
and duplication, the human first draft is better than the mature release, so
maturity cannot explain an agentic deficit on those dimensions.* On MI, smells,
and security density the first draft is worse than the mature release, which
means maturity is a live confound for exactly those three dimensions and the
control does not clear it. The abstract's "every structural metric" and the
blanket "the maturity effect runs opposite in direction to the agentic gap"
both overstate what was measured.

A single-module 249-SLOC subject also has a mechanical effect on MI: Radon's MI
is computed per file, so Flask 0.1 contributes one file-level value (40.6) and
has a median identical to its mean, while Flask 3.0.3's 64.1 is a mean over 24
files. That is worth a sentence in the paper rather than being left for a
reviewer to find.

## 4. What this package cannot check at all

- **Every agentic number.** All three agentic subjects are `available: false`;
  their snapshots are absent from this checkout and from the author's machine
  (searched 2026-09-15 and again 2026-10-08). That covers the abstract's
  10–13 pp correctness gap, 47–53% CC, 38–46% CogC, 12.5–14.2 MI points,
  2.2–2.3x security density, and 152–161% duplication, plus every agentic cell
  in Tables 1 and 2 and all of Sections IV–V.
- **Every p-value and effect size.** `analysis/significance.py` tests each
  agentic subject against the human baseline in its own pair, so with no
  agentic subject registered the stage exits with
  `SKIP: no agentic/human pair had results for any dimension`
  (`logs/stages/significance.log`). There is no `results/significance/`.
- **The manuscript's oracle pass rates.** The committed oracle files are
  documented in their own `oracle/{flask,django}/README.md` as a partial
  stand-in ("the full case set ... is distributed separately"); that fuller set
  was never added. What ships is 119 Flask / 85 Django test *functions*
  (133 / 97 after parametrisation) and it passes 100% against both baselines.
  Category counts differ from the draft as well:

  | Flask category | Draft | Shipped | Django category | Draft | Shipped |
  |---|---|---|---|---|---|
  | URL Routing | 25 | 31 | URL Resolution | 22 | 24 |
  | Request Handling | 20 | 23 | Request Object | 18 | 22 |
  | Response Rendering | 18 | 22 | Response Handling | 15 | 19 |
  | Templating | 15 | 15 | View Dispatch | 20 | 22 |
  | App Context | 22 | 22 | Class-Based Views | 10 | 10 |
  | Blueprints | 20 | 20 | | | |
  | **Total** | **120** | **133** | **Total** | **85** | **97** |

  The draft's per-category human failures (e.g. App Context 19/22,
  Blueprints 13/20) are not reproducible from anything in this repository.

## 5. Open blocker: the oracle is bound to Flask's API names

This is not a number mismatch; it is a defect in the instrument, and it blocks
RQ1 even once the agentic snapshots arrive.

`oracle/conftest.py` resolves the system-under-test generically: the correctness
runner exports `SUT_IMPORT` and prepends the subject's source root to
`PYTHONPATH` (`analysis/correctness.py:43-68`), and the shared conftest aliases
that package to `sut`. That part is implementation-neutral and its docstring
correctly advertises `sut.Application()` as the specification-level usage.

The Flask suite then ignores that neutrality. Of the 12 distinct symbols it
reaches through the SUT handle, **8 are Flask API names that the specification
never mentions**:

| Symbol | Uses | In the specification? |
|---|---|---|
| `request` | 17 | yes |
| `Blueprint` | 15 | yes |
| `g` | 11 | yes |
| `current_app` | 9 | yes |
| `make_response` | 4 | **no** |
| `url_for` | 3 | **no** |
| `abort` | 2 | **no** |
| `Response` | 2 | **no** |
| `render_template_string` | 2 | **no** |
| `jsonify` | 1 | **no** |
| `redirect` | 1 | **no** |
| `Flask` | 1 | **no** |

The last one is fatal on its own: `oracle/flask/conftest.py` builds the
application with `sut_module.Flask(__name__)`, and the `app` fixture feeds
almost every test in the suite. An agent given the Section III-B4 specification
has no reason to name its application class `Flask` — the specification names
`current_app`, `g`, and `Blueprint`, but never the class, `url_for`, `abort`,
`jsonify`, `redirect`, `make_response`, `render_template_string`, or
`test_client`. Against any agentic subject that chose `Application` or `App`,
the fixture raises `AttributeError` and the affected cases error out rather
than reporting a behavioural failure.

Consequences for the draft:

- The claim in Section III-D that one suite "runs unchanged" against Flask, the
  SWE-agent framework, and the OpenHands framework is false for the suite in
  this repository.
- The `\authortodo` in Section III-D1 asks for a description of "a thin adapter
  that maps specification-level names to each subject's import paths." No such
  adapter exists. `docs/oracle-binding.tex` documents the binding mechanism
  that *does* exist and deliberately does not claim an adapter.
- Section III-D2's statement that a second reviewer rewrote fourteen cases "to
  use more generic assertions" is not observable in this suite.
- Any agentic pass rate measured with the suite as it stands would understate
  correctness by an unknown amount and would not be a valid RQ1 result.

Required before RQ1 is measurable: a name-resolution layer (resolve the
application class and each helper by trying specification-level candidates, or
require each subject to ship a small declarative mapping), applied identically
to the human baselines so the baseline numbers stay comparable. This changes the
measurement instrument, so it should be done before, not after, the agentic
snapshots are scored.

## 6. Harness defects found and fixed

Checking the draft against the package meant running the package, which
surfaced four defects. All four are fixed in this commit, and `results/` was
regenerated end-to-end from the hermetic image afterwards.

### 6.1 The committed results were not produced by the pinned toolchain

`logs/environment.txt` claimed the toolchain was "requirements-analysis.txt,
verbatim." It was not. The host virtualenv that produced the committed
`results/` had drifted:

| Tool | Pinned | Host venv (produced the old results/) |
|---|---|---|
| complexipy | 0.4.0 | **6.0.1** |
| pylint | 3.1.0 | **4.0.6** |
| pytest | 8.1.1 | **9.1.1** |
| radon | 6.0.1 | 6.0.1 |
| bandit | 1.9.4 | 1.9.4 |

The two oracle verbose logs came from a third environment again (a scratchpad
virtualenv, visible in the old log header). Everything in `results/` and
`logs/` is now produced by one path: `make docker && make docker-run`.

Reassuringly, **CC, CogC, MI, security, repo-stats and duplication are
bit-identical under complexipy 0.4.0 and 6.0.1** — so the RQ2/RQ3/RQ4 numbers
in §1 above were never version artifacts, and the draft's mean-CogC gap is not
explained by toolchain drift. Only pylint-dependent numbers moved.

### 6.2 pylint's smell count was nondeterministic

`cyclic-import` (R0401) is not a per-file smell; pylint emits it once per
detected cycle after walking the whole import graph, and its count varies
between identical runs. Four runs of the same image over the same mounted
snapshot gave Flask 276 / 277 / 276 / 276 and Django 387 / 387 / 388 / 388.
That contradicted the package's central determinism claim.

R0401 is now excluded both at the pylint invocation and when tallying
(`analysis/smells.py`). Five consecutive runs then gave identical counts.
**The paper's code-smell subsection needs a sentence recording this
exclusion**, alongside the existing note that F- and I-category messages are
dropped.

### 6.3 The hermetic path scored unimportable subjects 0%

The image installed the analysis tools but not the subjects' own runtime
dependencies, so no subject could be imported inside it. The oracle therefore
skipped every case — and `_parse_junit` counted a skipped case toward the
denominator but not the numerator, so `make docker-run`, the path the README
advertises as the fully reproducible one, reported **0/133 and 0/97 (0.0%)**
for the two human baselines.

Two fixes: `requirements-subjects.txt` pins the baselines' runtime
dependencies and the image installs them, and `analysis/correctness.py` now
counts skips separately, computes the pass rate over *executed* cases, and
raises rather than reporting a rate when nothing executed.

This failure mode matters well beyond the Docker path. It is exactly what an
agentic subject hits when its application class is not named `Flask` (§5): the
suite would have reported a confident **0% agentic pass rate** that actually
meant "never ran." Given the draft reports agentic pass rates in the 75–83%
range, this is not the origin of those numbers — but it is a trap for the
re-run.

### 6.4 Absolute paths leaked into the committed artifact

Bandit and CPD report absolute paths, and those were stored verbatim, so
`results/security/*.json` carried `/Users/<author>/Desktop/Agentic/...` and
`results/duplication/*.json` carried the container mount point. Both are now
stored relative to the subject root, which also removes a spurious host-vs-
container difference.

### 6.5 Net effect on the measured values

Only pylint-derived numbers changed. Everything else is identical to what was
committed before:

| Metric | Was committed | Now (reproducible) |
|---|---|---|
| Flask pylint findings | 276 (6.5 / 100 LOC) | **270 (6.36)** |
| Django pylint findings | 387 (10.99 / 100 LOC) | **384 (10.91)** |
| Flask 0.1 pylint findings | 39 (15.66) | 39 (15.66) — unchanged |
| CC / CogC / MI / security / duplication / repo stats | — | all unchanged |

Determinism is now verified rather than asserted: two independent `make all`
runs produced byte-identical JSON and CSV. The two JUnit XML reports differ
only in per-test `time`, `timestamp`, and container `hostname`; stripped of
those three attributes they hash identically.

## 7. Smaller items

- `README.md` listed `results/significance/` in the layout as if shipped.
  Corrected to mark it absent in this checkout.
- `README.md` said "both oracle suites are complete," contradicting the
  discrepancy note directly below it. Corrected.
- `logs/environment.txt` said RQ5 was "not exercised here." It now is, and the
  record names the image, PMD 7.0.0, the JRE, and the determinism check.
- Added `.dockerignore`: the build context previously included the 59 MB host
  virtualenv and the 307 MB of baseline snapshots that `make docker-run` mounts
  anyway, which also risked a stale host copy shadowing the mount.

## 8. Status summary

| Manuscript element | Status |
|---|---|
| Table 1, human columns | **does not reproduce** (6/6 Flask, 6/6 Django differ) |
| Table 2, human columns | **does not reproduce** (7/8 rows differ; test-file row is a scope artifact) |
| Maturity claim (Flask 0.1) | **partly contradicted** (3/6 metrics reverse; LOC off by 5x) |
| RQ5 duplication, human columns | **measured as of 2026-10-08**; Flask 3.1→3.4, Django 2.9→1.0 |
| All agentic columns, Sections IV–V | **no data in existence** |
| All p-values / effect sizes | **not computed** |
| Oracle pass rates | **not reproducible**; suite is a stand-in and is Flask-bound |
| Code-smell numbers | **measured, and now reproducible**; Flask 6.5 -> 6.36, Django 10.99 -> 10.91 per 100 LOC |
| Package determinism claim | **was false, now verified** (see §6.1-6.2) |
