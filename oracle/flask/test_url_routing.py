"""URL Routing — oracle cases for specification area (1).

"URL routing with variable segments and HTTP method filtering."

Every assertion is made on the WSGI response (status line, headers, body).
Rule strings are built through `api.rule`, because the specification requires
variable segments but does not fix their syntax.
"""

from __future__ import annotations

import pytest


def _view(**params):
    """Report the captured variable segments, or "ok" when there are none."""
    return "|".join(f"{k}={v}" for k, v in sorted(params.items())) or "ok"


# --- Basic: registration and dispatch -------------------------------------- #

def test_route_accepts_rule_string(route, get):
    route("/hello")(_view)
    assert get("/hello").status_code == 200


def test_static_route_returns_view_body(route, get):
    route("/ping")(_view)
    assert b"ok" in get("/ping").body


def test_root_route(route, get):
    route("/")(_view)
    assert get("/").status_code == 200


def test_unregistered_path_is_404(route, get):
    route("/exists")(_view)
    assert get("/missing").status_code == 404


def test_two_routes_dispatch_independently(route, get):
    def first(**_):
        return "first"

    def second(**_):
        return "second"
    route("/one")(first)
    route("/two")(second)
    assert b"first" in get("/one").body
    assert b"second" in get("/two").body


def test_response_is_200_with_a_body(route, get):
    def body(**_):
        return "content-here"
    route("/body")(body)
    result = get("/body")
    assert result.status_code == 200
    assert b"content-here" in result.body


# --- Behavioural: variable segments ---------------------------------------- #

@pytest.mark.parametrize("value", ["alice", "bob", "123", "a-b_c"])
def test_variable_segment_value_reaches_view(api, route, get, value):
    route(api.rule("user", ":name"))(_view)
    assert f"name={value}".encode() in get(f"/user/{value}").body


def test_variable_segment_matches_any_single_segment(api, route, get):
    route(api.rule("item", ":id"))(_view)
    assert get("/item/anything").status_code == 200


def test_variable_segment_does_not_span_slash(api, route, get):
    route(api.rule("user", ":name"))(_view)
    assert get("/user/alice/extra").status_code == 404


def test_variable_segment_requires_a_value(api, route, get):
    route(api.rule("user", ":name"))(_view)
    assert get("/user/").status_code in (301, 308, 404)


@pytest.mark.parametrize("path,expected", [
    ("/mix/x/9", [b"s=x", b"n=9"]),
    ("/mix/y/0", [b"s=y", b"n=0"]),
])
def test_multiple_variable_segments(api, route, get, path, expected):
    route(api.rule("mix", ":s", ":n"))(_view)
    body = get(path).body
    assert all(fragment in body for fragment in expected)


def test_variable_and_literal_segments_combined(api, route, get):
    route(api.rule("a", ":mid", "z"))(_view)
    assert b"mid=middle" in get("/a/middle/z").body


def test_static_route_takes_precedence_over_variable(api, route, get):
    def literal(**_):
        return "literal"
    route("/u/me")(literal)
    route(api.rule("u", ":name"))(_view)
    assert b"literal" in get("/u/me").body
    assert b"name=other" in get("/u/other").body


# --- Behavioural: HTTP method filtering ------------------------------------ #

def test_default_route_allows_get(route, get):
    route("/g")(_view)
    assert get("/g").status_code == 200


def test_method_restricted_route_accepts_its_method(route, request_):
    route("/p", methods=["POST"])(_view)
    assert request_("POST", "/p").status_code == 200


def test_method_restricted_route_rejects_other_method(route, get):
    route("/p", methods=["POST"])(_view)
    assert get("/p").status_code == 405


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_multi_method_route_accepts_each(route, request_, method):
    route("/multi", methods=["GET", "POST", "PUT", "DELETE"])(_view)
    assert request_(method, "/multi").status_code == 200


def test_method_not_in_list_is_rejected(route, request_):
    route("/limited", methods=["GET", "POST"])(_view)
    assert request_("DELETE", "/limited").status_code == 405


def test_405_advertises_an_allow_header(route, get):
    route("/only", methods=["POST"])(_view)
    result = get("/only")
    assert result.status_code == 405
    assert "POST" in result.header("Allow")


def test_method_filtering_is_per_route(route, get, request_):
    def readonly(**_):
        return "r"

    def writeonly(**_):
        return "w"
    route("/readonly", methods=["GET"])(readonly)
    route("/writeonly", methods=["POST"])(writeonly)
    assert get("/readonly").status_code == 200
    assert get("/writeonly").status_code == 405
    assert request_("POST", "/writeonly").status_code == 200


# --- Edge cases ------------------------------------------------------------ #

def test_path_matching_is_case_sensitive(route, get):
    route("/CaseSensitive")(_view)
    assert get("/casesensitive").status_code == 404


def test_query_string_does_not_affect_matching(route, get):
    route("/q")(_view)
    assert get("/q", query={"x": "1", "y": "2"}).status_code == 200


def test_unregistered_method_on_unregistered_path_is_404(route, request_):
    route("/known")(_view)
    assert request_("POST", "/unknown").status_code == 404
