"""Request Handling — oracle cases for specification area (2).

"request object encapsulating method, path, headers, query string, and body."

Each test registers a view that reads one documented request attribute through
the resolved accessor (`api.method`, `api.path`, `api.header`, `api.query_get`,
`api.body_bytes`) and echoes it, then asserts on the WSGI response body. No
assertion names an implementation's attribute directly.
"""

from __future__ import annotations

import json

import pytest

import wsgi


@pytest.fixture
def report(api, route, app):
    """Register a view at `path` that echoes `fn(request)` as the body."""
    counter = {"n": 0}

    def _report(fn, path="/r", methods=None):
        counter["n"] += 1
        req = api.request

        def view(**_params):
            return str(fn(req))
        view.__name__ = f"view_{counter['n']}"
        route(path, methods)(view)
        return path
    return _report


# --- Method ---------------------------------------------------------------- #

@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
def test_request_exposes_method(api, app, report, method):
    path = report(api.method, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    assert method.encode() in wsgi.call(app, method, path).body


def test_request_method_is_upper_case(api, app, report):
    path = report(api.method)
    assert wsgi.call(app, "GET", path).text.strip().isupper()


# --- Path ------------------------------------------------------------------ #

def test_request_exposes_path(api, app, report):
    path = report(api.path, path="/where")
    assert b"/where" in wsgi.call(app, "GET", path).body


def test_request_path_excludes_query_string(api, app, report):
    path = report(api.path, path="/noquery")
    body = wsgi.call(app, "GET", path, query={"x": "1"}).text
    assert "/noquery" in body and "x=1" not in body


def test_request_path_for_nested_route(api, app, report):
    path = report(api.path, path="/a/b/c")
    assert b"/a/b/c" in wsgi.call(app, "GET", path).body


# --- Query string ---------------------------------------------------------- #

def test_request_query_parameter(api, app, report):
    path = report(lambda r: api.query_get(r, "x"))
    assert b"hello" in wsgi.call(app, "GET", path, query={"x": "hello"}).body


def test_request_missing_query_parameter_is_empty(api, app, report):
    path = report(lambda r: api.query_get(r, "x", "MISSING"))
    assert b"MISSING" in wsgi.call(app, "GET", path).body


@pytest.mark.parametrize("value", ["a", "b b", "1+1", "sp ace", "ü"])
def test_request_query_parameter_values(api, app, report, value):
    path = report(lambda r: api.query_get(r, "x"))
    assert value in wsgi.call(app, "GET", path, query={"x": value}).text


def test_request_multiple_query_parameters(api, app, report):
    path = report(lambda r: f"{api.query_get(r, 'a')},{api.query_get(r, 'b')}")
    body = wsgi.call(app, "GET", path, query={"a": "1", "b": "2"}).text
    assert "1,2" in body


def test_request_query_parameter_empty_value(api, app, report):
    path = report(lambda r: f"[{api.query_get(r, 'x')}]")
    assert "[]" in wsgi.call(app, "GET", path, query="x=").text


# --- Headers --------------------------------------------------------------- #

def test_request_custom_header(api, app, report):
    path = report(lambda r: api.header(r, "X-Test"))
    result = wsgi.call(app, "GET", path, headers={"X-Test": "yes"})
    assert b"yes" in result.body


def test_request_header_read_case_insensitively(api, app, report):
    path = report(lambda r: api.header(r, "x-test"))
    result = wsgi.call(app, "GET", path, headers={"X-Test": "mixed"})
    assert b"mixed" in result.body


def test_request_missing_header_default(api, app, report):
    path = report(lambda r: api.header(r, "X-Absent", "NONE"))
    assert b"NONE" in wsgi.call(app, "GET", path).body


def test_request_content_type_header(api, app, report):
    path = report(lambda r: api.header(r, "Content-Type"), methods=["POST"])
    body, ctype = wsgi.json_body({"a": 1})
    result = wsgi.call(app, "POST", path, body=body, content_type=ctype)
    assert b"application/json" in result.body


# --- Body ------------------------------------------------------------------ #

def test_request_body_bytes(api, app, report):
    path = report(lambda r: len(api.body_bytes(r)), methods=["POST"])
    assert b"5" in wsgi.call(app, "POST", path, body=b"12345").body


def test_request_body_content(api, app, report):
    path = report(lambda r: api.body_bytes(r).decode(), methods=["POST"])
    assert b"payload" in wsgi.call(app, "POST", path, body=b"payload").body


def test_request_empty_body(api, app, report):
    path = report(lambda r: len(api.body_bytes(r)), methods=["POST"])
    assert b"0" in wsgi.call(app, "POST", path, body=b"").body


def test_request_json_body_is_readable(api, app, report):
    def read_json(r):
        return json.loads(api.body_bytes(r).decode())["k"]
    path = report(read_json, methods=["POST"])
    body, ctype = wsgi.json_body({"k": "v"})
    result = wsgi.call(app, "POST", path, body=body, content_type=ctype)
    assert b"v" in result.body


def test_request_body_with_explicit_content_type(api, app, report):
    """A text body is delivered intact when its content type says so.

    A form-encoded body is deliberately not asserted on here: the
    specification names "body" but no form mapping, and an implementation is
    free to parse a form body out of the raw stream (Werkzeug does), so a raw
    assertion would test an unspecified choice.
    """
    path = report(lambda r: api.body_bytes(r).decode(), methods=["POST"])
    result = wsgi.call(app, "POST", path, body=b"plain text body",
                       content_type="text/plain")
    assert b"plain text body" in result.body


def test_request_body_not_consumed_by_routing(api, app, report):
    """The body is still readable inside the view after dispatch."""
    path = report(lambda r: api.body_bytes(r).decode() or "EMPTY",
                  methods=["POST"])
    assert b"intact" in wsgi.call(app, "POST", path, body=b"intact").body
