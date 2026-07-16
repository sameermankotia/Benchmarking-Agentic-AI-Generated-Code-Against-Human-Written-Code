"""URL Resolution — 22 oracle cases (paper §3.3.2).

URL pattern matching, converters, resolve()/reverse(), and include().
"""

from __future__ import annotations

import pytest


def _view(request, **kw):
    from django.http import HttpResponse
    return HttpResponse("ok")


@pytest.fixture
def urls(dj):
    from django.urls import path, re_path
    return path, re_path


def test_path_basic_match(dj, urls):
    from django.urls import resolve, set_urlconf
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc1")
    mod.urlpatterns = [path("home/", _view, name="home")]
    set_urlconf(None)
    match = resolve("/home/", urlconf=mod)
    assert match.url_name == "home"


def test_path_no_match_raises(dj, urls):
    from django.urls import resolve, Resolver404
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc2")
    mod.urlpatterns = [path("home/", _view, name="home")]
    with pytest.raises(Resolver404):
        resolve("/nope/", urlconf=mod)


@pytest.mark.parametrize("url,expected", [
    ("/u/42/", 42),
    ("/u/0/", 0),
    ("/u/999/", 999),
])
def test_int_converter(dj, urls, url, expected):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc3")
    mod.urlpatterns = [path("u/<int:pk>/", _view, name="u")]
    match = resolve(url, urlconf=mod)
    assert match.kwargs["pk"] == expected


def test_int_converter_rejects_non_digit(dj, urls):
    from django.urls import resolve, Resolver404
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc4")
    mod.urlpatterns = [path("u/<int:pk>/", _view)]
    with pytest.raises(Resolver404):
        resolve("/u/abc/", urlconf=mod)


def test_str_converter_excludes_slash(dj, urls):
    from django.urls import resolve, Resolver404
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc5")
    mod.urlpatterns = [path("s/<str:v>/", _view)]
    with pytest.raises(Resolver404):
        resolve("/s/a/b/", urlconf=mod)


def test_slug_converter(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc6")
    mod.urlpatterns = [path("post/<slug:s>/", _view)]
    assert resolve("/post/hello-world/", urlconf=mod).kwargs["s"] == "hello-world"


def test_path_converter_allows_slash(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc7")
    mod.urlpatterns = [path("f/<path:p>/", _view)]
    assert resolve("/f/a/b/c/", urlconf=mod).kwargs["p"] == "a/b/c"


def test_uuid_converter(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    import uuid
    path, _ = urls
    mod = ModuleType("uc8")
    mod.urlpatterns = [path("x/<uuid:u>/", _view)]
    u = uuid.uuid4()
    assert resolve(f"/x/{u}/", urlconf=mod).kwargs["u"] == u


def test_re_path_named_group(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    _, re_path = urls
    mod = ModuleType("uc9")
    mod.urlpatterns = [re_path(r"^y/(?P<year>[0-9]{4})/$", _view)]
    assert resolve("/y/2024/", urlconf=mod).kwargs["year"] == "2024"


def test_reverse_simple(dj, urls):
    from django.urls import reverse
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc10")
    mod.urlpatterns = [path("home/", _view, name="home")]
    assert reverse("home", urlconf=mod) == "/home/"


def test_reverse_with_args(dj, urls):
    from django.urls import reverse
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc11")
    mod.urlpatterns = [path("u/<int:pk>/", _view, name="u")]
    assert reverse("u", urlconf=mod, kwargs={"pk": 7}) == "/u/7/"


def test_include_prefixes_patterns(dj, urls):
    from django.urls import resolve, include
    from types import ModuleType
    path, _ = urls
    inner = ModuleType("inner")
    inner.urlpatterns = [path("leaf/", _view, name="leaf")]
    mod = ModuleType("uc12")
    mod.urlpatterns = [path("api/", include(inner))]
    assert resolve("/api/leaf/", urlconf=mod).url_name == "leaf"


def test_include_reverse(dj, urls):
    from django.urls import reverse, include
    from types import ModuleType
    path, _ = urls
    inner = ModuleType("inner2")
    inner.urlpatterns = [path("leaf/", _view, name="leaf")]
    mod = ModuleType("uc13")
    mod.urlpatterns = [path("api/", include(inner))]
    assert reverse("leaf", urlconf=mod) == "/api/leaf/"


def test_resolve_returns_func(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc14")
    mod.urlpatterns = [path("z/", _view, name="z")]
    assert resolve("/z/", urlconf=mod).func is _view


def test_multiple_patterns_first_match(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    def other(r, **k):
        return None
    mod = ModuleType("uc15")
    mod.urlpatterns = [path("a/", _view, name="a"), path("b/", other, name="b")]
    assert resolve("/b/", urlconf=mod).url_name == "b"


def test_empty_path_root(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc16")
    mod.urlpatterns = [path("", _view, name="root")]
    assert resolve("/", urlconf=mod).url_name == "root"


def test_kwargs_passed_through(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc17")
    mod.urlpatterns = [path("k/", _view, {"extra": "v"}, name="k")]
    assert resolve("/k/", urlconf=mod).kwargs["extra"] == "v"


def test_two_converters(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc18")
    mod.urlpatterns = [path("p/<int:y>/<slug:s>/", _view)]
    m = resolve("/p/2024/my-post/", urlconf=mod)
    assert m.kwargs == {"y": 2024, "s": "my-post"}


def test_reverse_nonexistent_raises(dj, urls):
    from django.urls import reverse, NoReverseMatch
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc19")
    mod.urlpatterns = [path("home/", _view, name="home")]
    with pytest.raises(NoReverseMatch):
        reverse("missing", urlconf=mod)


def test_app_name_namespacing(dj, urls):
    from django.urls import resolve, include
    from types import ModuleType
    path, _ = urls
    inner = ModuleType("ns_inner")
    inner.app_name = "myapp"
    inner.urlpatterns = [path("x/", _view, name="x")]
    mod = ModuleType("uc20")
    mod.urlpatterns = [path("m/", include(inner))]
    assert resolve("/m/x/", urlconf=mod).namespace == "myapp"


def test_trailing_slash_significant(dj, urls):
    from django.urls import resolve, Resolver404
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc21")
    mod.urlpatterns = [path("t/", _view)]
    with pytest.raises(Resolver404):
        resolve("/t", urlconf=mod)


def test_resolvermatch_route_attr(dj, urls):
    from django.urls import resolve
    from types import ModuleType
    path, _ = urls
    mod = ModuleType("uc22")
    mod.urlpatterns = [path("u/<int:pk>/", _view, name="u")]
    assert "pk" in resolve("/u/1/", urlconf=mod).route
