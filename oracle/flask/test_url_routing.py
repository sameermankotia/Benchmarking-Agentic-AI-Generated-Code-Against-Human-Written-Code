"""URL Routing — 25 oracle cases (paper §3.3.1).

Spec area (1): URL routing with variable segments and HTTP method filtering.
Behavioural assertions only; no implementation internals.
"""

from __future__ import annotations

import pytest


def _register(app, rule, **kw):
    @app.route(rule, **kw)
    def _view(**kwargs):
        return "|".join(f"{k}={v}" for k, v in sorted(kwargs.items())) or "ok"
    return _view


# --- Basic: API surface ---------------------------------------------------- #

def test_route_decorator_accepts_rule_string(app):
    _register(app, "/hello")
    assert any(r.rule == "/hello" for r in app.url_map.iter_rules())


def test_static_route_dispatch(client, app):
    _register(app, "/ping")
    assert client.get("/ping").data == b"ok"


def test_root_route(client, app):
    _register(app, "/")
    assert client.get("/").status_code == 200


def test_unregistered_path_is_404(client, app):
    _register(app, "/exists")
    assert client.get("/missing").status_code == 404


def test_add_url_rule_api(client, app):
    app.add_url_rule("/added", "added", lambda: "added")
    assert client.get("/added").data == b"added"


# --- Behavioural: variable segments ---------------------------------------- #

@pytest.mark.parametrize("path,expected", [
    ("/user/alice", b"name=alice"),
    ("/user/bob", b"name=bob"),
    ("/user/123", b"name=123"),
])
def test_string_variable_segment(client, app, path, expected):
    _register(app, "/user/<name>")
    assert client.get(path).data == expected


@pytest.mark.parametrize("path,code", [("/post/42", 200), ("/post/abc", 404)])
def test_int_converter(client, app, path, code):
    _register(app, "/post/<int:pid>")
    assert client.get(path).status_code == code


def test_int_converter_value(client, app):
    _register(app, "/post/<int:pid>")
    assert client.get("/post/42").data == b"pid=42"


def test_path_converter_allows_slashes(client, app):
    _register(app, "/files/<path:p>")
    assert client.get("/files/a/b/c.txt").data == b"p=a/b/c.txt"


@pytest.mark.parametrize("path,expected", [
    ("/mix/x/9", b"n=9|s=x"),
    ("/mix/y/0", b"n=0|s=y"),
])
def test_multiple_variable_segments(client, app, path, expected):
    _register(app, "/mix/<s>/<int:n>")
    assert client.get(path).data == expected


def test_float_converter(client, app):
    _register(app, "/rate/<float:r>")
    assert client.get("/rate/3.5").data == b"r=3.5"


# --- Behavioural: HTTP method filtering ------------------------------------ #

def test_default_route_allows_get(client, app):
    _register(app, "/g")
    assert client.get("/g").status_code == 200


def test_default_route_rejects_post(client, app):
    _register(app, "/g")
    assert client.post("/g").status_code == 405


def test_post_only_route(client, app):
    _register(app, "/p", methods=["POST"])
    assert client.post("/p").status_code == 200
    assert client.get("/p").status_code == 405


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_multi_method_route(client, app, method):
    _register(app, "/multi", methods=["GET", "POST", "PUT", "DELETE"])
    assert client.open("/multi", method=method).status_code == 200


def test_405_lists_allowed_methods(client, app):
    _register(app, "/only", methods=["POST"])
    resp = client.get("/only")
    assert resp.status_code == 405
    assert "POST" in resp.headers.get("Allow", "")


def test_head_implied_by_get(client, app):
    _register(app, "/h")
    assert client.head("/h").status_code == 200


def test_options_auto_provided(client, app):
    _register(app, "/o")
    assert client.options("/o").status_code == 200


# --- Edge cases ------------------------------------------------------------ #

def test_trailing_slash_redirect(client, app):
    _register(app, "/dir/")
    assert client.get("/dir").status_code in (301, 308)


def test_route_precedence_static_over_dynamic(client, app):
    @app.route("/u/me")
    def me():
        return "me"
    @app.route("/u/<name>")
    def other(name):
        return name
    assert client.get("/u/me").data == b"me"
    assert client.get("/u/xyz").data == b"xyz"


def test_two_rules_same_endpoint_name_conflict(app):
    _register(app, "/dup")
    with pytest.raises(Exception):
        @app.route("/dup2", endpoint="_view")
        def _dup():
            return "x"


def test_url_map_contains_all_registered(app):
    for p in ("/a", "/b", "/c"):
        app.add_url_rule(p, p, lambda: "x")
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert {"/a", "/b", "/c"} <= rules


def test_case_sensitive_path(client, app):
    _register(app, "/CaseSensitive")
    assert client.get("/casesensitive").status_code == 404


def test_query_string_does_not_affect_matching(client, app):
    _register(app, "/q")
    assert client.get("/q?x=1&y=2").status_code == 200
