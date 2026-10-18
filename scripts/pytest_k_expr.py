#!/usr/bin/env python3
"""Build the pytest ``-k`` expression for validate-pr.yml's changed-language filter.

validate-pr.yml runs ``tests/test_po_files.py`` for only the languages a PR
actually changed, so a PR is never failed for a language it did not touch. The
filter is an OR of the language codes: ``["ca", "sq"] -> "ca or sq"``.

This used to live inline in the workflow as::

    K_EXPR=$(echo "$LANGS" | tr ' ' '\\n' | grep -v '^$' | paste -sd ' or ')

which was wrong: ``paste -d`` takes a list of SINGLE-character delimiters used
cyclically, so ``-sd ' or '`` joined the codes with a single space and produced
an invalid pytest ``-k`` ("ca sq" -> exit 4) on every PR touching 2+ languages.
A one-character paste happens to work, so single-language PRs passed and the bug
stayed hidden. It is kept here, unit-tested (tests/test_pytest_k_expr.py), so
that class of failure cannot silently come back.

Usage, from the workflow (``$LANGS`` unquoted so each code is its own argv, but a
single whitespace-joined string works too)::

    K_EXPR=$(python scripts/pytest_k_expr.py $LANGS)
    if [ -z "$K_EXPR" ]; then
      python -m pytest tests/test_po_files.py -q            # no locale changes
    else
      python -m pytest tests/test_po_files.py -k "$K_EXPR" -q
    fi
"""
from __future__ import annotations

import sys


def build_k_expr(langs: list[str]) -> str:
    """Return a pytest ``-k`` OR-expression for ``langs``.

    ``langs`` items may each be a single code or a whitespace-separated group.
    Blanks are dropped and order-preserving de-duplication is applied. Returns
    "" when there are no codes (the caller then runs the full suite).
    """
    codes: list[str] = []
    seen: set[str] = set()
    for item in langs:
        for code in item.split():
            if code and code not in seen:
                seen.add(code)
                codes.append(code)
    return " or ".join(codes)


def main(argv: list[str]) -> int:
    print(build_k_expr(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
