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

## 4. The agentic subjects now exist and are measured

**Superseded.** Earlier versions of this audit recorded that no agentic
snapshot existed anywhere. All 15 were generated on 2026-10-13 by
`generation/run_generation.py`, are committed under `subjects/*_run*/`, and
are scored by the same pipeline as the human baselines. Section 9 reports the
results, which contradict the manuscript's claimed gaps on four of six
dimensions.

Two departures from the manuscript's stated design were forced and must be
disclosed:

- **Claude was reached through OpenRouter**, as `anthropic/claude-sonnet-4`.
  The account has no Anthropic API key, and OpenRouter does not expose the
  dated `claude-sonnet-4-20250514` snapshot, so Section III-B2's "both model
  snapshots were pinned" is no longer accurate as written.
- **Each run carried a $10 cost cap** in addition to the wall-clock and
  tool-call budgets. This is not in the manuscript, and it bound on one run
  (Section 9.3).
- **P-values and effect sizes now compute.** `analysis/significance.py` runs
  against every agentic subject; the stage no longer skips.
- **The manuscript's oracle pass rates.** The committed oracle files are
  documented in their own `oracle/{flask,django}/README.md` as a partial
  stand-in ("the full case set ... is distributed separately"); that fuller set
  was never added. What ships is 119 Flask / 85 Django test *functions*
  (133 / 97 after parametrisation) and it passes 100% against both baselines.

  **Correction to an earlier version of this audit.** The draft's category
  counts are *test-function* counts, and at that level they very nearly
  matched the suite that shipped: Flask 25/20/18/15/22/20 against an actual
  24/20/18/15/22/20 (only URL Routing was off, by one), and Django
  22/18/20/15/10 against an actual 22/18/20/15/10 — exact. The 133 and 97
  figures are post-parametrisation counts, which is what the correctness
  stage reports. So the draft's Table 3 structure was sound; what was not
  reproducible was the human baseline *failing* any of it (the draft's App
  Context 19/22 and Blueprints 13/20), since the shipped suite passed 100%.

  Both suites have since been rebuilt (§5), which changes these counts
  again — see the table there.

## 5. The oracle was bound to its reference implementations — rebuilt

### 5.1 What was wrong

Both suites were conformance suites for the implementation they were written
against, not oracles for the specification.

**Flask.** Of 30 distinct symbols the suite reached through the subject, only
four — `request`, `Blueprint`, `g`, `current_app` — were named in the
specification. The other 26 were Flask API names it never mentions: `route`,
`test_client`, `register_blueprint`, `config`, `url_map`, `add_url_rule`,
`app_context`, `test_request_context`, `before_request`, `after_request`,
`teardown_request`, `teardown_appcontext`, `errorhandler`, `abort`, `jsonify`,
`redirect`, `make_response`, `render_template_string`, `Response`, `url_for`,
`name`, and the HTTP verb methods of Flask's test client — plus the private
`_get_current_object`. 94 of 119 test functions touched at least one, and all
119 depended on the application class being called `Flask`, via the `app`
fixture's `sut_module.Flask(__name__)`.

**Django.** Worse: all five test files hard-imported by literal module path —
`from django.urls import path, resolve, Resolver404`, `from django.http import
HttpResponse`, `from django.views import View`, `django.views.decorators.*` —
bypassing the `sut` handle entirely. No adapter could have made that suite run
against anything but Django.

Consequently Stage 4's claim that the suites "interact only with the public
surface named in the specification" was false for both, and RQ1 could not have
been measured for any agentic subject.

### 5.2 What replaced it

Both suites are rebuilt on two layers:

- **`oracle/wsgi.py`** — a PEP 3333 driver. Every behavioural assertion is now
  made by calling the subject as a WSGI application and reading the status
  line, response headers, and response body. The specification requires that
  an implementation "pass a WSGI compliance check," so WSGI is the one
  interface it fixes for every subject; that is what lets one suite run
  against implementations sharing no API names. The driver also exercises
  `start_response`, an iterable body, and `close()`, and rejects a response
  iterable yielding non-bytes.
