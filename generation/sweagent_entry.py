"""Entry point for SWE-agent that registers this study's models first.

SWE-agent 1.0.0 looks a model's provider up in litellm's bundled cost map and
raises a bare ``KeyError`` if it is absent, before any request is made. The
litellm it ships with knows no ``openrouter/*`` models at all, so the models
this study uses have to be registered before SWE-agent's CLI starts.

Doing it from a ``sitecustomize.py`` does not work: at interpreter start-up
litellm is not importable yet, the failure is silent, and the agent then dies
on the KeyError anyway. So the registration happens here instead, immediately
before handing control to SWE-agent's own ``main``, and every argument is
passed through untouched.

Invoked as:
    .venv-sweagent/bin/python generation/sweagent_entry.py run --config ...
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import litellm_model_shim                                  # noqa: E402

registered = litellm_model_shim.install()
if registered:
    print(f"[sweagent_entry] registered with litellm: "
          f"{', '.join(registered)}", file=sys.stderr)

from sweagent.run.run import main                          # noqa: E402

if __name__ == "__main__":
    main()
