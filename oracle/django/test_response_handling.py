"""Response Handling — 15 oracle cases (paper §3.3.2).

HttpResponse status/headers/body, JsonResponse, redirects, streaming.
"""

from __future__ import annotations

import json

import pytest


def test_response_default_200(dj):
    from django.http import HttpResponse
    assert HttpResponse("x").status_code == 200


def test_response_body(dj):
    from django.http import HttpResponse
    assert HttpResponse("body").content == b"body"


@pytest.mark.parametrize("code", [200, 201, 400, 404, 500])
def test_response_status_codes(dj, code):
    from django.http import HttpResponse
    assert HttpResponse("x", status=code).status_code == code


def test_response_content_type(dj):
    from django.http import HttpResponse
    resp = HttpResponse("x", content_type="text/plain")
    assert resp["Content-Type"] == "text/plain"


def test_response_default_content_type_html(dj):
    from django.http import HttpResponse
    assert "text/html" in HttpResponse("x")["Content-Type"]


def test_response_set_header(dj):
    from django.http import HttpResponse
    resp = HttpResponse("x")
    resp["X-Custom"] = "v"
    assert resp["X-Custom"] == "v"


def test_json_response(dj):
    from django.http import JsonResponse
    resp = JsonResponse({"a": 1})
    assert json.loads(resp.content) == {"a": 1}


def test_json_response_content_type(dj):
    from django.http import JsonResponse
    assert "application/json" in JsonResponse({})["Content-Type"]


def test_json_response_list_safe_false(dj):
    from django.http import JsonResponse
    resp = JsonResponse([1, 2, 3], safe=False)
    assert json.loads(resp.content) == [1, 2, 3]


def test_redirect_response(dj):
    from django.http import HttpResponseRedirect
    resp = HttpResponseRedirect("/target/")
    assert resp.status_code == 302 and resp["Location"] == "/target/"


def test_permanent_redirect(dj):
    from django.http import HttpResponsePermanentRedirect
    assert HttpResponsePermanentRedirect("/t/").status_code == 301


def test_not_found_response(dj):
    from django.http import HttpResponseNotFound
    assert HttpResponseNotFound("nope").status_code == 404


def test_response_set_cookie(dj):
    from django.http import HttpResponse
    resp = HttpResponse("x")
    resp.set_cookie("sid", "abc")
    assert resp.cookies["sid"].value == "abc"


def test_response_delete_cookie(dj):
    from django.http import HttpResponse
    resp = HttpResponse("x")
    resp.delete_cookie("sid")
    assert "sid" in resp.cookies


def test_streaming_response(dj):
    from django.http import StreamingHttpResponse
    resp = StreamingHttpResponse(iter(["a", "b", "c"]))
    assert b"".join(resp.streaming_content) == b"abc"
