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
        pytest.skip(
            f"subject {sut_module.__name__!r} exposes no settings object; "
            f"declare one via api_map if it is configured differently")
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
def view_base(api, dj):
    """The subject's class-based-view base class."""
    cls = _first_attr(dj, ("views.View", "views.generic.View", "View"))
    if cls is None:
        pytest.skip("cannot resolve the class-based-view role on this subject")
    return cls


@pytest.fixture
def pattern(api, dj):
    """Declare one URL pattern: ``pattern("items/<int:pk>", view)``."""
    fn = _first_attr(dj, ("urls.path", "urls.url", "urls.route", "path"))
    if fn is None:
        pytest.skip("cannot resolve the URL-pattern role on this subject")
    return fn


@pytest.fixture
def re_pattern(api, dj):
    """Declare one regex URL pattern."""
    fn = _first_attr(dj, ("urls.re_path", "urls.url", "re_path"))
    if fn is None:
        pytest.skip("cannot resolve the regex-URL-pattern role on this subject")
    return fn


@pytest.fixture
def serve(api, dj):
    """Build a WSGI application from URL patterns and call it.

    Returns ``call(patterns, method, path, **kwargs)``. Each call gets a fresh,
    uniquely named URL configuration so the subject's resolver cache cannot
    carry state between tests.
    """
    settings = _first_attr(dj, ("conf.settings", "settings"))
    handler_factory = _first_attr(dj, (
        "core.handlers.wsgi.WSGIHandler", "WSGIHandler",
        "core.wsgi.get_wsgi_application", "get_wsgi_application"))
    if handler_factory is None:
        pytest.skip("cannot resolve the WSGI-handler role on this subject")

    created: list[str] = []

    def _serve(patterns, method="GET", path="/", **kwargs):
        name = f"oracle_urlconf_{uuid.uuid4().hex}"
        module = ModuleType(name)
        module.urlpatterns = list(patterns)
        sys.modules[name] = module
        created.append(name)
        settings.ROOT_URLCONF = name
        app = handler_factory()
        return wsgi_driver.call(app, method, path, **kwargs)

    yield _serve

    for name in created:
        sys.modules.pop(name, None)
