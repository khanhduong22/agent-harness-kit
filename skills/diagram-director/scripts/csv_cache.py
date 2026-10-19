#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV loading and BM25 index caching, keyed by file signature (mtime+size).

Split out of core.py so ranking orchestration (core.py) stays under the
200-line cap and this module can be unit-tested independently of search
logic. Named exports load_rows()/get_row() are re-exported through core.py
so callers can keep importing them from there.
"""

import csv

from bm25_engine import BM25
from csv_config import CSV_CONFIG, domain_path

# Bump whenever the CORPUS tokenizer changes, so a cached index built by the
# old rules is never reused. v2 (2026-08-26): synonym expansion left the corpus
# side entirely and became query-only -- see bm25_engine.normalize.
_INDEX_VERSION = 2
# Memoization caches keyed by file signature -- the only global mutable
# state permitted per docs/code-standards.md.
_csv_cache = {}   # filepath -> (signature, rows)
_bm25_cache = {}  # (filepath, tuple(search_cols), version) -> (signature, BM25)


def _file_signature(filepath):
    stat = filepath.stat()
    return stat.st_mtime_ns, stat.st_size


def load_csv_snapshot(filepath, attempts=3):
    """Return (rows, signature) from a byte-stable read of filepath."""
    signature = _file_signature(filepath)
    cached = _csv_cache.get(filepath)
    if cached and cached[0] == signature:
        return cached[1], signature

    for _ in range(attempts):
        before = _file_signature(filepath)
        with open(filepath, "r", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        after = _file_signature(filepath)
        if before == after:
            _csv_cache[filepath] = (after, rows)
            return rows, after
    raise OSError(f"File changed while reading: {filepath}")


def get_bm25(filepath, search_cols, rows, signature, partition=None):
    """Fitted BM25 index over rows[search_cols], reused while signature matches.

    `partition` names the SUBSET of the file `rows` is -- today, the active genre.
    It is part of the cache key, not decoration: two genres of one file produce two
    different corpora with two different IDF tables, and a key that ignored the
    partition would hand the second caller the first caller's index and silently
    score against the wrong corpus. `None` means "the whole file".
    """
    key = (filepath, tuple(search_cols), _INDEX_VERSION, partition)
    cached = _bm25_cache.get(key)
    if cached and cached[0] == signature:
        return cached[1]
    documents = [" ".join(str(row.get(col, "")) for col in search_cols) for row in rows]
    index = BM25()
    index.fit(documents)
    _bm25_cache[key] = (signature, index)
    return index


def load_rows(domain):
    """Return all rows for domain as a list of dicts (Status not filtered)."""
    rows, _ = load_csv_snapshot(domain_path(domain))
    return rows


def get_row(domain, row_id):
    """Return the row whose id_field exactly matches row_id, or None.

    Ignores Status so the blueprint composer can still resolve a deprecated
    ID rather than have it silently vanish.
    """
    config = CSV_CONFIG[domain]
    id_field = config["id_field"]
    if not id_field:
        return None
    folded = str(row_id).strip().casefold()
    for row in load_rows(domain):
        if row.get(id_field, "").strip().casefold() == folded:
            return row
    return None
