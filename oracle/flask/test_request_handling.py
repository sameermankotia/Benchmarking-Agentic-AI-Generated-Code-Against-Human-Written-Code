"""Request Handling — 20 oracle cases (paper §3.3.1).

Spec area (2): request object encapsulating method, path, headers, query
string, and body.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def echo_app(app, fw):
    req = fw.request

    @app.route("/echo", methods=["GET", "POST", "PUT"])
    def echo():
        return {
            "method": req.method,
            "path": req.path,
            "arg": req.args.get("x", ""),
            "form": req.form.get("f", ""),
            "header": req.headers.get("X-Test", ""),
        }
    return app


def test_request_exposes_method(echo_app):
    c = echo_app.test_client()
    assert c.get("/echo").json["method"] == "GET"


def test_request_exposes_path(echo_app):
    c = echo_app.test_client()
    assert c.get("/echo").json["path"] == "/echo"


def test_request_query_arg(echo_app):
    c = echo_app.test_client()
    assert c.get("/echo?x=hello").json["arg"] == "hello"


def test_request_missing_query_arg_default(echo_app):
    c = echo_app.test_client()
    assert c.get("/echo").json["arg"] == ""


@pytest.mark.parametrize("val", ["a", "b b", "%20", "1+1"])
def test_request_query_arg_values(echo_app, val):
    c = echo_app.test_client()
    assert c.get("/echo", query_string={"x": val}).json["arg"] == val


def test_request_form_body(echo_app):
    c = echo_app.test_client()
    assert c.post("/echo", data={"f": "posted"}).json["form"] == "posted"


def test_request_custom_header(echo_app):
    c = echo_app.test_client()
    assert c.get("/echo", headers={"X-Test": "yes"}).json["header"] == "yes"


def test_request_method_post(echo_app):
    c = echo_app.test_client()
    assert c.post("/echo").json["method"] == "POST"


def test_request_method_put(echo_app):
    c = echo_app.test_client()
    assert c.put("/echo").json["method"] == "PUT"


def test_request_json_body(app, fw):
    req = fw.request

    @app.route("/j", methods=["POST"])
    def j():
        return {"got": req.get_json()["k"]}
    assert app.test_client().post("/j", json={"k": "v"}).json["got"] == "v"


def test_request_args_multidict_getlist(app, fw):
    req = fw.request

    @app.route("/list")
    def lst():
        return {"vals": req.args.getlist("n")}
    r = app.test_client().get("/list?n=1&n=2&n=3")
    assert r.json["vals"] == ["1", "2", "3"]


def test_request_content_type_available(app, fw):
    req = fw.request

    @app.route("/ct", methods=["POST"])
    def ct():
        return {"ct": req.content_type or ""}
    r = app.test_client().post("/ct", json={"a": 1})
    assert "application/json" in r.json["ct"]


def test_request_cookies(app, fw):
    req = fw.request

    @app.route("/cook")
    def cook():
        return {"c": req.cookies.get("sid", "")}
    c = app.test_client()
    c.set_cookie("sid", "abc")
    assert c.get("/cook").json["c"] == "abc"


def test_request_view_args_populated(app, fw):
    req = fw.request

    @app.route("/va/<item>")
    def va(item):
        return {"va": req.view_args.get("item")}
    assert app.test_client().get("/va/thing").json["va"] == "thing"


def test_request_full_path_includes_query(app, fw):
    req = fw.request

    @app.route("/fp")
    def fp():
        return {"fp": req.full_path}
    assert "x=1" in app.test_client().get("/fp?x=1").json["fp"]


def test_request_is_json_flag(app, fw):
    req = fw.request

    @app.route("/isj", methods=["POST"])
    def isj():
        return {"isj": bool(req.is_json)}
    assert app.test_client().post("/isj", json={}).json["isj"] is True


def test_request_raw_data(app, fw):
    req = fw.request

    @app.route("/raw", methods=["POST"])
    def raw():
        return {"len": len(req.get_data())}
    assert app.test_client().post("/raw", data=b"12345").json["len"] == 5


def test_request_url_property(app, fw):
    req = fw.request

    @app.route("/url")
    def url():
        return {"url": req.url}
    assert app.test_client().get("/url").json["url"].endswith("/url")


def test_request_blueprint_none_at_app_level(app, fw):
    req = fw.request

    @app.route("/nb")
    def nb():
        return {"bp": req.blueprint or "none"}
    assert app.test_client().get("/nb").json["bp"] == "none"


def test_request_scheme(app, fw):
    req = fw.request

    @app.route("/scheme")
    def scheme():
        return {"scheme": req.scheme}
    assert app.test_client().get("/scheme").json["scheme"] in ("http", "https")
