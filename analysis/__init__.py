"""Agentic-vs-human benchmark analysis harness.

Each module in this package computes one dimension of the study and writes a
per-subject JSON blob to ``results/<dimension>/<subject_id>.json``.
``aggregate.py`` reads those blobs and renders the paper tables as CSV, and
``paper_numbers.py`` aggregates them into the single figure set the paper
quotes (``results/paper_numbers.json``).
"""

__version__ = "1.0.0"
