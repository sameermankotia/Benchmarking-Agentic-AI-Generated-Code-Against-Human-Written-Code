"""Class-Based Views — 10 oracle cases (paper §3.3.2).

View.as_view(), dispatch, HTTP-method routing, and http_method_not_allowed.
"""

from __future__ import annotations

import pytest


def test_view_as_view_get(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request):
            return HttpResponse("got")
    assert V.as_view()(rf.get("/")).content == b"got"


def test_view_as_view_post(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def post(self, request):
            return HttpResponse("posted")
    assert V.as_view()(rf.post("/")).content == b"posted"


def test_method_not_allowed_405(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request):
            return HttpResponse("ok")
    assert V.as_view()(rf.post("/")).status_code == 405


def test_allow_header_lists_methods(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request):
            return HttpResponse("ok")

        def post(self, request):
            return HttpResponse("ok")
    resp = V.as_view()(rf.delete("/"))
    allow = resp.get("Allow", "")
    assert "GET" in allow and "POST" in allow


def test_dispatch_routes_by_method(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request):
            return HttpResponse("G")

        def put(self, request):
            return HttpResponse("P")
    view = V.as_view()
    assert view(rf.get("/")).content == b"G"
    assert view(rf.put("/")).content == b"P"


def test_view_receives_kwargs(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request, pk):
            return HttpResponse(str(pk))
    assert V.as_view()(rf.get("/"), pk=7).content == b"7"


def test_view_stores_kwargs_attr(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request, **kwargs):
            return HttpResponse(str(self.kwargs.get("pk")))
    assert V.as_view()(rf.get("/"), pk=3).content == b"3"


def test_view_initkwargs_rejects_bad(dj):
    from django.views import View

    class V(View):
        def get(self, request):
            return None
    with pytest.raises(TypeError):
        V.as_view(nonexistent=1)


def test_http_method_names_default(dj):
    from django.views import View
    assert "get" in View.http_method_names and "post" in View.http_method_names


def test_head_falls_back_to_get(rf, dj):
    from django.http import HttpResponse
    from django.views import View

    class V(View):
        def get(self, request):
            return HttpResponse("body")
    # HEAD is allowed when GET is defined; status must be 200.
    assert V.as_view()(rf.head("/")).status_code == 200
