# Pipeline run logs

Frozen console output from the analysis pipeline, committed so a reviewer can
see the raw tool invocations and their results without re-running anything.

| File | What it is |
|------|------------|
| `environment.txt`          | Interpreter, image, platform, PMD/JRE, the exact `requirements-analysis.txt` tool versions behind the run below, and the determinism check. |
| `make-all.log`             | Full `make all` transcript from the hermetic image (every stage, in order, all 18 subjects). |
| `stages/repo_stats.log`    | Structural characteristics stage. |
| `stages/correctness.log`   | RQ1 — oracle suites executed against each subject. |
| `stages/complexity.log`    | RQ2 + MI (Radon + complexipy). |
| `stages/smells.log`        | RQ3 — pylint. |
| `stages/security.log`      | RQ4 — Bandit. |
| `stages/duplication.log`   | RQ5 — CPD. Skips outside the Docker path (needs PMD + a JRE). |
| `stages/significance.log`  | Mann-Whitney U / Fisher's exact, each agentic run against its pair's baseline. |
| `stages/aggregate.log`     | CSV table assembly. |
| `stages/paper_numbers.log` | `results/paper_numbers.json` — the medians, ranges and ratios the paper quotes. |
| `oracle-flask-verbose.log` | Per-case `pytest -v` for the Flask oracle vs. the Flask baseline (140/140). |
| `oracle-django-verbose.log`| Per-case `pytest -v` for the Django oracle vs. the Django baseline (104/104). |

## Scope

These logs cover every subject in the study: the two **human baselines**
(Flask 3.0.3, Django 5.0.6), the **maturity reference point** (Flask 0.1,
structural metrics only), and the **15 agentic runs** frozen under
`subjects/*_run*/`. The three `available: false` entries that appear as skipped
in the transcript are the registry's configuration rows (`swe_flask`,
`openhands_flask`, `swe_django`); the runs themselves are the `*_run0N`
subjects.

`flask_0_1`'s source (`subjects/flask-0.1/flask.py`) required two
mechanical Python-2-to-3 syntax fixes (`except X, e:` -> `except X as e:`,
the only construct in the file that Python 3's `ast` cannot parse) before any
tool in this pipeline could analyze it; see `snapshots/flask-0.1-patch.md`.

## Reproducing

Everything here comes from the pinned image, which is the only path that has
PMD/CPD and therefore the only one that produces RQ5:

```bash
make docker && make docker-run
```

`complexipy` in particular is version-sensitive: `analysis/complexity.py`
targets the pinned `0.4.0` Rust binding, and a newer `complexipy` silently
reports cognitive complexity as `0`. Running the pipeline outside the image
means installing both requirement files on Python 3.11 by hand:

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt -r requirements-subjects.txt
python run_all.py            # RQ5 skips: no PMD
```
