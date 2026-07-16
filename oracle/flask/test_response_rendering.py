"""Response Rendering — 18 oracle cases (paper §3.3.1).

Spec area (3): response object with status code, headers, and body, plus the
make_response helper and content-type handling.
"""

from __future__ import annotations

import pytest


def test_string_return_is_200(client, app):
    @app.route("/s")
    def s():
        return "hello"
    r = client.get("/s")
    assert r.status_code == 200 and r.data == b"hello"


def test_string_return_is_html_content_type(client, app):
    @app.route("/h")
    def h():
        return "<b>hi</b>"
    assert "text/html" in client.get("/h").headers["Content-Type"]


def test_tuple_sets_status_code(client, app):
    @app.route("/created")
    def created():
        return "made", 201
    assert client.get("/created").status_code == 201


def test_tuple_sets_headers(client, app):
    @app.route("/hdr")
    def hdr():
        return "x", 200, {"X-Custom": "v"}
    assert client.get("/hdr").headers["X-Custom"] == "v"


def test_dict_return_is_json(client, app):
    @app.route("/d")
    def d():
        return {"a": 1}
    r = client.get("/d")
    assert r.json == {"a": 1}
    assert "application/json" in r.headers["Content-Type"]


def test_list_return_is_json(client, app):
    @app.route("/l")
    def l():
        return [1, 2, 3]
    assert client.get("/l").json == [1, 2, 3]


def test_make_response_wraps_string(client, app, fw):
    @app.route("/mr")
    def mr():
        resp = fw.make_response("body")
        resp.status_code = 202
        return resp
    r = client.get("/mr")
    assert r.status_code == 202 and r.data == b"body"


def test_make_response_set_header(client, app, fw):
    @app.route("/mrh")
    def mrh():
        resp = fw.make_response("x")
        resp.headers["X-Made"] = "1"
        return resp
    assert client.get("/mrh").headers["X-Made"] == "1"


def test_response_class_direct(client, app, fw):
    @app.route("/rc")
    def rc():
        return fw.Response("direct", status=203, mimetype="text/plain")
    r = client.get("/rc")
    assert r.status_code == 203
    assert "text/plain" in r.headers["Content-Type"]


def test_jsonify_helper(client, app, fw):
    @app.route("/jf")
    def jf():
        return fw.jsonify(ok=True)
    assert client.get("/jf").json == {"ok": True}


@pytest.mark.parametrize("code", [200, 201, 400, 404, 500])
def test_explicit_status_codes(client, app, code):
    @app.route("/code")
    def code_view():
        return "x", code
    assert client.get("/code").status_code == code


def test_custom_content_type_preserved(client, app, fw):
    @app.route("/csv")
    def csv():
        resp = fw.make_response("a,b,c")
        resp.headers["Content-Type"] = "text/csv"
        return resp
    assert client.get("/csv").headers["Content-Type"] == "text/csv"


def test_empty_body_allowed(client, app):
    @app.route("/empty")
    def empty():
        return "", 204
    r = client.get("/empty")
    assert r.status_code == 204 and r.data == b""


def test_redirect_helper(client, app, fw):
    @app.route("/go")
    def go():
        return fw.redirect("/target")
    r = client.get("/go")
    assert r.status_code in (301, 302) and r.headers["Location"].endswith("/target")


def test_abort_produces_error_response(client, app, fw):
    @app.route("/ab")
    def ab():
        fw.abort(403)
    assert client.get("/ab").status_code == 403


def test_bytes_body(client, app, fw):
    @app.route("/by")
    def by():
        return fw.Response(b"\x00\x01\x02", mimetype="application/octet-stream")
    assert client.get("/by").data == b"\x00\x01\x02"


def test_response_set_cookie(client, app, fw):
    @app.route("/setc")
    def setc():
        resp = fw.make_response("x")
        resp.set_cookie("token", "xyz")
        return resp
    assert "token=xyz" in client.get("/setc").headers.get("Set-Cookie", "")


def test_content_length_header(client, app):
    @app.route("/cl")
    def cl():
        return "12345"
    assert client.get("/cl").headers.get("Content-Length") == "5"
