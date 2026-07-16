"""Blueprints — 20 oracle cases (paper §3.3.1).

Spec area (6): Blueprint-based modular applications with URL prefix
inheritance. The paper reports 65% parity across all three subjects here
(§4.1), so the suite intentionally probes edge cases.
"""

from __future__ import annotations

import pytest


def _bp(fw, name="bp", **kw):
    bp = fw.Blueprint(name, __name__, **kw)

    @bp.route("/item")
    def item():
        return f"{name}-item"
    return bp


def test_blueprint_registers_route(app, fw):
    app.register_blueprint(_bp(fw))
    assert app.test_client().get("/item").data == b"bp-item"


def test_blueprint_url_prefix(app, fw):
    app.register_blueprint(_bp(fw), url_prefix="/api")
    assert app.test_client().get("/api/item").data == b"bp-item"


def test_blueprint_prefix_excludes_root(app, fw):
    app.register_blueprint(_bp(fw), url_prefix="/api")
    assert app.test_client().get("/item").status_code == 404


def test_blueprint_defined_prefix(app, fw):
    bp = _bp(fw, name="pre", url_prefix="/pre")
    app.register_blueprint(bp)
    assert app.test_client().get("/pre/item").data == b"pre-item"


def test_two_blueprints_distinct_prefixes(app, fw):
    app.register_blueprint(_bp(fw, name="a"), url_prefix="/a")
    app.register_blueprint(_bp(fw, name="b"), url_prefix="/b")
    c = app.test_client()
    assert c.get("/a/item").data == b"a-item"
    assert c.get("/b/item").data == b"b-item"


def test_blueprint_endpoint_namespacing(app, fw):
    app.register_blueprint(_bp(fw, name="ns"), url_prefix="/ns")
    with app.test_request_context():
        assert fw.url_for("ns.item") == "/ns/item"


def test_blueprint_before_request(app, fw):
    bp = fw.Blueprint("br", __name__)
    hits = []

    @bp.before_request
    def before():
        hits.append(1)

    @bp.route("/br")
    def br():
        return "x"
    app.register_blueprint(bp)
    app.test_client().get("/br")
    assert hits == [1]


def test_blueprint_before_request_scoped(app, fw):
    bp = fw.Blueprint("scoped", __name__)
    hits = []

    @bp.before_request
    def before():
        hits.append(1)

    @bp.route("/in")
    def in_view():
        return "x"
    app.register_blueprint(bp)

    @app.route("/out")
    def out_view():
        return "y"
    c = app.test_client()
    c.get("/out")
    assert hits == []  # blueprint hook must not fire for app-level routes
    c.get("/in")
    assert hits == [1]


def test_blueprint_variable_route(app, fw):
    bp = fw.Blueprint("var", __name__)

    @bp.route("/u/<name>")
    def u(name):
        return name
    app.register_blueprint(bp, url_prefix="/v")
    assert app.test_client().get("/v/u/bob").data == b"bob"


def test_blueprint_multiple_routes(app, fw):
    bp = fw.Blueprint("multi", __name__)

    @bp.route("/one")
    def one():
        return "1"

    @bp.route("/two")
    def two():
        return "2"
    app.register_blueprint(bp, url_prefix="/m")
    c = app.test_client()
    assert c.get("/m/one").data == b"1"
    assert c.get("/m/two").data == b"2"


def test_blueprint_method_filtering(app, fw):
    bp = fw.Blueprint("meth", __name__)

    @bp.route("/post", methods=["POST"])
    def post_only():
        return "ok"
    app.register_blueprint(bp)
    c = app.test_client()
    assert c.post("/post").status_code == 200
    assert c.get("/post").status_code == 405


def test_blueprint_registered_twice_different_prefix(app, fw):
    bp = _bp(fw, name="reuse")
    app.register_blueprint(bp, url_prefix="/x", name="rx")
    app.register_blueprint(bp, url_prefix="/y", name="ry")
    c = app.test_client()
    assert c.get("/x/item").status_code == 200
    assert c.get("/y/item").status_code == 200


def test_blueprint_error_handler(app, fw):
    bp = fw.Blueprint("err", __name__)

    @bp.route("/boom")
    def boom():
        fw.abort(418)

    @bp.errorhandler(418)
    def handle(e):
        return "teapot", 418
    app.register_blueprint(bp)
    r = app.test_client().get("/boom")
    assert r.status_code == 418 and r.data == b"teapot"


def test_blueprint_request_blueprint_name(app, fw):
    bp = fw.Blueprint("named", __name__)
    req = fw.request

    @bp.route("/name")
    def name():
        return {"bp": req.blueprint}
    app.register_blueprint(bp)
    assert app.test_client().get("/name").json["bp"] == "named"


def test_blueprint_nested_prefix(app, fw):
    parent = fw.Blueprint("parent", __name__, url_prefix="/parent")
    child = fw.Blueprint("child", __name__, url_prefix="/child")

    @child.route("/leaf")
    def leaf():
        return "leaf"
    parent.register_blueprint(child)
    app.register_blueprint(parent)
    assert app.test_client().get("/parent/child/leaf").data == b"leaf"


def test_blueprint_after_request(app, fw):
    bp = fw.Blueprint("aft", __name__)

    @bp.after_request
    def add(resp):
        resp.headers["X-BP"] = "1"
        return resp

    @bp.route("/aft")
    def aft():
        return "x"
    app.register_blueprint(bp)
    assert app.test_client().get("/aft").headers["X-BP"] == "1"


def test_blueprint_url_defaults(app, fw):
    bp = fw.Blueprint("ud", __name__)

    @bp.route("/page")
    def page():
        return "p"
    app.register_blueprint(bp, url_prefix="/ud")
    assert app.test_client().get("/ud/page").status_code == 200


def test_blueprint_trailing_slash(app, fw):
    bp = fw.Blueprint("ts", __name__)

    @bp.route("/dir/")
    def d():
        return "d"
    app.register_blueprint(bp, url_prefix="/ts")
    assert app.test_client().get("/ts/dir/").status_code == 200


def test_blueprint_static_and_dynamic_precedence(app, fw):
    bp = fw.Blueprint("prec", __name__)

    @bp.route("/x/me")
    def me():
        return "me"

    @bp.route("/x/<v>")
    def other(v):
        return v
    app.register_blueprint(bp, url_prefix="/p")
    c = app.test_client()
    assert c.get("/p/x/me").data == b"me"
    assert c.get("/p/x/z").data == b"z"


def test_blueprint_url_for_from_other_endpoint(app, fw):
    bp = fw.Blueprint("cross", __name__)

    @bp.route("/dest")
    def dest():
        return "d"

    @bp.route("/src")
    def src():
        return fw.url_for("cross.dest")
    app.register_blueprint(bp, url_prefix="/c")
    assert app.test_client().get("/c/src").data == b"/c/dest"
