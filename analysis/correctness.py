"""RQ1 functional correctness: run an oracle pytest suite against a subject.

The oracle suites (120 Flask cases, 85 Django cases) live under ``oracle/`` and
import the system-under-test through the canonical name ``sut`` — the runner
puts the subject's source root on ``PYTHONPATH`` and exports ``SUT_IMPORT`` (the
subject's top-level package) so a shared ``conftest.py`` can alias it to ``sut``.

Results are parsed from a JUnit XML report and bucketed into the paper's
behavioural categories by the test file stem (e.g. ``test_app_context.py`` ->
"App Context"). Runs in a hermetic pytest invocation per subject.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from . import common

ORACLE_ROOT = common.REPO_ROOT / "oracle"

# Map oracle test-file stem -> human-readable category label (paper §3.3).
CATEGORY_LABELS = {
    "test_url_routing": "URL Routing",
    "test_request_handling": "Request Handling",
    "test_response_rendering": "Response Rendering",
    "test_templating": "Templating",
    "test_app_context": "App Context",
    "test_blueprints": "Blueprints",
    # Django
    "test_url_resolution": "URL Resolution",
    "test_request_object": "Request Object",
    "test_view_dispatch": "View Dispatch",
    "test_response_handling": "Response Handling",
    "test_class_based_views": "Class-Based Views",
}


def _sut_import(subject: common.Subject) -> tuple[str, Path]:
    """Resolve (import_name, sys.path entry) for the system-under-test.

    If the subject root is itself a package (has ``__init__.py``), the import
    name is the root's name and the path entry is its *parent* — never the
    package dir itself, which would shadow stdlib modules of the same name
    (e.g. flask/typing.py vs. stdlib typing). Otherwise the root is a container
    (a ``src/`` dir); the import name is its single child package and the path
    entry is the root.
    """
    root = subject.root
    if (root / "__init__.py").exists():
        return root.name, root.parent
    pkgs = [p for p in root.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()]
    if len(pkgs) == 1:
        return pkgs[0].name, root
    return root.name, root.parent


def _run_pytest(subject: common.Subject, junit_path: Path) -> subprocess.CompletedProcess:
    oracle_dir = ORACLE_ROOT / subject.oracle
    import_name, path_entry = _sut_import(subject)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(path_entry) + os.pathsep + env.get("PYTHONPATH", "")
    env["SUT_IMPORT"] = import_name
    cmd = [sys.executable, "-m", "pytest", str(oracle_dir), "-q",
           f"--junitxml={junit_path}", "-p", "no:cacheprovider"]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _category_for(testcase: ET.Element) -> str:
    # Prefer the `file` attribute (a path) when present; else the dotted
    # `classname`, whose final segment is the test module name.
    filename = testcase.get("file")
    if filename:
        stem = Path(filename).stem
    else:
        classname = testcase.get("classname", "")
        stem = classname.rsplit(".", 1)[-1] if classname else ""
    return CATEGORY_LABELS.get(stem, stem or "uncategorized")


def _parse_junit(junit_path: Path) -> dict:
    tree = ET.parse(junit_path)
    root = tree.getroot()
    suites = root.findall("testsuite") or [root]

    categories: dict[str, dict[str, int]] = {}
    total = passed = 0
    for suite in suites:
        for case in suite.findall("testcase"):
            total += 1
            cat = _category_for(case)
            bucket = categories.setdefault(cat, {"n": 0, "passed": 0})
            bucket["n"] += 1
            failed = case.find("failure") is not None or case.find("error") is not None
            skipped = case.find("skipped") is not None
            if not failed and not skipped:
                bucket["passed"] += 1
                passed += 1
    return {"total": total, "passed": passed, "categories": categories}


def analyze(subject: common.Subject) -> dict:
    junit_path = common.RESULTS_DIR / "correctness" / f"{subject.id}.junit.xml"
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _run_pytest(subject, junit_path)
    if not junit_path.exists():
        raise RuntimeError(
            f"pytest produced no JUnit report for {subject.id}:\n{proc.stderr[-2000:]}")
    parsed = _parse_junit(junit_path)
    cats = {
        label: {
            "n": c["n"],
            "passed": c["passed"],
            "pass_rate": common.pct(c["passed"], c["n"]),
        }
        for label, c in sorted(parsed["categories"].items())
    }
    return {
        "subject": subject.id,
        "label": subject.label,
        "oracle": subject.oracle,
        "total": parsed["total"],
        "passed": parsed["passed"],
        "pass_rate": common.pct(parsed["passed"], parsed["total"]),
        "categories": cats,
    }


def run(subject_ids: list[str] | None = None) -> None:
    for subject in common.load_subjects(subject_ids):
        if not subject.is_present():
            print(f"[correctness] SKIP {subject.id}: snapshot not present")
            continue
        if not subject.oracle:
            print(f"[correctness] SKIP {subject.id}: structural reference only "
                  f"(no oracle)")
            continue
        if not (ORACLE_ROOT / subject.oracle).exists():
            print(f"[correctness] SKIP {subject.id}: oracle '{subject.oracle}' not found")
            continue
        try:
            payload = analyze(subject)
        except RuntimeError as e:
            print(f"[correctness] SKIP {subject.id}: {e}")
            continue
        common.write_result("correctness", subject.id, payload)
        print(f"[correctness] {subject.id}: {payload['passed']}/{payload['total']} "
              f"({payload['pass_rate']}%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="*", default=None)
    args = ap.parse_args()
    run(args.subjects)
