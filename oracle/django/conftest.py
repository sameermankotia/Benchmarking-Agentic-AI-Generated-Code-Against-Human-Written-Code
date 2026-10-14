"""Django-pair oracle fixtures.

The Django-pair specification covers URL resolution, request-object behaviour,
view dispatch, response handling, and class-based views. As in the Flask pair,
the suite constructs a subject through a small declared surface and then drives
it over WSGI, so no behavioural assertion names a Django symbol.

The declared surface for this pair is four roles:

* ``url_pattern``   -- declare one URL pattern (Django: ``urls.path``)
* ``wsgi_handler``  -- build a WSGI application (Django: ``WSGIHandler``)
* ``response_class``-- construct a response (Django: ``http.HttpResponse``)
* ``view_base``     -- base class for class-based views (Django: ``views.View``)

Each is resolved from the subject's own module tree, with the conventional
Django-shaped locations tried first. A subject that wires these differently
declares them in ``subjects/subjects.json`` under its ``api_map``; nothing
below hard-imports ``django``.
"""

from __future__ import annotations

import importlib
import sys
import uuid
from types import ModuleType

import pytest

import wsgi as wsgi_driver


class RoleUnresolvedError(Exception):
    """A Django-pair construction role has no counterpart on the subject."""


def _submodule(root, dotted: str):
    """``_submodule(sut, "core.handlers.wsgi")`` without importing by literal name."""
    try:
        return importlib.import_module(f"{root.__name__}.{dotted}")
    except Exception:                                  # noqa: BLE001
        return None


def _first_attr(root, paths: tuple[str, ...]):
    """First resolvable ``dotted.path:attr`` among `paths`."""
    for spec in paths:
        dotted, _, attr = spec.rpartition(".")
        holder = _submodule(root, dotted) if dotted else root
        if holder is not None and hasattr(holder, attr):
            return getattr(holder, attr)
    return None


@pytest.fixture(scope="session")
def dj(api, sut_module):
    """The configured subject.

    A Django-shaped subject needs its settings populated before most of its
    symbols can be imported, so the oracle supplies a minimal in-memory
    configuration: templating enabled, and no installed applications,
    database, or middleware.
    """
    settings = _first_attr(sut_module, ("conf.settings", "settings"))
    if settings is None:
        # A subject is not required to have a settings object. The
        # specification says nothing about configuration, and an
        # implementation that wires URL patterns directly into its WSGI
        # application needs none. Skipping here would have made every such
        # subject unscoreable.
        return sut_module
    if not getattr(settings, "configured", False):
        base = dict(
            DEBUG=True,
            SECRET_KEY="oracle-key-not-secret",
            ALLOWED_HOSTS=["*"],
            ROOT_URLCONF=None,
            DATABASES={},
            INSTALLED_APPS=[],
            MIDDLEWARE=[],
            USE_TZ=True,
        )
        # A template backend path is the one subject-specific string here, so
        # it is derived from the subject's own package name and the whole
        # TEMPLATES block is dropped if the subject does not accept it.
        backend = (f"{sut_module.__name__}.template.backends."
                   f"{sut_module.__name__}.DjangoTemplates")
        try:
            settings.configure(TEMPLATES=[{
                "BACKEND": backend,
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {},
            }], **base)
        except Exception:                              # noqa: BLE001
            settings.configure(**base)
        setup = getattr(sut_module, "setup", None)
        if setup is not None:
            setup()
    return sut_module


@pytest.fixture
def response_class(api, dj):
    """The subject's response class."""
    cls = _first_attr(dj, ("http.HttpResponse", "http.Response", "HttpResponse",
                           "Response"))
    if cls is None:
        pytest.skip("cannot resolve the response role on this subject")
    return cls


@pytest.fixture
def set_header():
    """Set one response header, however this subject allows it.

    The specification requires a response object carrying headers but fixes no
    API for setting them. Django's mapping style (``resp[name] = value``) is a
    convention, not a requirement, so an implementation offering only a
    ``headers`` mapping must not be failed for it.
    """
    def _set(resp, name, value):
        try:
            resp[name] = value
            return
        except (TypeError, AttributeError):
            pass
        headers = getattr(resp, "headers", None)
        if headers is not None:
            try:
                headers[name] = value
                return
            except (TypeError, AttributeError):
                pass
        for method in ("set_header", "add_header", "setdefault"):
            fn = getattr(resp, method, None)
            if callable(fn):
                fn(name, value)
                return
        raise AssertionError(
            f"{type(resp).__name__} offers no way to set a response header: "
            f"not item assignment, not a .headers mapping, not set_header()")
    return _set


