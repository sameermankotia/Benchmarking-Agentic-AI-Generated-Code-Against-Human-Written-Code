"""Application Context — oracle cases for specification area (5).

"application context management using thread-local storage so that
`current_app` and `g` are accessible within a request."

`current_app` and `g` are two of the four names the specification fixes, so
they are read directly off the subject module. The application is identified
through an attribute the test itself sets on the instance, never through a
framework-specific property, so the assertions stay implementation-neutral.
"""

from __future__ import annotations

import threading

import pytest

import wsgi


@pytest.fixture
def marked_app(api):
    """An application carrying a marker attribute set by the test."""
    app = api.app()
    app.oracle_marker = "marker-value"
    return app


@pytest.fixture
def ctx_route(api, marked_app):
    """Register a view on the marked application."""
    counter = {"n": 0}

    def _route(fn, path=None, methods=None):
        counter["n"] += 1
        path = path or f"/ctx{counter['n']}"
        fn.__name__ = f"ctx_view_{counter['n']}"
        api.route(marked_app, path, methods)(fn)
        return path
    return _route


# --- current_app ----------------------------------------------------------- #

def test_current_app_accessible_in_a_view(api, marked_app, ctx_route):
    def view(**_):
        return "yes" if api.current_app is not None else "no"
    path = ctx_route(view)
    assert b"yes" in wsgi.call(marked_app, "GET", path).body


def test_current_app_is_the_handling_application(api, marked_app, ctx_route):
    def view(**_):
        return getattr(api.current_app, "oracle_marker", "absent")
    path = ctx_route(view)
    assert b"marker-value" in wsgi.call(marked_app, "GET", path).body


def test_current_app_accessible_from_a_nested_call(api, marked_app, ctx_route):
    def helper():
        return getattr(api.current_app, "oracle_marker", "absent")

    def view(**_):
        return helper()
    path = ctx_route(view)
    assert b"marker-value" in wsgi.call(marked_app, "GET", path).body


def test_current_app_distinguishes_two_applications(api):
    first, second = api.app(), api.app()
    first.oracle_marker, second.oracle_marker = "first", "second"

    def make(app, name):
        def view(**_):
            return getattr(api.current_app, "oracle_marker", "absent")
        view.__name__ = name
        api.route(app, "/who")(view)
    make(first, "who_first")
    make(second, "who_second")
    assert b"first" in wsgi.call(first, "GET", "/who").body
    assert b"second" in wsgi.call(second, "GET", "/who").body


def test_current_app_unavailable_outside_a_request(api):
    """Reading the context outside a request must not silently succeed."""
    with pytest.raises(Exception):
        getattr(api.current_app, "oracle_marker")


# --- g --------------------------------------------------------------------- #

def test_g_is_writable_in_a_view(api, marked_app, ctx_route):
    def view(**_):
        api.g.value = "stored"
        return "written"
    path = ctx_route(view)
    assert wsgi.call(marked_app, "GET", path).status_code == 200


def test_g_value_readable_back_in_the_same_request(api, marked_app, ctx_route):
    def view(**_):
        api.g.value = "roundtrip"
        return api.g.value
    path = ctx_route(view)
    assert b"roundtrip" in wsgi.call(marked_app, "GET", path).body


def test_g_shared_between_view_and_helper(api, marked_app, ctx_route):
    def helper():
        return api.g.value

    def view(**_):
        api.g.value = "via-helper"
        return helper()
    path = ctx_route(view)
    assert b"via-helper" in wsgi.call(marked_app, "GET", path).body


def test_g_is_empty_at_the_start_of_each_request(api, marked_app, ctx_route):
    def view(**_):
        seen = getattr(api.g, "leaked", "clean")
        api.g.leaked = "dirty"
        return seen
    path = ctx_route(view)
    assert b"clean" in wsgi.call(marked_app, "GET", path).body
    assert b"clean" in wsgi.call(marked_app, "GET", path).body


def test_g_does_not_leak_between_sequential_requests(api, marked_app, ctx_route):
    def view(**_):
        previous = getattr(api.g, "n", "none")
        api.g.n = "set"
        return str(previous)
    path = ctx_route(view)
    first = wsgi.call(marked_app, "GET", path).body
    second = wsgi.call(marked_app, "GET", path).body
    assert first == second == b"none"


