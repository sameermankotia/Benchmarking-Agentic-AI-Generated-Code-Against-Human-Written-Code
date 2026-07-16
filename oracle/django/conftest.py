"""Django-pair oracle fixtures.

Django's URL/view subsystem needs a configured settings module before import of
most symbols. We configure a minimal in-memory settings object once per session
and call ``django.setup()``. The system-under-test is reached through the
canonical ``sut`` handle (``django`` for the human baseline).

Tests assert on documented behaviour of the URL resolver, request/response
objects, and view dispatch (paper §3.3.2).
"""

from __future__ import annotations

import pytest


def _configure(sut):
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="oracle-key-not-secret",
            ALLOWED_HOSTS=["*"],
            ROOT_URLCONF=None,
            DATABASES={},
            INSTALLED_APPS=[],
            TEMPLATES=[{
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {},
            }],
            MIDDLEWARE=[],
            USE_TZ=True,
        )
        sut.setup()


@pytest.fixture(scope="session")
def dj(sut_module):
    _configure(sut_module)
    return sut_module


@pytest.fixture
def rf(dj):
    from django.test import RequestFactory
    return RequestFactory()
