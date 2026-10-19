#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data integrity gate for the eight system-design CSVs (checks V1-V13).

Read-only: never writes to data/. Accumulates every error/warning found
across all files in one run instead of failing fast, so a single pass
surfaces the whole punch list. Exit 0 on no errors, 1 otherwise; warnings
never change the exit code. `--counts` is the only authorized source of
dataset row counts (see docs/code-standards.md).

Checks live in three modules by concern: validate_checks.py (structure: V1-V6,
V10), validate_anchors.py (cross-references: V7, V7s, V11), validate_colors.py
(colour: V8, V9, V11a/b).
"""

import argparse
import csv
import sys

import validate_checks as checks
from csv_config import CSV_CONFIG, domain_path, set_data_dir
from validate_anchors import check_anchors
from validate_colors import check_canvas, check_color_coverage, check_contrast


def _print_counts():
    total = 0
    for domain in CSV_CONFIG:
        path = domain_path(domain)
        count = len(list(csv.DictReader(open(path, encoding="utf-8")))) if path.exists() else 0
        total += count
        print(f"{domain}: {count} rows")
    print(f"TOTAL: {total} rows")


def _run_all_checks():
    errors, warnings = [], []
    for domain in CSV_CONFIG:
        header, rows = checks.read_rows(domain, errors)
        if not rows:
            continue
        checks.check_header(domain, header, errors)
        checks.check_keys(domain, rows, errors)
        checks.check_enums(domain, rows, errors)
        checks.check_required_cells(domain, rows, errors)
        checks.check_genres(domain, rows, errors)

    checks.check_fks(errors)
    check_anchors(warnings, errors)
    check_color_coverage(errors)
    check_contrast(errors)
    checks.check_runtime_consistency(errors)
    check_canvas(errors, warnings)
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the system-design CSV datasets")
    parser.add_argument("--counts", action="store_true", help="Print row counts per domain and exit")
    # Exists so the gate itself can be tested against a deliberately-broken copy of
    # the datasets without ever writing one into data/. Cross-reference targets
    # (templates/, references/) always resolve against the real skill root.
    parser.add_argument("--data-dir", default=None, metavar="DIR",
                        help="Validate CSVs in DIR instead of data/ (for testing the gate itself)")
    args = parser.parse_args(argv)

    if args.data_dir:
        set_data_dir(args.data_dir)

    if args.counts:
        _print_counts()
        return 0

    errors, warnings = _run_all_checks()
    for message in warnings:
        print(f"WARN {message}")
    for message in errors:
        print(f"ERROR {message}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"OK -- 0 errors, {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
