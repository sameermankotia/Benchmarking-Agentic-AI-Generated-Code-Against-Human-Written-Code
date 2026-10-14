"""Shared oracle fixtures.

Every oracle test reaches the system under test through the canonical name
``sut``. The correctness runner sets the ``SUT_IMPORT`` environment variable to
the subject's top-level package and puts its source root on ``PYTHONPATH``;
this conftest imports that package and aliases it to ``sut`` so a single oracle
suite runs unchanged against Flask, the SWE-agent framework, the OpenHands
framework, and Django.

Two layers keep the suite independent of a subject's API names:

* ``oracle/api.py`` resolves the small set of specification-level roles needed
  to *construct* a subject (its application class, route registration,
  blueprint class, response class, template renderer), from an explicit
  per-subject ``api_map`` in the subject registry or from conventional
  candidate names.
* ``oracle/wsgi.py`` drives the constructed subject over its WSGI interface,
  which is the one interface the specification fixes, so every behavioural
  assertion is made on status, headers, and body rather than on a
  framework-specific test client.

Tests therefore assert on behaviour documented in the specification, never on
implementation-specific symbols. See the paper's oracle-construction
subsection.
"""

from __future__ import annotations

import importlib
import json
import os
import pathlib
import sys

import pytest

# Make `oracle/` importable regardless of pytest's rootdir, so the suites can
# `import wsgi` / `import api` wherever they are invoked from.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from api import Api                       # noqa: E402

_SUT_NAME = os.environ.get("SUT_IMPORT")


def _load_sut():
    if not _SUT_NAME:
        pytest.skip("SUT_IMPORT not set; run oracle via analysis.correctness")
    try:
        return importlib.import_module(_SUT_NAME)
    except Exception as e:  # noqa: BLE001 - report import failure as a skip
        pytest.skip(f"cannot import system-under-test '{_SUT_NAME}': {e}")


# Importable module-level handle (kept for tests that want the raw module).
try:
    sut = importlib.import_module(_SUT_NAME) if _SUT_NAME else None
except Exception:
    sut = None


def _api_map() -> dict:
    raw = os.environ.get("ORACLE_API_MAP", "").strip()
    if not raw:
        return {}
    try:
        return dict(json.loads(raw))
    except (ValueError, TypeError):
        return {}


@pytest.fixture(scope="session")
def sut_module():
    """Session-scoped handle to the imported system-under-test."""
    return _load_sut()


@pytest.fixture(scope="session")
def api(sut_module):
    """The subject's declared construction surface (see oracle/api.py)."""
    return Api(sut_module, _api_map())
