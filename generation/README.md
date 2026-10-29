# Generation harness — the 15 agentic subjects

This directory produces the agentic half of the study. It was missing from the
replication package entirely: `analysis/` could *measure* subjects, but nothing
could *produce* them, so the generation step was not reproducible even in
principle and no run of it is archived here.

```
specs/flask.md        the Flask-pair specification, verbatim from the manuscript
specs/django.md       the Django-pair specification (RECONSTRUCTED — see below)
run_generation.py     the runner: 3 configurations x 5 runs = 15 subjects
runs/<run_id>/        per-run agent trace + stdout/stderr   (committed)
runs/MANIFEST.json    per-run timing, tool-call count, commit sha, outcome
work/                 scratch tree the agent edits while running (git-ignored)
```

## What a run is

Each run gets the specification text and nothing else — no reference source, no
oracle tests, no issue tracker — in a clean directory seeded only with a
skeleton `pyproject.toml` declaring `jinja2`, `werkzeug`, `pytest`. The study's
budget is applied per run: **90 minutes wall clock, 500 tool calls,
temperature 0.2**, against a pinned model snapshot.

| Configuration     | Agent              | Model                   | Spec   | Runs |
|-------------------|--------------------|-------------------------|--------|-----:|
| `swe_flask`       | SWE-agent 1.0.0    | `--anthropic-model`     | flask  |    5 |
| `openhands_flask` | OpenHands 0.14.0   | `--openai-model`        | flask  |    5 |
| `swe_django`      | SWE-agent 1.0.0    | `--anthropic-model`     | django |    5 |

**Models are a study variable, not a default.** `--anthropic-model` defaults to
`claude-sonnet-5-5`, the current successor to the Sonnet tier the study
used, which keeps the comparison like-for-like; `claude-opus-5-5` is the more
capable option. `--openai-model` has no default on purpose — run
`--list-models` with a key present to see what the account actually serves,
rather than having a guessed id baked in. `--study-models` restores the
pair the study used, `anthropic/claude-sonnet-4` and `gpt-4o-2024-11-20`, if
the providers still serve them; note that OpenRouter resolves the Claude id to
whatever snapshot it is serving and does not report which, so the dated Claude
snapshot cannot be pinned on this route and the paper does not claim it was
(§III-B4). **Whichever pair is used must be named in the paper**, including in
Section III-B, the study-design figure, and the abstract.

Hitting the 90-minute cap is a study outcome, not a failure: the tree is frozen
as it stands, which is what the budget is for. On completion each run is
committed, copied to `subjects/<run_id>/`, registered in
`subjects/subjects.json` with `available: true`, and its trace archived under
`runs/<run_id>/`. `make all` then scores it alongside the human baselines.

## Running it

```bash
# 1. install the agents (neither is installed in this checkout)
pip install 'git+https://github.com/SWE-agent/SWE-agent.git@v1.0.0'
pip install openhands-ai==0.14.0

# 2. provide credentials in the environment — never on the command line,
#    never in a file inside this repository
export ANTHROPIC_API_KEY=...     # for the two SWE-agent configurations
export OPENAI_API_KEY=...        # for the OpenHands configuration

# 3. check everything before spending anything
python generation/run_generation.py --preflight

# 4. validate end to end on one run first
python generation/run_generation.py --config swe_flask --runs 1

# 5. the full study, both agents at once
python generation/run_generation.py --parallel 3
```

`--parallel N` runs N generations concurrently. It is a genuine speed-up — 15
sequential runs is up to ~22 hours, three at a time brings that to ~8 — but it
is **not free of consequence**: the budget is 90 minutes of *wall clock*, so
concurrent runs compete for CPU, for Docker, and for the provider's rate limit,
and a contended run can hit the cap having completed less work than an
uncontended one would. That biases the very thing the study measures. The
concurrency level is written into `runs/MANIFEST.json` for exactly this reason,
and it belongs in Section III-B2 alongside the budget.

Note also that `swe_flask` and `swe_django` share one Anthropic key, so running
both concurrently halves each one's effective rate limit. If you parallelise,
`--parallel 2` across the two *providers* (one SWE-agent config plus the
OpenHands config) contends less than `--parallel 3`.

`--dry-run` prints the plan without contacting any provider. A real run refuses
to start unless preflight passes, so a missing credential or a retired model
snapshot stops the harness instead of producing a partial study.

Credentials are read from the environment only. They are never logged, echoed,
or written into a trace, a manifest, or any other artifact.

## Two things to settle before generating

**Which models.** The study used Claude Sonnet 4, reached through OpenRouter
as `anthropic/claude-sonnet-4`, and `gpt-4o-2024-11-20`; both are old and may
no longer be served. The OpenAI snapshot is dated and therefore pinnable; the
Claude one is not, because OpenRouter does not expose the dated identifier of
the snapshot it serves — which is why the paper records the identifier it
requested and states that the snapshot served is unknown (§III-B4). Preflight
queries each provider's model endpoint and fails with an explicit message on a
404, and `--list-models` shows what the account can reach. Generating against
current models is the better study — but it is a *different* study from the one
the paper describes, and every claim about Claude Sonnet 4 and GPT-4o has to
change with it, including the paper's framing of which systems were compared.

**The Django specification in `specs/django.md` is a reconstruction.** Unlike
the Flask specification, its text appears nowhere in the manuscript or in any
earlier version of this package — the manuscript only describes it ("rephrased
to Django's request and response model", five behavioural areas). The file
reconstructs it from that description and is marked as such at the top. The
Django oracle's scope derives from those five areas, so if the original text
still exists it should replace that file before anything is generated.

## Cost and time

15 runs at up to 90 minutes each is up to ~22 hours of wall clock sequentially,
or roughly a third of that at `--parallel 3`. Runs are sequential by default so
that each gets its full budget without contention.

The 500-call budget per run bounds the token spend, and each run additionally
carries a hard per-run cost cap (`PER_RUN_COST_LIMIT_USD`, $10, passed to
SWE-agent as `--agent.model.per_instance_cost_limit` and to OpenHands as `-b`),
so the worst case across 15 runs is bounded at $150. A run that hits the cost
cap is truncated, which would bias its metrics, so the manifest records the cap
and any run that reached it has to be reported rather than pooled with the
others. The spend is real and lands on whichever account the keys belong to --
here, the `OCR-Eval-Dashboard` vault's. Start with one run.
