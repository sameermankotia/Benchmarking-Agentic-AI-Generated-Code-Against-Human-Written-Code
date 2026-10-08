"""Flask-pair oracle fixtures.

Subjects are constructed through the declared role surface (`api`) and then
driven over WSGI (`oracle/wsgi.py`), so the same suite runs against Flask, the
SWE-agent framework, and the OpenHands framework without naming any of them.
Tests assert on behaviour the specification fixes, never on implementation
internals.
"""

from __future__ import annotations

import pytest

import wsgi


@pytest.fixture
def app(api):
    """A fresh application instance for one test."""
    return api.app()


@pytest.fixture
def route(api, app):
    """Register a view on this test's application.

    Usage:
        @route("/path", methods=["GET"])
        def view(**params): ...
    """
    def _route(rule, methods=None):
        return api.route(app, rule, methods)
    return _route


@pytest.fixture
def get(app):
    """GET `path` on this test's application, over WSGI."""
    def _get(path="/", **kwargs):
        return wsgi.call(app, "GET", path, **kwargs)
    return _get


@pytest.fixture
def request_(app):
    """Call this test's application with any method, over WSGI."""
    def _call(method, path="/", **kwargs):
        return wsgi.call(app, method, path, **kwargs)
    return _call


@pytest.fixture
def echo(api):
    """Build a view body that reports request attributes as JSON.

    Only the attributes the specification names are reported: method, path,
    headers, query string, and body.
    """
    import json as _json

    def _echo(**extra):
        req = api.request

        def view(**_params):
            payload = {
                "method": req.method,
                "path": req.path,
            }
            payload.update({k: fn(req) for k, fn in extra.items()})
            return _json.dumps(payload)
        return view
    return _echo
