"""Shared oracle fixtures.

Every oracle test imports the system-under-test through the canonical name
``sut``. The correctness runner sets the ``SUT_IMPORT`` environment variable to
the subject's top-level package and puts its source root on ``PYTHONPATH``; this
conftest aliases that package to ``sut`` so a single oracle suite runs unchanged
against Flask, the SWE-agent framework, the OpenHands framework, and Django.

Usage inside an oracle test:

    from conftest import sut          # the subject's top package
    app = sut.Application()           # or Flask(), etc., per the spec's API

Because API surface differs across subjects, oracle tests assert on documented
*behaviour* (from the written specification), not on implementation-specific
symbols. See paper §3.3.
"""

from __future__ import annotations

import importlib
import os

import pytest

_SUT_NAME = os.environ.get("SUT_IMPORT")


def _load_sut():
    if not _SUT_NAME:
        pytest.skip("SUT_IMPORT not set; run oracle via analysis.correctness")
    try:
        return importlib.import_module(_SUT_NAME)
    except Exception as e:  # noqa: BLE001 - report import failure as a skip
        pytest.skip(f"cannot import system-under-test '{_SUT_NAME}': {e}")


# Importable module-level handle (tests do `from conftest import sut`).
try:
    sut = importlib.import_module(_SUT_NAME) if _SUT_NAME else None
except Exception:
    sut = None


@pytest.fixture(scope="session")
def sut_module():
    """Session-scoped handle to the imported system-under-test."""
    return _load_sut()
