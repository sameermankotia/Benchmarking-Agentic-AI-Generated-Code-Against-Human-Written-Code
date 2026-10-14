"""Class-Based Views — oracle cases for the Django-pair specification.

The base class and its request-entry point are resolved roles; everything
asserted is the WSGI response produced by routing a pattern to the class.
"""

from __future__ import annotations

import pytest


def _as_view(cls):
    """The pattern-ready callable for a class-based view.

    Conventionally a classmethod on the view class; resolved rather than
    assumed so a subject may name it differently.
    """
    for name in ("as_view", "as_callable", "view", "dispatch_view"):
        if hasattr(cls, name):
            return getattr(cls, name)()
    pytest.skip(f"{cls!r} exposes no class-based-view entry point")


def test_class_based_view_handles_get(serve, pattern, response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class("got")
    assert b"got" in serve([pattern("v/", _as_view(V))], "GET", "/v/").body


def test_class_based_view_handles_post(serve, pattern, response_class, view_base):
    class V(view_base):
        def post(self, request, **_):
            return response_class("posted", status=201)
    result = serve([pattern("v/", _as_view(V))], "POST", "/v/")
    assert result.status_code == 201 and b"posted" in result.body


def test_dispatch_routes_by_method(serve, pattern, response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class("read")

        def post(self, request, **_):
            return response_class("wrote")
    patterns = [pattern("v/", _as_view(V))]
    assert b"read" in serve(patterns, "GET", "/v/").body
    assert b"wrote" in serve(patterns, "POST", "/v/").body


def test_unhandled_method_is_405(serve, pattern, response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class("read")
    result = serve([pattern("v/", _as_view(V))], "DELETE", "/v/")
    assert result.status_code == 405


def test_405_advertises_an_allow_header(serve, pattern, response_class,
                                        view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class("read")
    result = serve([pattern("v/", _as_view(V))], "POST", "/v/")
    assert result.status_code == 405 and "GET" in result.header("Allow")


def test_class_based_view_receives_captured_parameters(serve, pattern,
                                                       response_class,
                                                       view_base):
    class V(view_base):
        def get(self, request, **params):
            return response_class(params.get("name", ""))
    patterns = [pattern("u/<str:name>/", _as_view(V))]
    assert b"zoe" in serve(patterns, "GET", "/u/zoe/").body


def test_class_based_view_receives_the_request(api, serve, pattern,
                                               response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class(api.path(request))
    assert b"/v/" in serve([pattern("v/", _as_view(V))], "GET", "/v/").body


def test_head_falls_back_to_get(serve, pattern, response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            return response_class("head-ok")
    result = serve([pattern("v/", _as_view(V))], "HEAD", "/v/")
    assert result.status_code == 200


def test_class_based_view_instance_is_per_request(serve, pattern,
                                                  response_class, view_base):
    class V(view_base):
        def get(self, request, **_):
            seen = getattr(self, "marker", "fresh")
            self.marker = "used"
            return response_class(seen)
    patterns = [pattern("v/", _as_view(V))]
    assert b"fresh" in serve(patterns, "GET", "/v/").body
    assert b"fresh" in serve(patterns, "GET", "/v/").body


def test_two_class_based_views_dispatch_independently(serve, pattern,
                                                      response_class,
                                                      view_base):
    class A(view_base):
        def get(self, request, **_):
            return response_class("alpha")

    class B(view_base):
        def get(self, request, **_):
            return response_class("beta")
    patterns = [pattern("a/", _as_view(A)), pattern("b/", _as_view(B))]
    assert b"alpha" in serve(patterns, "GET", "/a/").body
    assert b"beta" in serve(patterns, "GET", "/b/").body
