"""Tests for scripts/pytest_k_expr.py.

Guards the exact bug that false-failed every multi-language Weblate PR: the
changed-language list must become a valid pytest ``-k`` OR-expression
("ca or sq"), never a space-joined string ("ca sq") which pytest rejects with
exit 4. The last test exercises the CLI the workflow actually invokes and feeds
the result to a real ``pytest --co`` so the expression is proven acceptable, not
just string-equal.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "pytest_k_expr.py"
_spec = importlib.util.spec_from_file_location("pytest_k_expr", SCRIPT)
pytest_k_expr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pytest_k_expr)
build_k_expr = pytest_k_expr.build_k_expr


def test_two_languages_join_with_or():
    # The regression: must be "ca or sq", NOT "ca sq".
    assert build_k_expr(["ca", "sq"]) == "ca or sq"


def test_three_languages():
    assert build_k_expr(["de", "es", "fr"]) == "de or es or fr"


def test_single_language_has_no_operator():
    assert build_k_expr(["ca"]) == "ca"


def test_single_whitespace_joined_argument():
    # The workflow may pass the whole list as one string with a trailing space.
    assert build_k_expr(["ca sq "]) == "ca or sq"


def test_empty_yields_empty_expression():
    assert build_k_expr([]) == ""
    assert build_k_expr([""]) == ""
    assert build_k_expr(["   "]) == ""


def test_dedupes_preserving_order():
    assert build_k_expr(["ca", "sq", "ca"]) == "ca or sq"


def test_cli_output_is_accepted_by_pytest():
    # The CLI the workflow calls: `python scripts/pytest_k_expr.py $LANGS`.
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "ca", "sq"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert out == "ca or sq"
    # And a real pytest must accept that -k expression (collection only).
    po_tests = Path(__file__).resolve().parent / "test_po_files.py"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--co", "-q", "-k", out, str(po_tests)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