- **`oracle/api.py`** — the declared construction surface: the minimum set of
  roles needed to *build* a subject. Each resolves from the subject's
  `api_map` in `subjects/subjects.json`, then from conventional candidate
  names, then raises `RoleUnresolved` naming the role and listing what the
  subject exposes. Request attributes are resolved the same way, because the
  specification names the concepts ("method, path, headers, query string, and
  body") but not the attribute names. Variable-segment syntax is declared too.

The four specification-named symbols are still read directly. Everything else
goes through a role. `grep` the suites for `Flask`, `django`, `test_client`,
`url_for`, `jsonify`, `render_template` or `HttpResponse`: no matches, in
either pair.

### 5.3 Measured result

Both human baselines pass completely on the rebuilt suites, with no skips:

| Pair | Functions | Cases | Baseline result |
|---|---:|---:|---|
| Flask | 117 | **140** | Flask 3.0.3 — 140/140 (100%) |
| Django | 85 | **104** | Django 5.0.6 URL module — 104/104 (100%) |

Per category:

| Flask category | Cases | | Django category | Cases |
|---|---:|---|---|---:|
| URL Routing | 30 | | URL Resolution | 25 |
| Request Handling | 28 | | Request Object | 26 |
| Response Rendering | 24 | | View Dispatch | 22 |
| Templating | 15 | | Response Handling | 21 |
| App Context | 21 | | Class-Based Views | 10 |
| Blueprints | 22 | | | |
| **Total** | **140** | | **Total** | **104** |

**These are the counts the paper should now report**, in place of 120 and 85.
`docs/oracle-binding.tex` is the Section III-D1 text for the new design and
also resolves the `\authortodo` that recorded the blocker.

### 5.4 What this changes about scope

Restricting assertions to the specified surface means behaviour the
specification never mentions is now absent rather than required. Omitted from
the Flask pair: lifecycle hooks, error handlers, typed URL converters, form
parsing, cookie handling, URL building. Omitted from the Django pair:
middleware, sessions, authentication, ORM access, URL reversing, and any
assertion about what is served for an empty URL configuration (a framework may
serve a landing page; the specification does not say). Two cases were dropped
for the same reason during the rebuild — a raw assertion on a form-encoded
body, since an implementation may legitimately parse it out of the stream, and
the empty-urlconf case.

This narrows RQ1's construct, and the paper should say so: the oracle now
measures conformance to the written specification over WSGI, not parity with
the reference implementation's API. That is the stronger claim for the study's
purpose, but it is a different one.

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

This failure mode mattered well beyond the Docker path. It was exactly what an
agentic subject would have hit when its application class was not named
`Flask`: the suite would have reported a confident **0% agentic pass rate**
that actually meant "never ran." Both halves of that trap are now closed — the
runner refuses to score an unexecuted suite (here), and the suites no longer
depend on the class name at all (§5).

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
| Oracle pass rates | **suites rebuilt over WSGI** (§5); baselines now 140/140 and 104/104, and the paper's 120/85 case counts become 140/104 |
| Code-smell numbers | **measured, and now reproducible**; Flask 6.5 -> 6.36, Django 10.99 -> 10.91 per 100 LOC |
| Package determinism claim | **was false, now verified** (see §6.1-6.2) |

## 9. Measured results for the 15 agentic runs

Generated 2026-10-13 by `generation/run_generation.py`; scored by the same
pipeline as the human baselines. Medians across the five runs of each
configuration, with observed ranges.

| Metric | Flask (H) | SWE-agent/Flask | OpenHands/Flask | Django (H) | SWE-agent/Django |
|---|---|---|---|---|---|
| Oracle pass % | 100 | **73.6** [66.4, 75.0] | **15.0** [5.0, 20.0] | 100 | **96.2** [91.3, 100] |
| LOC | 4,243 | 540 [414, 644] | 74 [48, 102] | 3,520 | 337 [270, 484] |
| Mean CC | 2.8 | **2.3** [2.1, 2.4] | **2.0** [1.6, 2.5] | 2.8 | **2.5** [2.4, 2.7] |
| Mean CogC | 2.1 | **1.9** [1.4, 2.3] | **0.7** [0.2, 0.8] | 2.7 | **1.7** [1.6, 1.8] |
| Mean MI | 64.1 | **72.3** [69.1, 74.0] | **80.0** [50.0, 91.7] | 75.1 | **78.6** [64.9, 82.8] |
| pylint / 100 LOC | 6.36 | **28.42** [25.4, 30.6] | **32.43** [22.9, 38.5] | 10.91 | **30.74** [28.5, 55.2] |
| Security / 100 LOC | 0.26 | **0** [0, 0.23] | **1.35** [0, 2.08] | 0.03 | **0** [0, 7.38] |
| Duplicated % | 3.4 | **0** [0, 2.3] | **0** [0, 0] | 1.0 | **0** [0, 50.3] |

### 9.1 Four of six abstract claims are contradicted in direction

| Dimension | Abstract claims | Measured |
|---|---|---|
| Correctness | −10 to −13 pp | −26.4 pp (SWE/Flask), −85.0 pp (OpenHands), −3.8 pp (SWE/Django) |
| Mean CC | +47 to +53% | **−18%**, **−29%**, **−11%** |
| Mean CogC | +38 to +46% | **−10%**, **−67%**, **−37%** |
| Mean MI | −12.5 to −14.2 pts | **+8.2**, **+15.9**, **+3.5 pts** |
| Security density | 2.2–2.3x | 0x, 5.2x, 0x |
| Duplication | +152 to +161% | **−100%**, **−100%**, **−100%** |

The direction reverses on complexity, cognitive complexity, maintainability
and duplication, in all three configurations, across fifteen runs. Correctness
goes the predicted way but far harder than claimed. Security is mixed: only
OpenHands exceeds its baseline.

**The one robust agentic deficit not in the abstract is code smells**: 28–31
findings per 100 LOC against 6.4–10.9 for the baselines, a 3–5x gap present in
every configuration. On the current evidence this is the headline result, not
complexity.

**The Django pair is the strongest single finding.** SWE-agent's median is
96.2%, with two runs at a perfect 104/104, and its complexity distribution is
statistically indistinguishable from Django's own (CC p=0.47–0.90). An agent
given a five-area specification produced a URL/view layer that satisfies it
completely. That is the opposite of the manuscript's thesis and deserves to be
reported as such.

### 9.2 Scale is a confound on every density

The agentic repositories are 7x to 88x smaller than their baselines
(48–644 LOC against 3,520–4,243). Per-function means and per-100-LOC
densities are not comparable across that range, and OpenHands' Maintainability
Index of 80 largely reflects very small files rather than good structure. Any
density figure quoted from the OpenHands configuration needs this stated
alongside it.

Run-to-run spread is also wide where the manuscript implies stability:
OpenHands correctness spans 5.0–20.0% and MI spans 50.0–91.7. The five-run
design earns its place.

### 9.3 One run was truncated by the cost cap

`swe_flask_run03` ended with SWE-agent's `exit_status: "submitted
(exit_cost)"` at $10.06, i.e. it hit the harness's $10 per-run guard rather
than the study's wall-clock or tool-call budget. Its metrics come from an
incomplete run and it should be re-run with a higher cap or excluded. Observed
costs for the other SWE-agent runs were $4.45–$9.75, so the cap was close to
binding on several.

### 9.4 Seven oracle defects were fixed to obtain these numbers

Every one was the oracle penalising a working framework for a convention the
specification does not fix. They are listed because they bound how much
confidence these figures carry:

1. `app_class` unresolvable by name (`FlaskPair`) — now also resolved by shape.
2. Views called with the request positionally — all oracle views now accept it.
3. Blueprint registration inverted (`bp.register(app)`) — three directions now accepted.
4. Response headers set via Django's `resp[name] = value` only — now convention-agnostic.
5. Django wiring assumed settings + `ROOT_URLCONF` — a factory taking urlpatterns is now accepted.
6. `include` matched only the first path component, so **all five OpenHands subjects measured zero files**.
7. URL patterns assumed Django's slashless spelling — the subject's convention is now detected per session.

Fix 7 alone moved `swe_django_run01` from 12.5% to 95.2%. The human baselines
held at 140/140 and 104/104 through all seven changes, which is the control
that makes the rest trustworthy. The OpenHands figures remain the least
settled and warrant a second pass before publication.

### 9.5 Cost

Roughly $70 on the keys in `op://OCR-Eval-Dashboard/dashboard-secrets`
($4.45–$10.06 per SWE-agent run; the OpenHands runs were cheap, finishing in
48–64 s). Those keys belong to a different project. One of them was briefly
exposed in a process listing by an earlier version of the harness and should
be rotated.
