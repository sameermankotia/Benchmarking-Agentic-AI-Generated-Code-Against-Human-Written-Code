"""Register the OpenRouter-routed models SWE-agent needs with litellm.

SWE-agent 1.0.0 resolves a model's provider by indexing litellm's bundled cost
map::

    self.lm_provider = litellm.model_cost[self.config.name]["litellm_provider"]

so any model missing from that map fails at construction with a bare
``KeyError`` before a single request is made. The litellm bundled with
SWE-agent 1.0.0 (1.105.0) contains **no** ``openrouter/*`` entries at all, and
has also aged ``claude-sonnet-4`` out of its Anthropic entries, so the model
this study uses is unknown to it twice over.

This module adds the needed entries. It is imported at interpreter start-up by
a ``sitecustomize.py`` placed in the SWE-agent virtualenv, so it applies to the
agent subprocess without patching SWE-agent's own source.

The prices are the published rates for the models concerned and are not
cosmetic: SWE-agent's ``--agent.model.per_instance_cost_limit`` is evaluated
against them, so a wrong number would silently disable the spend guard.
"""

from __future__ import annotations

#: model id -> cost-map entry. Prices are USD per token.
MODELS: dict[str, dict] = {
    # Claude Sonnet 4: $3 / 1M input, $15 / 1M output.
    "openrouter/anthropic/claude-sonnet-4": {
        "litellm_provider": "openrouter",
        "mode": "chat",
        "input_cost_per_token": 3e-06,
        "output_cost_per_token": 1.5e-05,
        "max_tokens": 64000,
        "max_input_tokens": 200000,
        "max_output_tokens": 64000,
        "supports_function_calling": True,
        "supports_vision": True,
    },
    # Current Sonnet, for runs that choose it instead.
    "openrouter/anthropic/claude-sonnet-5.5": {
        "litellm_provider": "openrouter",
        "mode": "chat",
        "input_cost_per_token": 2e-06,
        "output_cost_per_token": 1e-05,
        "max_tokens": 64000,
        "max_input_tokens": 200000,
        "max_output_tokens": 64000,
        "supports_function_calling": True,
        "supports_vision": True,
    },
    "openrouter/anthropic/claude-opus-5.5": {
        "litellm_provider": "openrouter",
        "mode": "chat",
        "input_cost_per_token": 4e-06,
        "output_cost_per_token": 2e-05,
        "max_tokens": 64000,
        "max_input_tokens": 200000,
        "max_output_tokens": 64000,
        "supports_function_calling": True,
        "supports_vision": True,
    },
}


def install() -> list[str]:
    """Add every entry litellm is missing. Returns the ids registered."""
    try:
        import litellm
    except ImportError:
        return []

    added = []
    for model_id, entry in MODELS.items():
        if model_id not in litellm.model_cost:
            litellm.model_cost[model_id] = dict(entry)
            added.append(model_id)
    # Keep litellm's own registry in step, so cost accounting sees it too.
    try:
        litellm.register_model({mid: dict(e) for mid, e in MODELS.items()})
    except Exception:                                      # noqa: BLE001
        pass
    return added


if __name__ == "__main__":
    print("registered:", install() or "(nothing missing)")
