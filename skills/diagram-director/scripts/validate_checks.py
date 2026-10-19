#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural checks V1-V6 and V10 for validate_csv.py, split out to keep the CLI
entry point under the 200-line cap. Colour checks (V8/V9/V11) live in
validate_colors.py, cross-reference checks (V7/V11) in validate_anchors.py. Every function appends to a caller-owned
errors/warnings list rather than raising, so one run reports everything.

Cell grammar (split_list/split_terms), closed vocabularies and FK rules come
from csv_schema.py -- this module holds the checking, not the schema.
"""

import csv
import re

from csv_config import CSV_CONFIG, GENRE_DOMAINS, REQUIRED_COLS, REQUIRED_HEADERS, domain_path
from csv_schema import ENUMS, FK_RULES, split_list, split_terms
from genre_registry import GENRE_COL, check_genre_cell, genres_overlap, row_genres

# Kebab-case per contract C1, with a deliberate relaxation: a "." is also
# accepted as a segment separator so the frozen id "isometric-2.5d" (a real,
# intentional style id -- see phase-02 roster) validates instead of being
# flagged as broken. Still rejects spaces, uppercase, underscores, etc.
ID_PATTERN = re.compile(r"^[a-z0-9]+([-.][a-z0-9]+)*$")


def read_rows(domain, errors):
    """Parse one domain's CSV, recording V1 (parse/short/ragged-row) errors.

    Read through csv.reader rather than csv.DictReader so row ARITY is visible:
    DictReader silently pads a short row with None and buries the extras under a
    None key, which turned a truncated row into a set of quiet empty cells. A row
    with the wrong number of cells is named here and still handed on (padded) so
    the remaining checks can report everything else about the file in one pass.
    """
    path = domain_path(domain)
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            raw = list(csv.reader(handle))
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{path.name}: cannot read file ({exc})")
        return [], []
    if not raw:
        errors.append(f"{path.name}: empty file (V1)")
        return [], []

    header, rows = raw[0], []
    for line_no, cells in enumerate(raw[1:], 2):
        label = f"{path.name}:row{line_no}"
        if cells and cells[0].strip():
            label += f" ('{cells[0].strip()}')"
        if len(cells) < len(header):
            errors.append(f"{label}: short row -- {len(cells)} cells, header has {len(header)} (V1)")
        elif len(cells) > len(header):
            errors.append(f"{label}: ragged row -- {len(cells)} cells, header has {len(header)} (V1)")
        padded = list(cells[:len(header)]) + [""] * max(0, len(header) - len(cells))
        rows.append(dict(zip(header, padded)))
    if not rows:
        errors.append(f"{path.name}: no data rows (V1)")
    return header, rows


def check_header(domain, header, errors):
    expected = REQUIRED_HEADERS[domain]
    if header != expected:
        errors.append(f"{CSV_CONFIG[domain]['file']}: header mismatch (V2) expected={expected} actual={header}")


def check_keys(domain, rows, errors):
    """V3: every key column is filled, kebab-case, and the key TUPLE is unique.

    Composite for colors (Style ID + Palette + Role): a duplicate there is not a
    cosmetic dupe, it is two competing values for one token the composer reads.
    """
    cfg = CSV_CONFIG[domain]
    fname, fields = cfg["file"], cfg["key_fields"]
    seen = set()
    for line_no, row in enumerate(rows, 2):
        values = [(row.get(field) or "").strip() for field in fields]
        label = "/".join(values) or f"row{line_no}"
        for field, value in zip(fields, values):
            if not value:
                errors.append(f"{fname}:row{line_no}: empty {field} (V3)")
            elif not ID_PATTERN.match(value):
                errors.append(f"{fname}:{label}: {field} is not lowercase kebab-case (V3)")
        if not all(values):
            continue
        key = tuple(values)
        if key in seen:
            errors.append(f"{fname}:{label}: duplicate key ({', '.join(fields)}) (V3)")
        seen.add(key)


def check_enums(domain, rows, errors):
    for column, allowed in ENUMS.get(domain, {}).items():
        fname = CSV_CONFIG[domain]["file"]
        row_key = CSV_CONFIG[domain]["id_field"]
        for row in rows:
            value = row.get(column, "").strip()
            if value and value not in allowed:
                label = row.get(row_key, "?") if row_key else "?"
                errors.append(f"{fname}:{label}: {column}='{value}' not in {sorted(allowed)} (V4)")


def check_required_cells(domain, rows, errors):
    """V5: no required column is blank, plus the Keywords richness floor."""
    fname = CSV_CONFIG[domain]["file"]
    row_key = CSV_CONFIG[domain]["id_field"]
    required = REQUIRED_COLS[domain]
    has_keywords = "Keywords" in REQUIRED_HEADERS[domain]
    for line_no, row in enumerate(rows, 2):
        label = row.get(row_key, "").strip() if row_key else ""
        label = label or f"row{line_no}"
        for column in required:
            if not (row.get(column) or "").strip():
                errors.append(f"{fname}:{label}: empty {column} (V5)")
        if has_keywords:
            terms = split_terms(row.get("Keywords", ""))
            if len(set(t.casefold() for t in terms)) < 5:
                errors.append(f"{fname}:{label}: Keywords has fewer than 5 distinct terms (V5)")


def check_genres(domain, rows, errors):
    """V13: Genres grammar on the datasets that partition by genre.

    Only runs for a domain that DECLARES the column (csv_config.GENRE_DOMAINS);
    a dataset without one is shared across genres by design, and V2 already
    catches a file that grew or lost the column behind the config's back. The
    check that matters is the EMPTY cell: blank is an error, never "all genres",
    because shared-by-omission is how a `process` row would end up in the
    system-design corpus the first time somebody forgot to fill it in.
    """
    if domain not in GENRE_DOMAINS:
        return
    fname = CSV_CONFIG[domain]["file"]
    row_key = CSV_CONFIG[domain]["id_field"]
    for line_no, row in enumerate(rows, 2):
        label = (row.get(row_key, "").strip() if row_key else "") or f"row{line_no}"
        for problem in check_genre_cell(row.get(GENRE_COL, "")):
            errors.append(f"{fname}:{label}: {problem}")


def _rows_by_id():
    """domain -> {id: row}, for FK resolution (V6) and its genre half (V6g)."""
    tables = {}
    for domain, cfg in CSV_CONFIG.items():
        id_field = cfg["id_field"]
        if not id_field:
            continue
        path = domain_path(domain)
        tables[domain] = {}
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8", newline="") as handle:
            tables[domain] = {row.get(id_field, "").strip(): row for row in csv.DictReader(handle)}
    return tables


def check_fks(errors):
    """V6: every FK resolves. V6g: and it resolves WITHIN the referrer's genre.

    V6g fires only where both ends partition (today: types.Node Kinds -> components).
    Without it the composer meets a cross-genre reference at runtime and can only WARN,
    on a catalog that is illustrative anyway -- the defect would ship as a short catalog.
    """
    tables = _rows_by_id()
    for source_domain, source_col, target_domain, is_multi in FK_RULES:
        path = domain_path(source_domain)
        if not path.exists():
            continue
        row_key = CSV_CONFIG[source_domain]["id_field"]
        with open(path, "r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                label = row.get(row_key, "?") if row_key else f"{row.get('Style ID')}/{row.get('Role')}"
                raw = row.get(source_col, "").strip()
                values = split_list(raw) if is_multi else ([raw] if raw else [])
                for value in values:
                    target_row = tables.get(target_domain, {}).get(value)
                    if target_row is None:
                        errors.append(
                            f"{CSV_CONFIG[source_domain]['file']}:{label}: "
                            f"{source_col}='{value}' not found in {CSV_CONFIG[target_domain]['file']} (V6)"
                        )
                    elif not genres_overlap(row, target_row):
                        errors.append(
                            f"{CSV_CONFIG[source_domain]['file']}:{label}: {source_col}='{value}' is "
                            f"a {'|'.join(row_genres(target_row))} row, referrer is "
                            f"{'|'.join(row_genres(row))} -- an FK may not cross genres (V6g)")


def check_runtime_consistency(errors):
    """V10: a css-only style needs >=1 css-only motion; empty CDN Deps forbids needs-js."""
    motion_runtime = {row["Motion ID"]: row.get("Runtime", "") for row in
                      csv.DictReader(open(domain_path("motion"), encoding="utf-8"))}
    for row in csv.DictReader(open(domain_path("styles"), encoding="utf-8")):
        style_id = row["Style ID"]
        affinity = split_list(row.get("Motion Affinity", ""))
        if row.get("Runtime") == "css-only" and not any(motion_runtime.get(m) == "css-only" for m in affinity):
            errors.append(f"styles.csv:{style_id}: Runtime=css-only but no css-only motion in Motion Affinity (V10)")
        if not row.get("CDN Deps", "").strip() and row.get("Runtime") == "needs-js":
            errors.append(f"styles.csv:{style_id}: empty CDN Deps but Runtime=needs-js (V10)")
