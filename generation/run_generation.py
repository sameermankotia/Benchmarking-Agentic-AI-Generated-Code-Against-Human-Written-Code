"""Generate the agentic subjects: 15 runs, 3 configurations, fixed budget.

This is the generation half of the study, which the analysis harness consumes.
It was missing from the replication package entirely: `analysis/` could measure
subjects but nothing could produce them, so the generation step was not
reproducible even in principle.

Each run is given the specification text and nothing else -- no reference
source, no oracle, no issue tracker -- in a clean working directory seeded only
with a skeleton `pyproject.toml`. Runs are capped at the study's budget (90
minutes wall clock, 500 tool calls, temperature 0.2) against a pinned model
snapshot. On completion the working tree is frozen as a git commit, copied to
`subjects/<id>/`, and its agent trace archived under `generation/runs/<id>/`.

Usage
-----
    # what would run, no API calls, no cost
    python generation/run_generation.py --dry-run

    # check tooling + credentials + model reachability, then stop
    python generation/run_generation.py --preflight

    # one configuration, one run, to validate end to end before committing
    python generation/run_generation.py --config swe_flask --runs 1

    # the full study
    python generation/run_generation.py

Credentials are read from the environment (ANTHROPIC_API_KEY, OPENAI_API_KEY)
and are never logged, echoed, or written to any artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN_ROOT = REPO_ROOT / "generation"
SPEC_DIR = GEN_ROOT / "specs"
RUN_DIR = GEN_ROOT / "runs"
WORK_DIR = GEN_ROOT / "work"
SUBJECTS_DIR = REPO_ROOT / "subjects"

# --- The study's fixed budget (manuscript Section III-B4) ------------------- #
TIME_LIMIT_S = 90 * 60
TOOL_CALL_BUDGET = 500
TEMPERATURE = 0.2
RUNS_PER_CONFIG = 5

# Dependencies the skeleton declares, per the manuscript.
SKELETON_DEPS = ["jinja2", "werkzeug", "pytest"]

# Spend guard. The manuscript's budget is wall clock plus tool calls and says
# nothing about cost, but these runs bill a shared key, so each run is also
# capped in dollars. Set high enough that it should not bind before the
# 500-call limit does; a run that hits it is recorded as cost-capped, because
# that would truncate the run and bias its metrics.
PER_RUN_COST_LIMIT_USD = 10.0

# SWE-agent 1.0.0 is installed editable from a clone, because the wheel does
# not ship its config/ directory. OpenHands 0.14.0 cannot be installed at all
# on any Python this machine has (its e2b pin is unsatisfiable), so it runs
# from its official pinned image.
SWE_SRC = GEN_ROOT / ".swe-agent-src"
SWE_PY = GEN_ROOT / ".venv-sweagent" / "bin" / "python"
SWE_ENTRY = GEN_ROOT / "sweagent_entry.py"
OPENHANDS_IMAGE = "ghcr.io/all-hands-ai/openhands:0.14.0"
OPENHANDS_RUNTIME_IMAGE = "ghcr.io/all-hands-ai/runtime:0.14-nikolaik"


@dataclass
class Config:
    """One agent + model + specification combination."""

    id: str
    agent: str                  # "swe-agent" | "openhands"
    model: str                  # pinned snapshot
    spec: str                   # stem under generation/specs/
    key_env: str                # environment variable holding the credential
    pair: str
    label: str
    #: 1Password secret reference. Resolved with `op read` at launch and passed
    #: to the agent subprocess in its environment only -- never written to
    #: disk, a log, a trace or the manifest.
    secret_ref: str = ""
    #: Subject-registry ids are <id>_run<NN>; the representative run is chosen
    #: after analysis, not here.
    def run_id(self, n: int) -> str:
        return f"{self.id}_run{n:02d}"


# Default model per provider.
#
# The study used Claude Sonnet 4 (requested as anthropic/claude-sonnet-4) and
# gpt-4o-2024-11-20. Both are old and may no longer be served, so the defaults
# below are the current generation instead, and both are overridable with
# --anthropic-model / --openai-model. Whichever is used must be stated in the
# paper: the model is a study variable, not an implementation detail.
#
# Anthropic's current family is Claude 5. claude-sonnet-5-5 is the direct
# successor to the Sonnet tier the study used, which keeps the comparison
# like-for-like; claude-opus-5-5 is the more capable option.
# Claude is reachable here only through OpenRouter: this account has no
# Anthropic API key. litellm (used by both agents) takes the `openrouter/`
# prefix and reads OPENROUTER_API_KEY. The manuscript must say that Claude was
# routed via OpenRouter rather than called on the Anthropic API directly.
DEFAULT_ANTHROPIC_MODEL = "openrouter/anthropic/claude-sonnet-4"

# Deliberately unset. The current OpenAI model id is not assumed here -- pass
# --openai-model, or run --list-models with a key present to see what the
# account can actually reach.
DEFAULT_OPENAI_MODEL = "gpt-4o-2024-11-20"

#: The snapshots the manuscript pins, kept for reference and for reproducing
#: the original design if the provider still serves them.
#: The identifiers this study requested. The OpenAI one is a dated snapshot;
#: the Claude one is not, because OpenRouter does not expose the dated
#: identifier of the snapshot it serves (paper §III-B4).
STUDY_MODELS = {
    "OPENROUTER_API_KEY": "openrouter/anthropic/claude-sonnet-4",
    "OPENAI_API_KEY": "gpt-4o-2024-11-20",
}

#: Where each credential lives. These are references, not secrets.
SECRET_REFS = {
    "OPENROUTER_API_KEY":
        "op://OCR-Eval-Dashboard/dashboard-secrets/OPENROUTER_API_KEY",
    "OPENAI_API_KEY":
        "op://OCR-Eval-Dashboard/dashboard-secrets/OPENAI_API_KEY",
}

CONFIGS: list[Config] = [
    Config(id="swe_flask", agent="swe-agent",
           model=DEFAULT_ANTHROPIC_MODEL, spec="flask",
           key_env="OPENROUTER_API_KEY", pair="flask",
           label="SWE-agent (A)"),
    Config(id="openhands_flask", agent="openhands",
           model=DEFAULT_OPENAI_MODEL, spec="flask",
           key_env="OPENAI_API_KEY", pair="flask",
           label="OpenHands (A)"),
    Config(id="swe_django", agent="swe-agent",
           model=DEFAULT_ANTHROPIC_MODEL, spec="django",
           key_env="OPENROUTER_API_KEY", pair="django",
           label="SWE-agent/Dj. (A)"),
]


@dataclass
class RunResult:
    run_id: str
    config: str
    agent: str
    model: str
    spec: str
    started_utc: str = ""
    finished_utc: str = ""
    wall_seconds: float = 0.0
    tool_calls: int | None = None
    exit_status: str = "not-run"
    commit: str = ""
    note: str = ""
    files_written: int = 0
    trace_path: str = ""
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #

def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


_SECRET_CACHE: dict[str, str] = {}


def resolve_secret(key_env: str) -> str:
    """The credential for `key_env`, from the environment or 1Password.

    An already-exported environment variable wins, so a locally provisioned key
    overrides the shared vault without editing this file. Otherwise the value is
    read from 1Password through `op read`. The value is held in memory for the
    life of the process and is never logged, printed, or persisted.
    """
    if key_env in _SECRET_CACHE:
        return _SECRET_CACHE[key_env]
    value = os.environ.get(key_env, "")
    if not value:
        ref = SECRET_REFS.get(key_env, "")
        if ref and _have("op"):
            completed = subprocess.run(["op", "read", ref],
                                       capture_output=True, text=True)
            if completed.returncode == 0:
                value = completed.stdout.strip()
    _SECRET_CACHE[key_env] = value
    return value


def _agent_available(agent: str) -> tuple[bool, str]:
    if agent == "swe-agent":
        if (SWE_PY.exists() and SWE_ENTRY.exists()
                and (SWE_SRC / "config").is_dir()):
            return True, f"{SWE_PY} {SWE_ENTRY}"
        return False, (
            "not installed. The wheel omits config/, so install from a clone:\n"
            "    git clone --depth 1 -b v1.0.0 "
            "https://github.com/SWE-agent/SWE-agent.git "
            f"{SWE_SRC.relative_to(REPO_ROOT)}\n"
            f"    uv venv --python 3.11 "
            f"{(GEN_ROOT / '.venv-sweagent').relative_to(REPO_ROOT)}\n"
            f"    uv pip install --python "
            f"{(GEN_ROOT / '.venv-sweagent' / 'bin' / 'python').relative_to(REPO_ROOT)}"
            f" -e {SWE_SRC.relative_to(REPO_ROOT)}")
    if agent == "openhands":
        present = subprocess.run(
            ["docker", "image", "inspect", OPENHANDS_IMAGE],
            capture_output=True).returncode == 0
        if present:
            return True, OPENHANDS_IMAGE
        return False, (
            f"image not pulled. openhands-ai==0.14.0 cannot be pip-installed "
            f"on any Python here (its e2b pin is unsatisfiable), so the pinned "
            f"image is used instead:\n    docker pull {OPENHANDS_IMAGE}")
    return False, f"unknown agent {agent!r}"


def _model_reachable(config: Config) -> tuple[bool, str]:
    """Check the selected model is served, without generating tokens."""
    key = resolve_secret(config.key_env)
    if not key:
        return False, f"{config.key_env} is not set"
    try:
        import urllib.error
        import urllib.request
    except ImportError:                                   # pragma: no cover
        return False, "urllib unavailable"

    if config.key_env == "OPENROUTER_API_KEY":
        # litellm's "openrouter/" prefix is not part of the provider's id.
        remote_id = config.model.split("/", 1)[1]
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {key}"}
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=20) as response:
                ids = {m.get("id") for m in json.load(response).get("data", [])}
            return (remote_id in ids,
                    "listed" if remote_id in ids else f"{remote_id} not routable")
        except Exception as exc:                          # noqa: BLE001
            return False, f"{type(exc).__name__}: {exc}"
    else:
        url = "https://api.openai.com/v1/models/" + config.model
        headers = {"Authorization": f"Bearer {key}"}

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, (f"HTTP 404 - the pinned snapshot {config.model!r} "
                           f"is no longer served. The study cannot be "
                           f"reproduced against it; re-pin and say so in the "
                           f"manuscript.")
        if exc.code in (401, 403):
            return False, f"HTTP {exc.code} - credential rejected"
        return False, f"HTTP {exc.code}"
    except Exception as exc:                              # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def list_models() -> int:
    """Print the models each provider will actually serve to this account."""
    import urllib.error
    import urllib.request

    providers = [
        ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1/models?limit=100",
         lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"}),
        ("OPENAI_API_KEY", "https://api.openai.com/v1/models",
         lambda k: {"Authorization": f"Bearer {k}"}),
    ]
    for env, url, headers_for in providers:
        print(f"=== {env} ===")
        key = os.environ.get(env)
        if not key:
            print(f"  {env} is not set; cannot list\n")
            continue
        try:
            request = urllib.request.Request(url, headers=headers_for(key))
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            print(f"  HTTP {exc.code}\n")
            continue
        except Exception as exc:                          # noqa: BLE001
            print(f"  {type(exc).__name__}: {exc}\n")
            continue
        ids = sorted(entry.get("id", "?") for entry in payload.get("data", []))
        for model_id in ids:
            marker = ""
            if model_id == STUDY_MODELS.get(env):
                marker = "   <- the identifier this study requested"
            print(f"  {model_id}{marker}")
        if STUDY_MODELS.get(env) not in ids:
            print(f"  (the study's {STUDY_MODELS.get(env)!r} is "
                  f"NOT in this list)")
        print()
    return 0


def preflight(configs: list[Config], check_models: bool = True) -> bool:
    """Report everything that would stop a run, without starting one."""
    ok = True
    print("=== specifications ===")
    for spec in sorted({c.spec for c in configs}):
        path = SPEC_DIR / f"{spec}.md"
        mark = "ok" if path.exists() else "MISSING"
        if not path.exists():
            ok = False
        print(f"  {spec:8} {mark:8} {path.relative_to(REPO_ROOT)}")

    print("\n=== models ===")
    for config in configs:
        if config.model:
            print(f"  {config.id:18} {config.model}")
        else:
            ok = False
            flag = ("--openai-model" if config.key_env == "OPENAI_API_KEY"
                    else "--anthropic-model")
            print(f"  {config.id:18} NOT SET - pass {flag}, or --list-models "
                  f"to see the options")

    print("\n=== agent tooling ===")
    for agent in sorted({c.agent for c in configs}):
        found, detail = _agent_available(agent)
        if not found:
            ok = False
        print(f"  {agent:12} {'ok' if found else 'MISSING'}  {detail}")

    print("\n=== credentials (presence only; values are never read out) ===")
    for env in sorted({c.key_env for c in configs}):
        from_env = bool(os.environ.get(env))
        value = resolve_secret(env)
        if not value:
            ok = False
            source = "NOT AVAILABLE"
        else:
            source = ("environment" if from_env
                      else f"1Password ({SECRET_REFS.get(env, '?')})")
        print(f"  {env:20} {source}")

    if check_models:
        print("\n=== pinned model snapshots ===")
        for config in configs:
            if not config.model:
                print(f"  {config.id:30} skipped (no model selected)")
                continue
            if not resolve_secret(config.key_env):
                print(f"  {config.model:30} skipped "
                      f"({config.key_env} unavailable)")
                continue
            reachable, detail = _model_reachable(config)
            if not reachable:
                ok = False
            print(f"  {config.model:30} "
                  f"{'ok' if reachable else 'UNAVAILABLE'}  {detail}")

    print("\n=== docker (agents run their tools in containers) ===")
    docker_ok = _have("docker") and subprocess.run(
        ["docker", "info"], capture_output=True).returncode == 0
    if not docker_ok:
        ok = False
    print(f"  docker daemon  {'ok' if docker_ok else 'NOT RUNNING'}")

    print("\n" + ("PREFLIGHT PASSED" if ok else "PREFLIGHT FAILED"))
    return ok


# --------------------------------------------------------------------------- #
# One run
# --------------------------------------------------------------------------- #

def seed_workdir(config: Config, run_id: str) -> Path:
    """A clean directory holding only the skeleton and the specification."""
    work = WORK_DIR / run_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    deps = ", ".join(f'"{d}"' for d in SKELETON_DEPS)
    (work / "pyproject.toml").write_text(
        "[project]\n"
        f'name = "{config.pair}framework"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = [{deps}]\n")
    shutil.copy(SPEC_DIR / f"{config.spec}.md", work / "SPECIFICATION.md")
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    # An initial commit is required, not cosmetic: SWE-agent's environment
    # setup runs `git reset --hard HEAD && git clean -fdq` before starting, and
    # fails with "Failed to clean repository" if the repo has no HEAD yet.
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    subprocess.run(["git", "-c", "user.email=oracle@local",
                    "-c", "user.name=generation harness",
                    "commit", "-q", "-m", "Skeleton and specification"],
                   cwd=work, check=True)
    return work


#: Answer supplied on stdin when an agent asks the user to continue. Repeated
#: because an agent may ask more than once in a run.
AGENT_STDIN = {"openhands": "/exit\n" * 200}


def agent_command(config: Config, work: Path, trace: Path) -> list[str]:
    """The agent invocation carrying the study's budget and selected model.

    No credential appears here. Both agents receive it through the subprocess
    environment, so it cannot show up in a process listing.
    """
    spec_path = SPEC_DIR / f"{config.spec}.md"
    _, binary = _agent_available(config.agent)

    if config.agent == "swe-agent":
        return [
            str(SWE_PY), str(SWE_ENTRY), "run",
            "--config", str(SWE_SRC / "config" / "default.yaml"),
            "--agent.model.name", config.model,
            "--agent.model.temperature", str(TEMPERATURE),
            "--agent.model.per_instance_call_limit", str(TOOL_CALL_BUDGET),
            "--agent.model.per_instance_cost_limit", str(PER_RUN_COST_LIMIT_USD),
            "--env.repo.path", str(work),
            f"--problem_statement.path={spec_path}",
            "--output_dir", str(trace),
        ]

    # OpenHands 0.14.0, headless, from its pinned image. It spawns its own
    # sandbox container, hence the docker socket mount.
    #
    # `-i` is required, not optional. When the agent decides it is done it
    # moves to AWAITING_USER_INPUT and calls input(); `exit_on_message` would
    # make it send "/exit" itself, but 0.14.0 hardcodes that to False and
    # exposes no flag for it. Without an open stdin the input() raises
    # EOFError inside a task whose exception is never retrieved, so the
    # process hangs until the wall-clock limit kills it -- the work is
    # finished, but 80 minutes of budget are burned per run. With stdin open
    # the harness answers "/exit", which is exactly what exit_on_message
    # would have sent.
    return [
        "docker", "run", "--rm", "-i",
        "-e", f"LLM_MODEL={config.model}",
        # Name only, no value: `-e NAME` makes docker inherit it from this
        # process's environment. Passing `-e NAME=value` would put the
        # credential in the container's argv, where it is readable by any
        # local process via `ps`.
        "-e", "LLM_API_KEY",
        "-e", f"LLM_TEMPERATURE={TEMPERATURE}",
        "-e", f"MAX_ITERATIONS={TOOL_CALL_BUDGET}",
        "-e", f"SANDBOX_RUNTIME_CONTAINER_IMAGE={OPENHANDS_RUNTIME_IMAGE}",
        "-e", f"WORKSPACE_MOUNT_PATH={work}",
        "-e", "SANDBOX_USER_ID=0",
        "-e", "LOG_ALL_EVENTS=true",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", f"{work}:/opt/workspace_base",
        "-v", f"{trace}:/opt/trace",
        OPENHANDS_IMAGE,
        "python", "-m", "openhands.core.main",
        # seed_workdir() copies the spec in as SPECIFICATION.md.
        "-f", "/opt/workspace_base/SPECIFICATION.md",
        "-i", str(TOOL_CALL_BUDGET),
        "-b", str(PER_RUN_COST_LIMIT_USD),
    ]


def recover_patch(config: Config, work: Path, trace: Path) -> str:
    """Apply an agent's produced patch to the working tree, if it made one.

    SWE-agent copies the repository into a container and never writes back to
    ``--env.repo.path``; the result of a run is a patch emitted into
    ``--output_dir``. Without this step the frozen subject would contain only
    the skeleton, and the run would look like an agent that wrote nothing.

    OpenHands edits its mounted workspace directly, so this is a no-op there.
    """
    if config.agent != "swe-agent":
        return ""

    candidates = sorted(trace.rglob("*.patch"))
    patch_text = ""
    source = ""
    for candidate in candidates:
        text = candidate.read_text(errors="replace")
        if text.strip():
            patch_text, source = text, candidate.name
            break
    if not patch_text:
        # Fall back to the trajectory's recorded submission.
        for traj in sorted(trace.rglob("*.traj")):
            try:
                data = json.loads(traj.read_text())
            except (ValueError, OSError):
                continue
            submission = (data.get("info") or {}).get("submission")
            if submission and submission.strip():
                patch_text, source = submission, traj.name
                break
    if not patch_text:
        return ""

    patch_text, dropped = _strip_unapplyable(patch_text)

    applied = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"],
                             cwd=work, input=patch_text,
                             capture_output=True, text=True)
    if applied.returncode != 0:
        applied = subprocess.run(["git", "apply", "-3", "--whitespace=nowarn", "-"],
                                 cwd=work, input=patch_text,
                                 capture_output=True, text=True)
    note = f"applied patch from {source}"
    if dropped:
        note += f"; dropped {len(dropped)} build-artifact path(s)"
    if applied.returncode != 0:
        return (f"patch from {source} did not apply: "
                f"{applied.stderr.strip()[:400]}")
    return note


#: Paths an agent may have committed that are build output, not source. They
#: are excluded from the frozen subject so the measured repository is the code
#: the agent wrote, and because a binary .pyc diff without a full index line
#: cannot be applied by `git apply` at all and would fail the whole patch.
_ARTIFACT_MARKERS = ("__pycache__/", ".pyc", ".pyo", ".egg-info/",
                     ".pytest_cache/")


def _strip_unapplyable(patch_text: str) -> tuple[str, list[str]]:
    """Drop per-file diffs for build artifacts. Returns (patch, dropped paths)."""
    lines = patch_text.splitlines(keepends=True)
    out: list[str] = []
    dropped: list[str] = []
    keep = True
    for line in lines:
        if line.startswith("diff --git "):
            path = line.split(" b/", 1)[-1].strip() if " b/" in line else line
            keep = not any(marker in path for marker in _ARTIFACT_MARKERS)
            if not keep:
                dropped.append(path)
        if keep:
            out.append(line)
    return "".join(out), dropped


def freeze(work: Path, run_id: str) -> tuple[str, int]:
    """Commit the final tree and copy it under subjects/. Returns (sha, files)."""
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    committed = subprocess.run(
        ["git", "commit", "-q", "-m", f"Agentic generation run {run_id}"],
        cwd=work, capture_output=True)
    sha = ""
    if committed.returncode == 0 or b"nothing to commit" not in committed.stdout:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=work,
                             capture_output=True, text=True).stdout.strip()
    files = len([p for p in work.rglob("*.py") if ".git" not in p.parts])

    destination = SUBJECTS_DIR / run_id
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(work, destination,
                    ignore=shutil.ignore_patterns(".git"))
    return sha, files


def execute(config: Config, n: int, dry_run: bool) -> RunResult:
    run_id = config.run_id(n)
    result = RunResult(run_id=run_id, config=config.id, agent=config.agent,
                       model=config.model, spec=config.spec)
    trace = RUN_DIR / run_id
    result.trace_path = str(trace.relative_to(REPO_ROOT))

    if dry_run:
        result.exit_status = "dry-run"
        result.note = (f"would run {config.agent} on {config.model} with the "
                       f"{config.spec} spec, {TIME_LIMIT_S // 60} min / "
                       f"{TOOL_CALL_BUDGET} calls / temp {TEMPERATURE}")
        return result

    available, detail = _agent_available(config.agent)
    if not available:
        result.exit_status = "blocked"
        result.note = f"{config.agent} {detail}"
        return result
    secret = resolve_secret(config.key_env)
    if not secret:
        result.exit_status = "blocked"
        result.note = (f"no credential for {config.key_env} (not in the "
                       f"environment and not readable from 1Password)")
        return result
    if not config.model:
        result.exit_status = "blocked"
        result.note = f"no model selected for {config.id}"
        return result

    work = seed_workdir(config, run_id)
    trace.mkdir(parents=True, exist_ok=True)
    command = agent_command(config, work, trace)
    env = dict(os.environ)
    env[config.key_env] = secret
    # OpenHands reads LLM_API_KEY; docker inherits it by name (see
    # agent_command) so it never reaches any command line.
    env["LLM_API_KEY"] = secret
    env["LITELLM_LOG"] = "ERROR"

    print(f"  [{run_id}] starting {config.agent} / {config.model}")
    result.started_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    started = time.monotonic()
    try:
        completed = subprocess.run(command, timeout=TIME_LIMIT_S,
                                   capture_output=True, text=True, env=env,
                                   input=AGENT_STDIN.get(config.agent))
        result.exit_status = "ok" if completed.returncode == 0 else "agent-error"
        if completed.returncode != 0:
            result.note = (completed.stderr or completed.stdout)[-1500:]
        (trace / "stdout.log").write_text(completed.stdout or "")
        (trace / "stderr.log").write_text(completed.stderr or "")
    except subprocess.TimeoutExpired:
        # Hitting the wall-clock cap is a study outcome, not a failure: the
        # tree is frozen as it stands, exactly as the budget intends.
        result.exit_status = "timeout"
        result.note = f"reached the {TIME_LIMIT_S // 60}-minute limit"
    except Exception as exc:                              # noqa: BLE001
        result.exit_status = "harness-error"
        result.note = f"{type(exc).__name__}: {exc}"

    result.wall_seconds = round(time.monotonic() - started, 1)
    result.finished_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result.tool_calls = count_tool_calls(trace)
    recovery = recover_patch(config, work, trace)
    if recovery:
        result.extra["patch_recovery"] = recovery
    # A run is only frozen if the agent actually wrote Python. An immediate
    # crash would otherwise register an empty directory as a study subject and
    # it would be scored as though the agent had produced nothing on purpose.
    produced = [p for p in work.rglob("*.py") if ".git" not in p.parts]
    result.extra["py_files_written"] = len(produced)
    if result.exit_status in ("ok", "timeout") or produced:
        if produced:
            result.commit, result.files_written = freeze(work, run_id)
        else:
            result.note = (result.note or "") + " | not frozen: no .py written"
    
    print(f"  [{run_id}] {result.exit_status} in {result.wall_seconds:.0f}s, "
          f"{result.files_written} python files, "
          f"tool calls: {result.tool_calls if result.tool_calls is not None else 'unknown'}")
    return result


def count_tool_calls(trace: Path) -> int | None:
    """Tool-call count from the agent's own trace, if it records one.

    Both agents write a trajectory; the key differs by agent and version, so
    several shapes are tried and None is returned rather than a guess.
    """
    for path in sorted(trace.rglob("*.json")) + sorted(trace.rglob("*.jsonl")):
        try:
            text = path.read_text()
        except OSError:
            continue
        if path.suffix == ".jsonl":
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if lines:
                return len(lines)
            continue
        try:
            data = json.loads(text)
        except ValueError:
            continue
        for key in ("trajectory", "history", "steps", "actions"):
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, list) and value:
                return len(value)
    return None


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

def register(results: list[RunResult]) -> None:
    """Add every frozen run to subjects.json so the analysis stages pick it up."""
    registry_path = SUBJECTS_DIR / "subjects.json"
    registry = json.loads(registry_path.read_text())
    by_id = {s["id"]: s for s in registry["subjects"]}
    configs = {c.id: c for c in CONFIGS}

    added = 0
    for result in results:
        if not result.commit:
            continue
        config = configs[result.config]
        entry = {
            "id": result.run_id,
            "label": f"{config.label} r{result.run_id[-2:]}",
            "kind": "agentic",
            "pair": config.pair,
            "path": f"subjects/{result.run_id}",
            "snapshot": f"{config.agent} + {config.model} @ {result.commit[:12]}",
            "oracle": config.pair,
            "available": True,
        }
        # Scope the subject to the package the agent built, matching how the
        # human baselines are scoped (src/flask/; django/urls/ + views/).
        # Without this, example scripts and scratch files at the repository
        # root would be measured for the agentic subjects but not for the
        # baselines, which would make the comparison unfair in the agents'
        # disfavour.
        root = SUBJECTS_DIR / result.run_id
        # Shallowest package dirs whose parent is not itself a package. Agents
        # do not always put the package at the repository root: OpenHands
        # tends to create a project directory containing it
        # (<root>/proj/proj/__init__.py), so a direct-children-only search
        # finds nothing and the subject ends up unscoped and unimportable.
        packages = sorted(
            {str(q.parent.relative_to(root))
             for q in root.rglob("__init__.py")
             if ".git" not in q.parts
             and not (q.parent.parent / "__init__.py").exists()},
            key=lambda rel: (len(pathlib.PurePath(rel).parts), rel))
        if packages:
            entry["include"] = packages[:1]
        if result.run_id in by_id:
            by_id[result.run_id].update(entry)
        else:
            registry["subjects"].append(entry)
            added += 1
    registry_path.write_text(json.dumps(registry, indent=2) + "\n")
    print(f"[registry] {added} new subject(s) registered, "
          f"{len(results)} run(s) considered")


def write_manifest(results: list[RunResult]) -> Path:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    path = RUN_DIR / "MANIFEST.json"
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "budget": {
            "wall_clock_seconds": TIME_LIMIT_S,
            "tool_calls": TOOL_CALL_BUDGET,
            "temperature": TEMPERATURE,
            "per_run_cost_limit_usd": PER_RUN_COST_LIMIT_USD,
            "runs_per_config": RUNS_PER_CONFIG,
            "concurrency": (results[0].extra.get("concurrency", 1)
                            if results else 1),
        },
        "configurations": [asdict(c) for c in CONFIGS],
        "runs": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=[c.id for c in CONFIGS],
                        action="append",
                        help="limit to one configuration (repeatable)")
    parser.add_argument("--runs", type=int, default=RUNS_PER_CONFIG,
                        help=f"last run index per configuration "
                             f"(default {RUNS_PER_CONFIG})")
    parser.add_argument("--from-run", type=int, default=1, metavar="N",
                        help="first run index, so completed runs are not "
                             "redone and overwritten (default 1)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan; no API calls, no cost")
    parser.add_argument("--preflight", action="store_true",
                        help="check tooling, credentials and models, then stop")
    parser.add_argument("--skip-model-check", action="store_true",
                        help="preflight without contacting the providers")
    parser.add_argument("--anthropic-model", default=DEFAULT_ANTHROPIC_MODEL,
                        help=f"model for the SWE-agent configurations "
                             f"(default {DEFAULT_ANTHROPIC_MODEL})")
    parser.add_argument("--openai-model", default=DEFAULT_OPENAI_MODEL,
                        help="model for the OpenHands configuration (required: "
                             "run --list-models to see what the account serves)")
    parser.add_argument("--study-models", "--manuscript-models", action="store_true",
                        help="use the identifiers this study requested, if "
                             "the providers still serve them")
    parser.add_argument("--list-models", action="store_true",
                        help="print the models each provider will serve, then stop")
    parser.add_argument("--parallel", type=int, default=1, metavar="N",
                        help="run N generations concurrently (default 1). See "
                             "the note in generation/README.md: the 90-minute "
                             "cap is wall clock, so concurrency is a study "
                             "variable, not just a speed-up.")
    args = parser.parse_args()

    if args.list_models:
        return list_models()

    configs = [c for c in CONFIGS
               if not args.config or c.id in args.config]

    # Model selection, applied before preflight so it is validated.
    for config in configs:
        if args.study_models:
            config.model = STUDY_MODELS[config.key_env]
        elif config.key_env == "OPENROUTER_API_KEY":
            config.model = args.anthropic_model
        else:
            config.model = args.openai_model

    if args.parallel < 1:
        print("--parallel must be at least 1", file=sys.stderr)
        return 2

    if args.preflight:
        return 0 if preflight(configs, not args.skip_model_check) else 1

    if not args.dry_run and not preflight(configs, not args.skip_model_check):
        print("\nRefusing to start: fix the items marked above first.",
              file=sys.stderr)
        return 1

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [(config, n) for config in configs
            for n in range(args.from_run, args.runs + 1)]
    total = len(jobs)
    concurrency = min(args.parallel, total)

    print(f"\n{total} run(s): {len(configs)} configuration(s) x runs "
          f"{args.from_run}-{args.runs}")
    for config in configs:
        print(f"  {config.id:18} {config.agent} / {config.model} "
              f"/ {config.spec} spec")
    if concurrency > 1:
        print(f"\nRunning {concurrency} at a time. Note for the manuscript: "
              f"the budget is 90 minutes of WALL CLOCK, so concurrent runs "
              f"compete for CPU, Docker and the provider's rate limit, and a "
              f"contended run can reach the cap having done less work than an "
              f"uncontended one. Concurrency is recorded in the manifest "
              f"because it is part of the experimental condition.")

    results: list[RunResult] = []
    if concurrency == 1:
        for config, n in jobs:
            results.append(execute(config, n, args.dry_run))
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(execute, config, n, args.dry_run)
                       for config, n in jobs]
            for future in futures:
                results.append(future.result())
    for result in results:
        result.extra["concurrency"] = concurrency

    manifest = write_manifest(results)
    print(f"\n[manifest] {manifest.relative_to(REPO_ROOT)}")
    if not args.dry_run:
        register(results)
        print("\nNext: make all        # scores every registered subject")
        print("      make significance")

    frozen = sum(1 for r in results if r.commit)
    blocked = [r for r in results if r.exit_status == "blocked"]
    if blocked:
        print(f"\n{len(blocked)} run(s) blocked: {blocked[0].note}")
    print(f"{frozen}/{len(results)} run(s) frozen into subjects/")
    return 0 if (args.dry_run or frozen) else 1


if __name__ == "__main__":
    sys.exit(main())
