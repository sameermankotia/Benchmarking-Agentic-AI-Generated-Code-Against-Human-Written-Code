# Pipeline run logs

Frozen console output from the analysis pipeline, committed so a reviewer can
see the raw tool invocations and their results without re-running anything.

| File | What it is |
|------|------------|
| `environment.txt`          | Interpreter, platform, and the exact `requirements-analysis.txt` tool versions behind the run below. |
| `make-all.log`             | Full `python run_all.py --subjects flask django` transcript (every stage, in order). |
| `stages/repo_stats.log`    | Structural characteristics stage. |
| `stages/correctness.log`   | RQ1 — oracle suites executed against each subject. |
| `stages/complexity.log`    | RQ2 + MI (Radon + complexipy). |
| `stages/smells.log`        | RQ3 — pylint. |
| `stages/security.log`      | RQ4 — Bandit. |
| `stages/duplication.log`   | RQ5 — CPD. Skips outside the Docker path (needs PMD + a JRE). |
| `stages/significance.log`  | Mann-Whitney U / Fisher's exact. Skips until an agentic subject is registered. |
| `stages/aggregate.log`     | CSV table assembly. |
| `oracle-flask-verbose.log` | Per-case `pytest -v` for the Flask oracle vs. the Flask baseline (133/133). |
| `oracle-django-verbose.log`| Per-case `pytest -v` for the Django oracle vs. the Django baseline (97/97). |

## Scope

These logs cover the two **human baselines** (Flask 3.0.3, Django 5.0.6), which
are the subjects wired in this checkout. The agentic snapshots are not part of
this harness repository (see the top-level `README.md`), so no agentic stage
output appears here — and with no agentic subject present, the `duplication`
(Docker-only) and `significance` stages have nothing to do.

## Reproducing

The committed numbers come from `requirements-analysis.txt` verbatim, on the
same Python the Dockerfile uses (`python:3.11-slim`). `complexipy` in particular
is version-sensitive: `analysis/complexity.py` targets the pinned `0.4.0` Rust
binding, and a newer `complexipy` silently reports cognitive complexity as `0`.

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt
pip install -e subjects/flask -e subjects/django
python run_all.py --subjects flask django
```

Duplication additionally needs the Docker path (`make docker && make docker-run`).
