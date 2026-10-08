"""Request Object — oracle cases for the Django-pair specification.

Each test routes one pattern to a view that reads one documented request
attribute and echoes it, then asserts on the WSGI response body.
"""

from __future__ import annotations

import json

import pytest

import wsgi


def _echo(response_class, fn):
    def view(request, **params):
        return response_class(str(fn(request, **params)))
    return view


# --- Method ---------------------------------------------------------------- #

@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
def test_request_exposes_method(api, serve, pattern, response_class, method):
    patterns = [pattern("m/", _echo(response_class, lambda r, **_: api.method(r)))]
    assert method.encode() in serve(patterns, method, "/m/").body


def test_request_method_is_upper_case(api, serve, pattern, response_class):
    patterns = [pattern("m/", _echo(response_class, lambda r, **_: api.method(r)))]
    assert serve(patterns, "GET", "/m/").text.strip().isupper()


# --- Path ------------------------------------------------------------------ #

def test_request_exposes_path(api, serve, pattern, response_class):
    patterns = [pattern("where/", _echo(response_class, lambda r, **_: api.path(r)))]
    assert b"/where/" in serve(patterns, "GET", "/where/").body


def test_request_path_excludes_query_string(api, serve, pattern, response_class):
    patterns = [pattern("nq/", _echo(response_class, lambda r, **_: api.path(r)))]
    body = serve(patterns, "GET", "/nq/", query={"x": "1"}).text
    assert "/nq/" in body and "x=1" not in body


def test_request_path_for_nested_route(api, serve, pattern, response_class):
    patterns = [pattern("a/b/c/", _echo(response_class, lambda r, **_: api.path(r)))]
    assert b"/a/b/c/" in serve(patterns, "GET", "/a/b/c/").body


# --- Query string ---------------------------------------------------------- #

def test_request_query_parameter(api, serve, pattern, response_class):
    fn = lambda r, **_: api.query_get(r, "x")     # noqa: E731
    patterns = [pattern("q/", _echo(response_class, fn))]
    assert b"hello" in serve(patterns, "GET", "/q/", query={"x": "hello"}).body


def test_request_missing_query_parameter_default(api, serve, pattern, response_class):
    fn = lambda r, **_: api.query_get(r, "x", "MISSING")  # noqa: E731
    patterns = [pattern("q/", _echo(response_class, fn))]
    assert b"MISSING" in serve(patterns, "GET", "/q/").body


@pytest.mark.parametrize("value", ["a", "b b", "1+1", "sp ace"])
def test_request_query_parameter_values(api, serve, pattern, response_class, value):
    fn = lambda r, **_: api.query_get(r, "x")     # noqa: E731
    patterns = [pattern("q/", _echo(response_class, fn))]
    assert value in serve(patterns, "GET", "/q/", query={"x": value}).text


def test_request_multiple_query_parameters(api, serve, pattern, response_class):
    fn = lambda r, **_: f"{api.query_get(r,'a')},{api.query_get(r,'b')}"  # noqa: E731
    patterns = [pattern("q/", _echo(response_class, fn))]
    result = serve(patterns, "GET", "/q/", query={"a": "1", "b": "2"})
    assert b"1,2" in result.body


# --- Headers --------------------------------------------------------------- #

def test_request_custom_header(api, serve, pattern, response_class):
    fn = lambda r, **_: api.header(r, "X-Test")       # noqa: E731
    patterns = [pattern("h/", _echo(response_class, fn))]
    result = serve(patterns, "GET", "/h/", headers={"X-Test": "yes"})
    assert b"yes" in result.body


def test_request_header_read_case_insensitively(api, serve, pattern, response_class):
    fn = lambda r, **_: api.header(r, "x-test")       # noqa: E731
    patterns = [pattern("h/", _echo(response_class, fn))]
    result = serve(patterns, "GET", "/h/", headers={"X-Test": "mixed"})
    assert b"mixed" in result.body


def test_request_missing_header_default(api, serve, pattern, response_class):
    fn = lambda r, **_: api.header(r, "X-Absent", "NONE")   # noqa: E731
    patterns = [pattern("h/", _echo(response_class, fn))]
    assert b"NONE" in serve(patterns, "GET", "/h/").body


def test_request_content_type_header(api, serve, pattern, response_class):
    fn = lambda r, **_: api.header(r, "Content-Type")       # noqa: E731
    patterns = [pattern("ct/", _echo(response_class, fn))]
    body, ctype = wsgi.json_body({"a": 1})
    result = serve(patterns, "POST", "/ct/", body=body, content_type=ctype)
    assert b"application/json" in result.body


# --- Body ------------------------------------------------------------------ #

def test_request_body_bytes(api, serve, pattern, response_class):
    fn = lambda r, **_: len(api.body_bytes(r))     # noqa: E731
    patterns = [pattern("b/", _echo(response_class, fn))]
    assert b"5" in serve(patterns, "POST", "/b/", body=b"12345").body


def test_request_body_content(api, serve, pattern, response_class):
    fn = lambda r, **_: api.body_bytes(r).decode() # noqa: E731
    patterns = [pattern("b/", _echo(response_class, fn))]
    assert b"payload" in serve(patterns, "POST", "/b/", body=b"payload").body


def test_request_empty_body(api, serve, pattern, response_class):
    fn = lambda r, **_: len(api.body_bytes(r))     # noqa: E731
    patterns = [pattern("b/", _echo(response_class, fn))]
    assert b"0" in serve(patterns, "POST", "/b/", body=b"").body


def test_request_json_body_is_readable(api, serve, pattern, response_class):
    fn = lambda r, **_: json.loads(api.body_bytes(r).decode())["k"]  # noqa: E731
    patterns = [pattern("j/", _echo(response_class, fn))]
    body, ctype = wsgi.json_body({"k": "v"})
    result = serve(patterns, "POST", "/j/", body=body, content_type=ctype)
    assert b"v" in result.body


# --- Captured URL parameters reach the view -------------------------------- #

def test_captured_parameters_passed_to_the_view(api, serve, pattern, response_class):
    fn = lambda r, **params: params.get("name", "")   # noqa: E731
    patterns = [pattern("u/<str:name>/", _echo(response_class, fn))]
    assert b"zoe" in serve(patterns, "GET", "/u/zoe/").body


def test_captured_int_parameter_is_an_int(api, serve, pattern, response_class):
    fn = lambda r, **params: type(params["pk"]).__name__   # noqa: E731
    patterns = [pattern("p/<int:pk>/", _echo(response_class, fn))]
    assert b"int" in serve(patterns, "GET", "/p/7/").body
