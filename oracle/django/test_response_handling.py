"""Response Handling — oracle cases for the Django-pair specification.

Responses are built through the resolved response role and asserted on through
the WSGI status line, headers, and body.
"""

from __future__ import annotations

import pytest


# --- Basic ----------------------------------------------------------------- #

def test_response_default_status_is_200(serve, pattern, response_class):
    def view(request, **_):
        return response_class("ok")
    assert serve([pattern("r/", view)], "GET", "/r/").status_code == 200


def test_response_body_is_returned(serve, pattern, response_class):
    def view(request, **_):
        return response_class("body-text")
    assert b"body-text" in serve([pattern("r/", view)], "GET", "/r/").body


def test_response_has_a_content_type(serve, pattern, response_class):
    def view(request, **_):
        return response_class("typed")
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.header("Content-Type") != ""


def test_status_line_is_well_formed(serve, pattern, response_class):
    def view(request, **_):
        return response_class("ok")
    status = serve([pattern("r/", view)], "GET", "/r/").status
    assert status[:3].isdigit() and len(status) > 4


def test_empty_body_is_allowed(serve, pattern, response_class):
    def view(request, **_):
        return response_class("")
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.status_code == 200 and result.body == b""


# --- Status codes ---------------------------------------------------------- #

@pytest.mark.parametrize("code", [200, 201, 202, 400, 404, 418, 500])
def test_response_status_code_is_honoured(serve, pattern, response_class, code):
    def view(request, **_):
        return response_class("x", status=code)
    assert serve([pattern("r/", view)], "GET", "/r/").status_code == code


def test_created_201_with_body(serve, pattern, response_class):
    def view(request, **_):
        return response_class("made", status=201)
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.status_code == 201 and b"made" in result.body


def test_error_status_with_body(serve, pattern, response_class):
    def view(request, **_):
        return response_class("nope", status=400)
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.status_code == 400 and b"nope" in result.body


# --- Headers --------------------------------------------------------------- #

def test_response_custom_header(serve, pattern, response_class):
    def view(request, **_):
        resp = response_class("h")
        resp["X-Custom"] = "set"
        return resp
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.header("X-Custom") == "set"


def test_response_multiple_custom_headers(serve, pattern, response_class):
    def view(request, **_):
        resp = response_class("h")
        resp["X-One"], resp["X-Two"] = "1", "2"
        return resp
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.header("X-One") == "1" and result.header("X-Two") == "2"


def test_response_explicit_content_type(serve, pattern, response_class):
    def view(request, **_):
        return response_class("{}", content_type="application/json")
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert "application/json" in result.header("Content-Type")


def test_response_header_and_status_together(serve, pattern, response_class):
    def view(request, **_):
        resp = response_class("both", status=503)
        resp["X-Why"] = "test"
        return resp
    result = serve([pattern("r/", view)], "GET", "/r/")
    assert result.status_code == 503 and result.header("X-Why") == "test"


# --- Body ------------------------------------------------------------------ #

def test_response_body_is_bytes_over_wsgi(serve, pattern, response_class):
    def view(request, **_):
        return response_class("bytes-check")
    assert isinstance(serve([pattern("r/", view)], "GET", "/r/").body, bytes)


def test_response_body_preserves_utf8(serve, pattern, response_class):
    def view(request, **_):
        return response_class("caffè-ü")
    assert "caffè-ü" in serve([pattern("r/", view)], "GET", "/r/").text


def test_response_is_regenerated_per_request(serve, pattern, response_class):
    calls = {"n": 0}

    def view(request, **_):
        calls["n"] += 1
        return response_class(str(calls["n"]))
    patterns = [pattern("n/", view)]
    assert serve(patterns, "GET", "/n/").body == b"1"
    assert serve(patterns, "GET", "/n/").body == b"2"
