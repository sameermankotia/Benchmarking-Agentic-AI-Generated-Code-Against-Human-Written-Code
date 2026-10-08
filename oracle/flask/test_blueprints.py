"""Blueprints — oracle cases for specification area (6).

"Blueprint-based modular applications with URL prefix inheritance."

`Blueprint` is one of the four names the specification fixes; how a blueprint
is constructed and mounted is not, so both go through the resolved roles
(`api.blueprint`, `api.register`). Reachability is asserted over WSGI.
"""

from __future__ import annotations

import pytest

import wsgi


def _view(**params):
    return "|".join(f"{k}={v}" for k, v in sorted(params.items())) or "ok"


@pytest.fixture
def mount(api, app):
    """Build a blueprint, add routes to it, and mount it on the application."""
    counter = {"n": 0}

    def _mount(routes, url_prefix=None, name=None):
        counter["n"] += 1
        bp = api.blueprint(name or f"bp{counter['n']}", url_prefix=url_prefix)
        for i, (rule, methods, fn) in enumerate(routes):
            fn.__name__ = f"bp{counter['n']}_view{i}"
            api.route(bp, rule, methods)(fn)
        api.register(app, bp, url_prefix=url_prefix)
        return bp
    return _mount


# --- Basic: construction and registration ---------------------------------- #

def test_blueprint_can_be_constructed(api):
    assert api.blueprint("plain") is not None


def test_blueprint_route_is_reachable_after_registration(mount, get):
    mount([("/inside", None, _view)])
    assert get("/inside").status_code == 200


def test_blueprint_route_returns_its_body(mount, get):
    def view(**_):
        return "from-blueprint"
    mount([("/body", None, view)])
    assert b"from-blueprint" in get("/body").body


def test_unregistered_blueprint_route_is_not_reachable(api, app, get):
    bp = api.blueprint("orphan")
    api.route(bp, "/orphaned")(_view)
    # Deliberately not registered.
    assert get("/orphaned").status_code == 404


def test_blueprint_with_several_routes(mount, get):
    def one(**_):
        return "one"

    def two(**_):
        return "two"
    mount([("/one", None, one), ("/two", None, two)])
    assert b"one" in get("/one").body
    assert b"two" in get("/two").body


# --- Behavioural: URL prefix inheritance ----------------------------------- #

def test_url_prefix_is_applied(mount, get):
    mount([("/item", None, _view)], url_prefix="/api")
    assert get("/api/item").status_code == 200


def test_route_not_reachable_without_the_prefix(mount, get):
    mount([("/item", None, _view)], url_prefix="/api")
    assert get("/item").status_code == 404


def test_all_blueprint_routes_inherit_the_prefix(mount, get):
    def a(**_):
        return "a"

    def b(**_):
        return "b"
    mount([("/a", None, a), ("/b", None, b)], url_prefix="/v1")
    assert b"a" in get("/v1/a").body
    assert b"b" in get("/v1/b").body


def test_prefix_with_multiple_segments(mount, get):
    mount([("/deep", None, _view)], url_prefix="/a/b")
    assert get("/a/b/deep").status_code == 200


def test_blueprint_root_route_under_prefix(mount, get):
    mount([("/", None, _view)], url_prefix="/root")
    assert get("/root/").status_code in (200, 301, 308)


def test_two_blueprints_with_different_prefixes(mount, get):
    def first(**_):
        return "first"

    def second(**_):
        return "second"
    mount([("/x", None, first)], url_prefix="/one", name="bp_one")
    mount([("/x", None, second)], url_prefix="/two", name="bp_two")
    assert b"first" in get("/one/x").body
    assert b"second" in get("/two/x").body


def test_blueprint_without_prefix_mounts_at_root(mount, get):
    mount([("/bare", None, _view)])
    assert get("/bare").status_code == 200


# --- Behavioural: routing features inside a blueprint ---------------------- #

def test_variable_segment_inside_a_blueprint(api, mount, get):
    mount([(api.rule("user", ":name"), None, _view)], url_prefix="/api")
    assert b"name=zoe" in get("/api/user/zoe").body


@pytest.mark.parametrize("value", ["one", "2", "three-3"])
def test_variable_segment_values_inside_a_blueprint(api, mount, get, value):
    mount([(api.rule("v", ":val"), None, _view)], url_prefix="/p")
    assert f"val={value}".encode() in get(f"/p/v/{value}").body


def test_method_filtering_inside_a_blueprint(mount, get, request_):
    mount([("/post-only", ["POST"], _view)], url_prefix="/api")
    assert request_("POST", "/api/post-only").status_code == 200
    assert get("/api/post-only").status_code == 405


def test_multi_method_route_inside_a_blueprint(mount, request_):
    mount([("/multi", ["GET", "PUT"], _view)], url_prefix="/api")
    assert request_("GET", "/api/multi").status_code == 200
    assert request_("PUT", "/api/multi").status_code == 200


def test_blueprint_and_app_routes_coexist(api, app, mount, route, get):
    def app_view(**_):
        return "app-level"
    route("/app-route")(app_view)

    def bp_view(**_):
        return "bp-level"
    mount([("/bp-route", None, bp_view)], url_prefix="/mod")

    assert b"app-level" in get("/app-route").body
    assert b"bp-level" in get("/mod/bp-route").body


# --- Edge cases ------------------------------------------------------------ #

def test_prefix_does_not_leak_to_app_routes(mount, route, get):
    mount([("/inside", None, _view)], url_prefix="/pre")

    def app_view(**_):
        return "root"
    route("/inside")(app_view)
    assert b"root" in get("/inside").body
    assert get("/pre/inside").status_code == 200


def test_three_blueprints_mounted_together(mount, get):
    def a(**_):
        return "alpha"

    def b(**_):
        return "beta"

    def c(**_):
        return "gamma"
    mount([("/x", None, a)], url_prefix="/a", name="bp_a")
    mount([("/x", None, b)], url_prefix="/b", name="bp_b")
    mount([("/x", None, c)], url_prefix="/c", name="bp_c")
    assert b"alpha" in get("/a/x").body
    assert b"beta" in get("/b/x").body
    assert b"gamma" in get("/c/x").body


def test_unknown_path_under_a_prefix_is_404(mount, get):
    mount([("/known", None, _view)], url_prefix="/api")
    assert get("/api/unknown").status_code == 404
