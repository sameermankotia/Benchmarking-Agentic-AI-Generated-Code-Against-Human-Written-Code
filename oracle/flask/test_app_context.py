"""Application Context — 22 oracle cases (paper §3.3.1).

Spec area (5): application context management using thread-local storage so
that current_app and g are accessible within a request. This is the area the
paper reports as hardest for agentic systems (§4.1).
"""

from __future__ import annotations

import threading

import pytest


def test_current_app_available_in_request(app, fw):
    @app.route("/ca")
    def ca():
        return {"name": fw.current_app.name}
    assert app.test_client().get("/ca").json["name"] == app.name


def test_g_is_writable_in_request(app, fw):
    @app.route("/g")
    def g_view():
        fw.g.value = "stored"
        return {"g": fw.g.value}
    assert app.test_client().get("/g").json["g"] == "stored"


def test_g_isolated_between_requests(app, fw):
    @app.route("/gi")
    def gi():
        seen = getattr(fw.g, "leaked", "clean")
        fw.g.leaked = "dirty"
        return {"seen": seen}
    c = app.test_client()
    assert c.get("/gi").json["seen"] == "clean"
    assert c.get("/gi").json["seen"] == "clean"


def test_app_context_manual_push(app, fw):
    with app.app_context():
        assert fw.current_app.name == app.name


def test_app_context_pops(app, fw):
    with app.app_context():
        pass
    # Outside the context, accessing current_app must fail, not leak.
    with pytest.raises(RuntimeError):
        _ = fw.current_app.name


def test_request_context_provides_request(app, fw):
    with app.test_request_context("/x?y=1"):
        assert fw.request.path == "/x"
        assert fw.request.args.get("y") == "1"


def test_test_request_context_method(app, fw):
    with app.test_request_context("/p", method="POST"):
        assert fw.request.method == "POST"


def test_g_shared_within_single_request(app, fw):
    @app.before_request
    def seed():
        fw.g.user = "alice"

    @app.route("/who")
    def who():
        return {"user": fw.g.user}
    assert app.test_client().get("/who").json["user"] == "alice"


def test_teardown_appcontext_runs(app, fw):
    calls = []

    @app.teardown_appcontext
    def teardown(exc):
        calls.append(1)

    @app.route("/td")
    def td():
        return "x"
    app.test_client().get("/td")
    assert calls == [1]


def test_before_request_can_short_circuit(app, fw):
    @app.before_request
    def guard():
        return "blocked", 401

    @app.route("/prot")
    def prot():
        return "secret"
    r = app.test_client().get("/prot")
    assert r.status_code == 401 and r.data == b"blocked"


def test_after_request_can_modify_response(app, fw):
    @app.after_request
    def add_header(resp):
        resp.headers["X-Processed"] = "1"
        return resp

    @app.route("/ar")
    def ar():
        return "x"
    assert app.test_client().get("/ar").headers["X-Processed"] == "1"


def test_current_app_outside_context_raises(app, fw):
    with pytest.raises(RuntimeError):
        _ = fw.current_app.name


def test_g_outside_context_raises(app, fw):
    with pytest.raises(RuntimeError):
        _ = fw.g.anything


def test_nested_app_contexts(app, fw):
    with app.app_context():
        outer = fw.current_app.name
        with app.app_context():
            assert fw.current_app.name == outer
        assert fw.current_app.name == outer


def test_context_local_across_threads(app, fw):
    results = {}

    @app.route("/thr")
    def thr():
        fw.g.tid = threading.get_ident()
        return {"tid": fw.g.tid}

    def worker(key):
        results[key] = app.test_client().get("/thr").json["tid"]

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 2  # each thread got its own context without error


def test_url_for_within_app_context(app, fw):
    @app.route("/dest")
    def dest():
        return "d"
    with app.test_request_context():
        assert fw.url_for("dest") == "/dest"


def test_config_accessible_via_current_app(app, fw):
    app.config["MY_SETTING"] = "val"

    @app.route("/cfg")
    def cfg():
        return {"v": fw.current_app.config["MY_SETTING"]}
    assert app.test_client().get("/cfg").json["v"] == "val"


def test_multiple_before_request_order(app, fw):
    order = []

    @app.before_request
    def first():
        order.append("first")

    @app.before_request
    def second():
        order.append("second")

    @app.route("/ord")
    def ord_view():
        return "x"
    app.test_client().get("/ord")
    assert order == ["first", "second"]


def test_g_setdefault(app, fw):
    @app.route("/sd")
    def sd():
        fw.g.setdefault("counter", 0)
        return {"c": fw.g.counter}
    assert app.test_client().get("/sd").json["c"] == 0


def test_teardown_receives_none_on_success(app, fw):
    received = []

    @app.teardown_request
    def td(exc):
        received.append(exc)

    @app.route("/ok")
    def ok():
        return "x"
    app.test_client().get("/ok")
    assert received == [None]


def test_request_context_json_body(app, fw):
    with app.test_request_context("/j", method="POST", json={"k": 5}):
        assert fw.request.get_json()["k"] == 5


def test_appcontext_pushed_flag(app, fw):
    with app.app_context():
        assert fw.current_app._get_current_object() is app
