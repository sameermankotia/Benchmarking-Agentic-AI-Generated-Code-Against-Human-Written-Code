"""Flask-pair oracle fixtures.

Builds the system-under-test through the canonical ``sut`` handle so the same
suite runs against Flask, the SWE-agent framework, and the OpenHands framework.
Tests assert on behaviour documented in the specification (paper §3.2.3), not on
implementation-specific internals.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def fw(sut_module):
    """The framework module under test."""
    return sut_module


@pytest.fixture
def app(sut_module):
    app = sut_module.Flask(__name__)
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()
