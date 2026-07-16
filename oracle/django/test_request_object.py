"""Request Object — 18 oracle cases (paper §3.3.2).

HttpRequest attributes: method, path, GET/POST, headers, body, content type.
"""

from __future__ import annotations

import json

import pytest


def test_request_method_get(rf):
    assert rf.get("/x").method == "GET"


def test_request_method_post(rf):
    assert rf.post("/x").method == "POST"


@pytest.mark.parametrize("method", ["get", "post", "put", "delete", "patch"])
def test_request_methods(rf, method):
    req = getattr(rf, method)("/m")
    assert req.method == method.upper()


def test_request_path(rf):
    assert rf.get("/some/path/").path == "/some/path/"


def test_request_get_params(rf):
    req = rf.get("/x", {"a": "1", "b": "2"})
    assert req.GET.get("a") == "1" and req.GET.get("b") == "2"


def test_request_get_missing_default(rf):
    assert rf.get("/x").GET.get("missing", "d") == "d"


def test_request_get_multivalue(rf):
    req = rf.get("/x?n=1&n=2&n=3")
    assert req.GET.getlist("n") == ["1", "2", "3"]


def test_request_post_form(rf):
    req = rf.post("/x", {"field": "value"})
    assert req.POST.get("field") == "value"


def test_request_json_body(rf):
    req = rf.post("/x", data=json.dumps({"k": "v"}), content_type="application/json")
    assert json.loads(req.body)["k"] == "v"


def test_request_content_type(rf):
    req = rf.post("/x", data="{}", content_type="application/json")
    assert req.content_type == "application/json"


def test_request_custom_header(rf):
    req = rf.get("/x", headers={"x-test": "hello"})
    assert req.headers["X-Test"] == "hello"


def test_request_meta_populated(rf):
    req = rf.get("/x")
    assert "REQUEST_METHOD" in req.META


def test_request_query_string(rf):
    req = rf.get("/x?a=1&b=2")
    assert "a=1" in req.META["QUERY_STRING"]


def test_request_get_full_path(rf):
    req = rf.get("/x", {"q": "1"})
    assert req.get_full_path() == "/x?q=1"


def test_request_cookies(rf):
    rf.cookies["sid"] = "abc"
    req = rf.get("/x")
    assert req.COOKIES.get("sid") == "abc"


def test_request_body_bytes(rf):
    req = rf.post("/x", data=b"raw", content_type="application/octet-stream")
    assert req.body == b"raw"


def test_request_is_secure_false(rf):
    assert rf.get("/x").is_secure() is False


def test_request_scheme(rf):
    assert rf.get("/x").scheme in ("http", "https")
