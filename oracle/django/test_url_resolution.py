"""URL Resolution — oracle cases for the Django-pair specification.

A URL resolves if and only if a request to it reaches the intended view, so
resolution is asserted through the WSGI response rather than through a
resolver API.
"""

from __future__ import annotations

import pytest


def _ok(response_class):
    def view(request, **params):
        body = "|".join(f"{k}={v}" for k, v in sorted(params.items())) or "ok"
        return response_class(body)
    return view


# --- Basic: static patterns ------------------------------------------------ #

def test_static_pattern_resolves(serve, pattern, response_class):
    result = serve([pattern("hello/", _ok(response_class))], path="/hello/")
    assert result.status_code == 200


def test_static_pattern_returns_view_body(serve, pattern, response_class):
    result = serve([pattern("ping/", _ok(response_class))], path="/ping/")
    assert b"ok" in result.body


def test_root_pattern_resolves(serve, pattern, response_class):
    result = serve([pattern("", _ok(response_class))], path="/")
    assert result.status_code == 200


def test_unmatched_path_is_404(serve, pattern, response_class):
    result = serve([pattern("exists/", _ok(response_class))], path="/missing/")
    assert result.status_code == 404


def test_two_patterns_resolve_independently(serve, pattern, response_class):
    def first(request, **_):
        return response_class("first")

    def second(request, **_):
        return response_class("second")
    patterns = [pattern("one/", first), pattern("two/", second)]
    assert b"first" in serve(patterns, path="/one/").body
    assert b"second" in serve(patterns, path="/two/").body


def test_nested_static_path_resolves(serve, pattern, response_class):
    result = serve([pattern("a/b/c/", _ok(response_class))], path="/a/b/c/")
    assert result.status_code == 200


# --- Behavioural: variable segments and converters ------------------------- #

@pytest.mark.parametrize("value", ["alice", "bob", "a-b_c"])
def test_string_converter_captures_value(serve, pattern, response_class, value):
    patterns = [pattern("user/<str:name>/", _ok(response_class))]
    result = serve(patterns, path=f"/user/{value}/")
    assert f"name={value}".encode() in result.body


@pytest.mark.parametrize("value,code", [("42", 200), ("abc", 404)])
def test_int_converter_matches_only_digits(serve, pattern, response_class,
                                           value, code):
    patterns = [pattern("post/<int:pk>/", _ok(response_class))]
    assert serve(patterns, path=f"/post/{value}/").status_code == code


def test_int_converter_captures_value(serve, pattern, response_class):
    patterns = [pattern("post/<int:pk>/", _ok(response_class))]
    assert b"pk=42" in serve(patterns, path="/post/42/").body


def test_slug_converter(serve, pattern, response_class):
    patterns = [pattern("entry/<slug:s>/", _ok(response_class))]
    assert b"s=my-post-1" in serve(patterns, path="/entry/my-post-1/").body


def test_path_converter_spans_slashes(serve, pattern, response_class):
    patterns = [pattern("files/<path:p>", _ok(response_class))]
    assert b"p=a/b/c.txt" in serve(patterns, path="/files/a/b/c.txt").body


def test_uuid_converter(serve, pattern, response_class):
    import uuid as _uuid
    value = str(_uuid.uuid4())
    patterns = [pattern("obj/<uuid:u>/", _ok(response_class))]
    assert value.encode() in serve(patterns, path=f"/obj/{value}/").body


def test_multiple_variable_segments(serve, pattern, response_class):
    patterns = [pattern("mix/<str:s>/<int:n>/", _ok(response_class))]
    body = serve(patterns, path="/mix/x/9/").body
    assert b"s=x" in body and b"n=9" in body


def test_variable_segment_does_not_span_slash(serve, pattern, response_class):
    patterns = [pattern("user/<str:name>/", _ok(response_class))]
    assert serve(patterns, path="/user/a/b/").status_code == 404


def test_literal_and_variable_segments_combined(serve, pattern, response_class):
    patterns = [pattern("a/<str:mid>/z/", _ok(response_class))]
    assert b"mid=middle" in serve(patterns, path="/a/middle/z/").body


# --- Behavioural: regex patterns ------------------------------------------- #

def test_regex_pattern_resolves(serve, re_pattern, response_class):
    patterns = [re_pattern(r"^rx/(?P<code>[0-9]{3})/$", _ok(response_class))]
    assert b"code=404" in serve(patterns, path="/rx/404/").body


def test_regex_pattern_rejects_non_matching(serve, re_pattern, response_class):
    patterns = [re_pattern(r"^rx/(?P<code>[0-9]{3})/$", _ok(response_class))]
    assert serve(patterns, path="/rx/abcd/").status_code == 404


# --- Edge cases ------------------------------------------------------------ #

def test_resolution_order_first_match_wins(serve, pattern, response_class):
    def literal(request, **_):
        return response_class("literal")

    def variable(request, **params):
        return response_class("variable")
    patterns = [pattern("u/me/", literal), pattern("u/<str:name>/", variable)]
    assert b"literal" in serve(patterns, path="/u/me/").body
    assert b"variable" in serve(patterns, path="/u/other/").body


def test_resolution_is_case_sensitive(serve, pattern, response_class):
    patterns = [pattern("CaseSensitive/", _ok(response_class))]
    assert serve(patterns, path="/casesensitive/").status_code == 404


def test_query_string_does_not_affect_resolution(serve, pattern, response_class):
    patterns = [pattern("q/", _ok(response_class))]
    result = serve(patterns, path="/q/", query={"x": "1", "y": "2"})
    assert result.status_code == 200


def test_trailing_slash_is_part_of_the_pattern(serve, pattern, response_class):
    """With no URL-rewriting middleware configured, the pattern matches exactly.

    An empty pattern list is deliberately not asserted on: a framework is free
    to serve a landing page when nothing is routed, which the specification
    does not fix either way.
    """
    patterns = [pattern("exact/", _ok(response_class))]
    assert serve(patterns, path="/exact/").status_code == 200
    assert serve(patterns, path="/exact").status_code == 404


def test_unmatched_nested_path_is_404(serve, pattern, response_class):
    patterns = [pattern("known/<int:pk>/", _ok(response_class))]
    assert serve(patterns, path="/known/").status_code == 404
