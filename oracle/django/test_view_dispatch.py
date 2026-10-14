"""View Dispatch — oracle cases for the Django-pair specification.

Dispatch is observed through the WSGI response: which view ran, what it
received, and what the framework returns when no view accepts the request.
"""

from __future__ import annotations

import pytest


# --- Basic: the right view runs -------------------------------------------- #

def test_view_is_called_for_its_pattern(serve, pattern, response_class):
    calls = {"n": 0}

    def view(request, **_):
        calls["n"] += 1
        return response_class("called")
    serve([pattern("v/", view)], "GET", "/v/")
    assert calls["n"] == 1


def test_view_not_called_for_other_paths(serve, pattern, response_class):
    calls = {"n": 0}

    def view(request, **_):
        calls["n"] += 1
        return response_class("called")
    serve([pattern("v/", view)], "GET", "/other/")
    assert calls["n"] == 0


def test_correct_view_among_several(serve, pattern, response_class):
    def first(request, **_):
        return response_class("first")

    def second(request, **_):
        return response_class("second")

    def third(request, **_):
        return response_class("third")
    patterns = [pattern("a/", first), pattern("b/", second),
                pattern("c/", third)]
    assert b"second" in serve(patterns, "GET", "/b/").body


def test_view_receives_the_request(api, serve, pattern, response_class):
    def view(request, **_):
        return response_class(api.path(request))
    assert b"/v/" in serve([pattern("v/", view)], "GET", "/v/").body


def test_view_receives_captured_parameters(serve, pattern, response_class):
    seen = {}

    def view(request, **params):
        seen.update(params)
        return response_class("ok")
    serve([pattern("u/<str:name>/<int:pk>/", view)], "GET", "/u/zoe/7/")
    assert seen == {"name": "zoe", "pk": 7}


def test_view_return_value_becomes_the_response(serve, pattern, response_class):
    def view(request, **_):
        return response_class("returned", status=201)
    result = serve([pattern("v/", view)], "GET", "/v/")
    assert result.status_code == 201 and b"returned" in result.body


# --- Behavioural: methods reach the same view ------------------------------ #

@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_function_view_receives_any_method(api, serve, pattern,
                                           response_class, method):
    def view(request, **_):
        return response_class(api.method(request))
    assert method.encode() in serve([pattern("v/", view)], method, "/v/").body


def test_view_can_branch_on_method(api, serve, pattern, response_class):
    def view(request, **_):
        if api.method(request) == "POST":
            return response_class("wrote", status=201)
        return response_class("read")
    patterns = [pattern("v/", view)]
    assert b"read" in serve(patterns, "GET", "/v/").body
    created = serve(patterns, "POST", "/v/")
    assert created.status_code == 201 and b"wrote" in created.body


def test_view_can_reject_a_method(api, serve, pattern, response_class):
    def view(request, **_):
        if api.method(request) != "GET":
            return response_class("", status=405)
        return response_class("ok")
    patterns = [pattern("v/", view)]
    assert serve(patterns, "GET", "/v/").status_code == 200
    assert serve(patterns, "POST", "/v/").status_code == 405


# --- Behavioural: dispatch failures ---------------------------------------- #

def test_no_matching_pattern_is_404(serve, pattern, response_class):
    def view(request, **_):
        return response_class("ok")
    assert serve([pattern("v/", view)], "GET", "/nope/").status_code == 404


def test_view_raising_is_not_a_200(serve, pattern, response_class):
    def view(request, **_):
        raise RuntimeError("boom")
    result = serve([pattern("v/", view)], "GET", "/v/")
    assert result.status_code != 200 or result.exc is not None


def test_view_returning_an_error_status(serve, pattern, response_class):
    def view(request, **_):
        return response_class("bad", status=400)
    assert serve([pattern("v/", view)], "GET", "/v/").status_code == 400


# --- Behavioural: dispatch is per-request ---------------------------------- #

def test_each_request_dispatches_once(serve, pattern, response_class):
    calls = {"n": 0}

    def view(request, **_):
        calls["n"] += 1
        return response_class("ok")
    patterns = [pattern("v/", view)]
    for _ in range(4):
        serve(patterns, "GET", "/v/")
    assert calls["n"] == 4


def test_views_do_not_share_state_implicitly(serve, pattern, response_class):
    def view(request, **_):
        local = []
        local.append("x")
        return response_class(str(len(local)))
    patterns = [pattern("v/", view)]
    assert serve(patterns, "GET", "/v/").body == b"1"
    assert serve(patterns, "GET", "/v/").body == b"1"


def test_captured_parameters_are_per_request(serve, pattern, response_class):
    def view(request, **params):
        return response_class(params.get("name", ""))
    patterns = [pattern("u/<str:name>/", view)]
    assert b"one" in serve(patterns, "GET", "/u/one/").body
    assert b"two" in serve(patterns, "GET", "/u/two/").body


def test_dispatch_to_nested_path(serve, pattern, response_class):
    def view(request, **_):
        return response_class("deep")
    assert b"deep" in serve([pattern("a/b/c/", view)], "GET", "/a/b/c/").body


# --- Edge cases ------------------------------------------------------------ #

def test_query_string_reaches_the_view_not_the_resolver(api, serve, pattern,
                                                        response_class):
    def view(request, **_):
        return response_class(api.query_get(request, "x", "none"))
    result = serve([pattern("v/", view)], "GET", "/v/", query={"x": "val"})
    assert b"val" in result.body


def test_two_patterns_to_the_same_view(serve, pattern, response_class):
    calls = {"n": 0}

    def view(request, **_):
        calls["n"] += 1
        return response_class("shared")
    patterns = [pattern("one/", view), pattern("two/", view)]
    serve(patterns, "GET", "/one/")
    serve(patterns, "GET", "/two/")
    assert calls["n"] == 2


def test_dispatch_with_an_empty_body_post(api, serve, pattern, response_class):
    def view(request, **_):
        return response_class(f"{api.method(request)}:{len(api.body_bytes(request))}")
    result = serve([pattern("v/", view)], "POST", "/v/", body=b"")
    assert b"POST:0" in result.body