@pytest.fixture
def view_base(api, dj):
    """The subject's class-based-view base class."""
    cls = _first_attr(dj, ("views.View", "views.generic.View", "View"))
    if cls is None:
        pytest.skip("cannot resolve the class-based-view role on this subject")
    return cls


@pytest.fixture
def pattern(api, dj, _pattern_prefix):
    """Declare one URL pattern: ``pattern("items/<int:pk>", view)``.

    The route string is written without a leading slash, Django's convention.
    An implementation may instead expect one, so the detected prefix for this
    subject (see `_pattern_prefix`) is applied here and the test bodies stay
    convention-free.
    """
    fn = _first_attr(dj, ("urls.path", "urls.url", "urls.route", "path"))
    if fn is None:
        pytest.skip("cannot resolve the URL-pattern role on this subject")

    def _pattern(route, *args, **kwargs):
        return fn(_pattern_prefix + route, *args, **kwargs)
    return _pattern


@pytest.fixture(scope="session")
def _pattern_prefix(dj, _serve_raw):
    """Whether this subject wants URL patterns with a leading slash.

    The specification requires URL resolution but fixes no spelling for a
    route, and implementations disagree: one subject's WSGI layer hands the
    raw PATH_INFO (which starts with "/") to a resolver that strips nothing,
    so only patterns written "/v/" ever match. Hardcoding Django's slashless
    convention scored that framework at 12.5% while it worked correctly under
    its own convention.

    Detected once per session with a throwaway route, so a single probe
    settles it and no test body carries the question.
    """
    path_fn = _first_attr(dj, ("urls.path", "urls.url", "urls.route", "path"))
    response = _first_attr(dj, ("http.HttpResponse", "http.Response",
                                "HttpResponse", "Response"))
    if path_fn is None or response is None:
        return ""

    def probe(prefix):
        def view(request, **_):
            return response("probe-ok")
        try:
            result = _serve_raw([path_fn(prefix + "oracle-probe/", view)],
                                "GET", "/oracle-probe/")
            return result.status_code == 200
        except Exception:                                  # noqa: BLE001
            return False

    if probe(""):
        return ""
    if probe("/"):
        return "/"
    return ""


@pytest.fixture
def re_pattern(api, dj):
    """Declare one regex URL pattern."""
    fn = _first_attr(dj, ("urls.re_path", "urls.url", "re_path"))
    if fn is None:
        pytest.skip("cannot resolve the regex-URL-pattern role on this subject")
    return fn


def _make_serve(dj):
    """Yield a ``call(patterns, method, path, **kwargs)`` for this subject.

    Each call builds a WSGI application over the given URL patterns, however
    the subject wires them, and drives it over WSGI. Shared by the per-test
    `serve` fixture and the session-scoped convention probe.
    """
    settings = _first_attr(dj, ("conf.settings", "settings"))
    handler_factory = _first_attr(dj, (
        "core.handlers.wsgi.WSGIHandler", "WSGIHandler",
        "core.wsgi.get_wsgi_application", "get_wsgi_application",
        "wsgi.get_wsgi_application", "wsgi.WSGIApplication",
        "wsgi.WSGIHandler", "WSGIApplication"))
    if handler_factory is None:
        pytest.skip("cannot resolve the WSGI-handler role on this subject")

    created: list[str] = []

    def _build(patterns):
        """Two wirings are accepted, because the specification fixes neither:

        1. the factory takes the URL patterns directly, which is what an
           implementation written from the specification alone tends to do;
        2. the patterns are published through a settings module the factory
           reads, which is Django's own arrangement.

        Only a signature rejection falls through to the second, so a genuine
        error inside the subject is not mistaken for a wiring mismatch.
        """
        try:
            return handler_factory(list(patterns))
        except TypeError:
            pass
        if settings is None:
            raise RoleUnresolvedError(
                "this subject's WSGI factory did not accept URL patterns and "
                "it exposes no settings module to publish them through")
        name = f"oracle_urlconf_{uuid.uuid4().hex}"
        module = ModuleType(name)
        module.urlpatterns = list(patterns)
        sys.modules[name] = module
        created.append(name)
        settings.ROOT_URLCONF = name
        return handler_factory()

    def _serve(patterns, method="GET", path="/", **kwargs):
        return wsgi_driver.call(_build(patterns), method, path, **kwargs)

    yield _serve

    for name in created:
        sys.modules.pop(name, None)


@pytest.fixture(scope="session")
def _serve_raw(dj):
    """`serve` without the per-test lifetime, for the convention probe."""
    yield from _make_serve(dj)


@pytest.fixture
def serve(api, dj):
    """Build a WSGI application from URL patterns and call it.

    Each call gets a freshly named URL configuration where the subject uses
    one, so its resolver cache cannot carry state between tests.
    """
    yield from _make_serve(dj)
