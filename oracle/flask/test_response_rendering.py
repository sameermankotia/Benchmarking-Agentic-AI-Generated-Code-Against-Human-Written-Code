"""Response Rendering — oracle cases for specification area (3).

"response object with status code, headers, and body."

Responses are constructed through the resolved response role (`api.response`)
or returned as a plain string, and every assertion reads the WSGI status line,
response headers, or response body.
"""

from __future__ import annotations

import pytest


# --- Basic: a view's return value becomes a response ----------------------- #

def test_string_return_is_200(route, get):
    def view(**_):
        return "hello"
    route("/s")(view)
    assert get("/s").status_code == 200


def test_string_return_becomes_the_body(route, get):
    def view(**_):
        return "body-text"
    route("/s")(view)
    assert b"body-text" in get("/s").body


def test_response_has_a_content_type(route, get):
    def view(**_):
        return "typed"
    route("/t")(view)
    assert get("/t").header("Content-Type") != ""


def test_status_line_is_well_formed(route, get):
    def view(**_):
        return "ok"
    route("/w")(view)
    status = get("/w").status
    assert status[:3].isdigit() and len(status) > 4


def test_empty_body_is_allowed(route, get):
    def view(**_):
        return ""
    route("/e")(view)
    result = get("/e")
    assert result.status_code == 200 and result.body == b""


# --- Behavioural: status codes --------------------------------------------- #

@pytest.mark.parametrize("code", [200, 201, 202, 400, 404, 418, 500])
def test_response_status_code_is_honoured(api, route, get, code):
    def view(**_):
        return api.response("x", status=code)
    route("/code")(view)
    assert get("/code").status_code == code


def test_created_201_with_body(api, route, get):
    def view(**_):
        return api.response("made", status=201)
    route("/c")(view)
    result = get("/c")
    assert result.status_code == 201 and b"made" in result.body


def test_error_status_with_body(api, route, get):
    def view(**_):
        return api.response("nope", status=400)
    route("/b")(view)
    result = get("/b")
    assert result.status_code == 400 and b"nope" in result.body


# --- Behavioural: headers -------------------------------------------------- #

def test_response_custom_header(api, route, get):
    def view(**_):
        return api.response("h", headers={"X-Custom": "set"})
    route("/h")(view)
    assert get("/h").header("X-Custom") == "set"


def test_response_multiple_custom_headers(api, route, get):
    def view(**_):
        return api.response("h", headers={"X-One": "1", "X-Two": "2"})
    route("/hh")(view)
    result = get("/hh")
    assert result.header("X-One") == "1" and result.header("X-Two") == "2"


def test_response_explicit_content_type(api, route, get):
    def view(**_):
        return api.response("{}", headers={"Content-Type": "application/json"})
    route("/j")(view)
    assert "application/json" in get("/j").header("Content-Type")


def test_response_header_and_status_together(api, route, get):
    def view(**_):
        return api.response("both", status=503, headers={"X-Why": "test"})
    route("/bo")(view)
    result = get("/bo")
    assert result.status_code == 503 and result.header("X-Why") == "test"


# --- Behavioural: body ----------------------------------------------------- #

def test_response_object_carries_body(api, route, get):
    def view(**_):
        return api.response("carried")
    route("/cb")(view)
    assert b"carried" in get("/cb").body


def test_response_body_is_bytes_over_wsgi(api, route, get):
    def view(**_):
        return api.response("bytes-check")
    route("/by")(view)
    assert isinstance(get("/by").body, bytes)


def test_response_body_preserves_utf8(api, route, get):
    def view(**_):
        return api.response("caffè-ü")
    route("/u")(view)
    assert "caffè-ü" in get("/u").text


def test_response_content_length_matches_body(api, route, get):
    def view(**_):
        return api.response("1234567890")
    route("/cl")(view)
    result = get("/cl")
    declared = result.header("Content-Length")
    if declared:
        assert int(declared) == len(result.body)
    else:
        assert len(result.body) == 10


# --- Edge cases ------------------------------------------------------------ #

def test_distinct_routes_get_distinct_responses(api, route, get):
    def first(**_):
        return api.response("A", status=201)

    def second(**_):
        return api.response("B", status=202)
    route("/r1")(first)
    route("/r2")(second)
    r1, r2 = get("/r1"), get("/r2")
    assert (r1.status_code, r1.body) == (201, b"A")
    assert (r2.status_code, r2.body) == (202, b"B")


def test_response_is_regenerated_per_request(api, route, get):
    calls = {"n": 0}

    def view(**_):
        calls["n"] += 1
        return api.response(str(calls["n"]))
    route("/n")(view)
    assert get("/n").body == b"1"
    assert get("/n").body == b"2"