def test_g_missing_attribute_raises(api, marked_app, ctx_route):
    def view(**_):
        try:
            _ = api.g.never_set
        except AttributeError:
            return "raised"
        return "did-not-raise"
    path = ctx_route(view)
    assert b"raised" in wsgi.call(marked_app, "GET", path).body


def test_g_getattr_default_works(api, marked_app, ctx_route):
    def view(**_):
        return getattr(api.g, "never_set", "defaulted")
    path = ctx_route(view)
    assert b"defaulted" in wsgi.call(marked_app, "GET", path).body


def test_g_holds_non_string_values(api, marked_app, ctx_route):
    def view(**_):
        api.g.payload = {"k": [1, 2, 3]}
        return str(api.g.payload["k"][2])
    path = ctx_route(view)
    assert b"3" in wsgi.call(marked_app, "GET", path).body


def test_g_unavailable_outside_a_request(api):
    with pytest.raises(Exception):
        api.g.anything = "x"


# --- request, alongside the context ---------------------------------------- #

def test_request_accessible_in_the_same_context(api, marked_app, ctx_route):
    req = api.request

    def view(**_):
        return api.path(req)
    path = ctx_route(view, path="/both")
    assert b"/both" in wsgi.call(marked_app, "GET", path).body


def test_request_and_g_coexist(api, marked_app, ctx_route):
    req = api.request

    def view(**_):
        api.g.seen = api.path(req)
        return api.g.seen
    path = ctx_route(view, path="/coexist")
    assert b"/coexist" in wsgi.call(marked_app, "GET", path).body


def test_current_app_and_g_coexist(api, marked_app, ctx_route):
    def view(**_):
        api.g.marker = getattr(api.current_app, "oracle_marker", "absent")
        return api.g.marker
    path = ctx_route(view)
    assert b"marker-value" in wsgi.call(marked_app, "GET", path).body


# --- Thread-local behaviour ------------------------------------------------- #

def test_g_is_isolated_between_concurrent_threads(api, marked_app, ctx_route):
    """Two in-flight requests must not see each other's `g`.

    The barrier forces both views to be inside their request at the same
    time, which is what makes this a test of thread-local storage rather than
    of sequential cleanup.
    """
    barrier = threading.Barrier(2, timeout=5)
    req = api.request

    def view(**_):
        own = api.query_get(req, "tag")
        api.g.tag = own
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass
        return api.g.tag
    path = ctx_route(view)

    results: dict[str, bytes] = {}

    def run(tag):
        results[tag] = wsgi.call(
            marked_app, "GET", path, query={"tag": tag}).body

    threads = [threading.Thread(target=run, args=(t,)) for t in ("aaa", "bbb")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert results.get("aaa") == b"aaa"
    assert results.get("bbb") == b"bbb"


def test_current_app_is_correct_in_concurrent_threads(api):
    first, second = api.app(), api.app()
    first.oracle_marker, second.oracle_marker = "A", "B"
    barrier = threading.Barrier(2, timeout=5)

    def make(app, name):
        def view(**_):
            marker = getattr(api.current_app, "oracle_marker", "absent")
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass
            return marker
        view.__name__ = name
        api.route(app, "/c")(view)
    make(first, "c_first")
    make(second, "c_second")

    out: dict[str, bytes] = {}

    def run(key, app):
        out[key] = wsgi.call(app, "GET", "/c").body

    threads = [threading.Thread(target=run, args=kv)
               for kv in (("a", first), ("b", second))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert out.get("a") == b"A"
    assert out.get("b") == b"B"


def test_context_is_released_after_the_request(api, marked_app, ctx_route):
    def view(**_):
        api.g.inside = "yes"
        return "done"
    path = ctx_route(view)
    assert wsgi.call(marked_app, "GET", path).status_code == 200
    with pytest.raises(Exception):
        _ = api.g.inside


def test_many_sequential_requests_keep_context_clean(api, marked_app, ctx_route):
    def view(**_):
        seen = getattr(api.g, "count", 0)
        api.g.count = seen + 1
        return str(seen)
    path = ctx_route(view)
    bodies = {wsgi.call(marked_app, "GET", path).body for _ in range(10)}
    assert bodies == {b"0"}
