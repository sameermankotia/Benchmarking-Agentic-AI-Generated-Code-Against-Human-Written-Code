# Generation harness: the 15 agentic subjects

This directory produced the agentic half of the study, and it archives what
each run produced. The 15 runs were generated on 14 October 2026 (UTC), two at a
time, and are frozen under `subjects/<run_id>/` with their traces under
`runs/<run_id>/`. Hosted models are not deterministic, so rerunning the harness
produces new subjects, not these ones.

```
specs/flask.md        the Flask-pair specification, as delivered to every Flask run
specs/django.md       the Django-pair specification (a reconstruction, see below)
run_generation.py     the runner, one configuration x five runs at a time
runs/<run_id>/        per-run agent trace + stdout/stderr   (committed)
runs/MANIFEST.json    per-run timing, commit sha, outcome
work/                 scratch tree the agent edits while running (git-ignored)
```

**Do not edit the files in `specs/`.** They are the exact files the agents
received. SWE-agent names each run after a hash of the file (`3159b3` for Flask,
`859eb1` for Django, the directory names under `runs/swe_*`), and the OpenHands
traces log the delivered text in full, so any edit breaks the check that ties a
run to its specification.

## What a run is

`seed_workdir()` creates a new Git repository whose single commit holds two
files: the specification as `SPECIFICATION.md`, and a skeleton `pyproject.toml`
declaring `jinja2`, `werkzeug` and `pytest`. No reference source, no oracle
tests and no issue tracker are present, and no third-party package is
installed in the agent's container. The same specification file is also the
agent's task:

1. **SWE-agent** receives it through `--problem_statement.path`, which inserts
   it as the issue text of the first prompt. SWE-agent runs with its default
   configuration (`config/default.yaml`), whose prompt is written for resolving
   an issue in an existing repository, recommends reproducing the bug first,
   and tells the agent not to install packages.
2. **OpenHands** receives it through `-f`, which sends it as the first user
   message.

Budget per run: **90 minutes wall clock, 500 steps, temperature 0.2, and a $10
cost cap.** A step is one model call that issues one tool call. For SWE-agent the
budget is `--agent.model.per_instance_call_limit` (a model-call limit; in every
committed trajectory the number of model calls equals the number of tool
calls). For OpenHands it is `MAX_ITERATIONS` / `-i` (agent iterations, each one
model call and one action). The cost cap is passed to SWE-agent as
`--agent.model.per_instance_cost_limit` and to OpenHands as `-b`. It bound on
`swe_flask_run03` and `swe_django_run05`, which the paper reports.

| Configuration     | Agent              | Model (as run)                         | Spec   | Runs |
|-------------------|--------------------|----------------------------------------|--------|-----:|
| `swe_flask`       | SWE-agent 1.0.0    | `openrouter/anthropic/claude-sonnet-4` | flask  |    5 |
| `openhands_flask` | OpenHands 0.14.0   | `gpt-4o-2024-11-20`                    | flask  |    5 |
| `swe_django`      | SWE-agent 1.0.0    | `openrouter/anthropic/claude-sonnet-4` | django |    5 |

Claude was reached through OpenRouter, which does not report the dated
snapshot it serves, so the snapshot behind `claude-sonnet-4` is not recorded.
The OpenAI snapshot is dated. These are also the harness defaults
(`DEFAULT_ANTHROPIC_MODEL`, `DEFAULT_OPENAI_MODEL`); `--anthropic-model` and
`--openai-model` override them, and any other model makes a different study.

### OpenHands in headless mode

When the OpenHands 0.14.0 agent considers its work done, it waits for user
input. Its `exit_on_message` option would answer `/exit`, but the 0.14.0 command
line does not expose it, so the harness keeps stdin open and answers every pause
with `/exit` (`AGENT_STDIN`). OpenHands' own benchmark scripts instead answer
with a message telling the agent to continue. In all three captured OpenHands
traces the run ended at the first such pause, after about a minute; the paper
discusses this choice as a threat to validity.

### What the traces show

1. Only `swe_flask_run04` installed a package (`pip install jinja2`). All five
   SWE-agent Flask runs import Jinja2 inside `try`/`except ImportError` with a
   string-substitution fallback, so their check scripts ran the fallback.
2. In the three captured OpenHands traces the agent ran no program except its
   file editor and `mkdir`. `openhands_flask_run01` imports
   `werkzeug.serving.run_simple` inside its development-server method, which
   neither generation nor scoring calls.
3. The traces of `openhands_flask_run01` and `openhands_flask_run02` were not
   captured. For the other three, the first user message matches
   `specs/flask.md` byte for byte.

## The Django specification is a reconstruction

The original Django-pair specification was not preserved. `specs/django.md` was
written before generation from the description of it in an earlier version of
the manuscript, after the Django oracle had been written, and it is marked as
such at the top. It was not changed after generation (the hash in the SWE-agent
run directories matches it). The note at its top still says to replace it if
the original is found; that note predates generation and no longer applies,
because replacing the file now would break the link to the runs. The paper
treats the Django pass rates as an upper bound for this reason.

## Running it

```bash
# 1. install the agents
#    (the SWE-agent wheel omits config/, so install from a clone)
git clone --depth 1 -b v1.0.0 https://github.com/SWE-agent/SWE-agent.git generation/.swe-agent-src
uv venv --python 3.11 generation/.venv-sweagent
uv pip install --python generation/.venv-sweagent/bin/python -e generation/.swe-agent-src
docker pull ghcr.io/all-hands-ai/openhands:0.14.0   # 0.14.0 cannot be pip-installed

# 2. credentials: an exported OPENROUTER_API_KEY / OPENAI_API_KEY wins;
#    otherwise the harness reads the 1Password reference in SECRET_REFS
#    with `op read`. Keys are never logged, echoed, or written to disk.

# 3. check everything before spending anything
python generation/run_generation.py --preflight

# 4. one run first, then the rest without redoing it
python generation/run_generation.py --config swe_flask --runs 1
python generation/run_generation.py --config swe_flask --from-run 2 --runs 5
```

`--dry-run` prints the plan without contacting any provider. A real run refuses
to start unless preflight passes.

`--parallel N` runs N generations at once. The budget is wall clock, so
concurrent runs compete for CPU, Docker and the provider's rate limit; the
study used `--parallel 2`, and the concurrency is written into
`runs/MANIFEST.json`. `swe_flask` and `swe_django` share one OpenRouter key, so
running both at once halves each one's rate limit.

`runs/MANIFEST.json` is merged by run id, so running one configuration does not
erase the records of the others. (Before this fix it was overwritten on every
invocation, which is why the committed manifest records only the five
`swe_django` runs, the last configuration generated. Per-run cost, model calls
and wall clock for every SWE-agent run are in its trajectory under `runs/`,
and `analysis/paper_numbers.py` reads them from there.)

On completion each run is committed, copied to `subjects/<run_id>/`, registered
in `subjects/subjects.json` with `available: true`, and its trace is archived
under `runs/<run_id>/`. `make all` then scores it with the human baselines.
