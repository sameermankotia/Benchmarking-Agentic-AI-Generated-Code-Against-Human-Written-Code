"""View Dispatch — 20 oracle cases (paper §3.3.2).

Function-view invocation, argument passing, decorators, and method handling.
"""

from __future__ import annotations

import pytest


def test_function_view_called(rf, dj):
    from django.http import HttpResponse

    def view(request):
        return HttpResponse("hi")
    assert view(rf.get("/")).content == b"hi"


def test_view_receives_url_kwargs(rf, dj):
    from django.http import HttpResponse

    def view(request, pk):
        return HttpResponse(str(pk))
    assert view(rf.get("/"), pk=5).content == b"5"


def test_view_reads_get_param(rf, dj):
    from django.http import HttpResponse

    def view(request):
        return HttpResponse(request.GET.get("q", ""))
    assert view(rf.get("/", {"q": "term"})).content == b"term"


def test_view_reads_post_data(rf, dj):
    from django.http import HttpResponse

    def view(request):
        return HttpResponse(request.POST.get("f", ""))
    assert view(rf.post("/", {"f": "posted"})).content == b"posted"


@pytest.mark.parametrize("method,expected", [
    ("get", b"GET"), ("post", b"POST"), ("put", b"PUT"),
])
def test_view_branches_on_method(rf, dj, method, expected):
    from django.http import HttpResponse

    def view(request):
        return HttpResponse(request.method)
    assert view(getattr(rf, method)("/")).content == expected


def test_require_http_methods_allows(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_http_methods

    @require_http_methods(["GET"])
    def view(request):
        return HttpResponse("ok")
    assert view(rf.get("/")).status_code == 200


def test_require_http_methods_rejects(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_http_methods

    @require_http_methods(["GET"])
    def view(request):
        return HttpResponse("ok")
    assert view(rf.post("/")).status_code == 405


def test_require_POST_decorator(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_POST

    @require_POST
    def view(request):
        return HttpResponse("ok")
    assert view(rf.post("/")).status_code == 200
    assert view(rf.get("/")).status_code == 405


def test_require_GET_decorator(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_GET

    @require_GET
    def view(request):
        return HttpResponse("ok")
    assert view(rf.get("/")).status_code == 200
    assert view(rf.post("/")).status_code == 405


def test_view_returns_404(rf, dj):
    from django.http import Http404, HttpResponse

    def view(request):
        raise Http404("nope")
    with pytest.raises(Http404):
        view(rf.get("/"))


def test_get_object_or_404_helper_exists(dj):
    from django.shortcuts import get_object_or_404
    assert callable(get_object_or_404)


def test_view_multiple_kwargs(rf, dj):
    from django.http import HttpResponse

    def view(request, a, b):
        return HttpResponse(f"{a}-{b}")
    assert view(rf.get("/"), a="x", b="y").content == b"x-y"


def test_decorator_preserves_kwargs(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_GET

    @require_GET
    def view(request, pk):
        return HttpResponse(str(pk))
    assert view(rf.get("/"), pk=9).content == b"9"


def test_csrf_exempt_decorator(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt

    @csrf_exempt
    def view(request):
        return HttpResponse("ok")
    assert getattr(view, "csrf_exempt", False) is True


def test_view_default_400_on_bad(rf, dj):
    from django.http import HttpResponseBadRequest

    def view(request):
        return HttpResponseBadRequest("bad")
    assert view(rf.get("/")).status_code == 400


def test_view_sets_custom_header(rf, dj):
    from django.http import HttpResponse

    def view(request):
        resp = HttpResponse("x")
        resp["X-Custom"] = "1"
        return resp
    assert view(rf.get("/"))["X-Custom"] == "1"


def test_view_conditional_get_post(rf, dj):
    from django.http import HttpResponse

    def view(request):
        if request.method == "POST":
            return HttpResponse("created", status=201)
        return HttpResponse("listed")
    assert view(rf.post("/")).status_code == 201
    assert view(rf.get("/")).content == b"listed"


def test_gzip_decorator_importable(dj):
    from django.views.decorators.gzip import gzip_page
    assert callable(gzip_page)


def test_cache_decorator_importable(dj):
    from django.views.decorators.cache import never_cache
    assert callable(never_cache)


def test_view_405_lists_allow_header(rf, dj):
    from django.http import HttpResponse
    from django.views.decorators.http import require_POST

    @require_POST
    def view(request):
        return HttpResponse("ok")
    resp = view(rf.get("/"))
    assert "POST" in resp.get("Allow", "")
