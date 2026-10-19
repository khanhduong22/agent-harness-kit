#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The genre registry: the closed set of skill genres and row membership.

Its own module rather than a section of csv_schema.py because the partition
axis has four independent consumers -- the search engine (pre-score corpus
split), the blueprint composer (type + catalog resolution), the CSV validator
(cell grammar) and the probe runner (per-genre replay) -- and csv_schema is
about what a CELL may contain, not about which CORPUS a row lives in.
"""

from csv_schema import split_list

# --- Genres (contract C6) ---------------------------------------------------
# A skill "genre" is what the CAST of a diagram IS: `system-design` draws deployed
# software components, `process` draws participants + work items + actions. The
# registry is CLOSED -- an unknown value is an error, never a new genre invented by
# a typo in a cell.
#
# Membership rules, in full:
#   - a dataset WITHOUT a `Genres` column is SHARED across every genre (styles,
#     colors, layouts, motion, states, payloads: a hand-drawn look and a dash-flow
#     recipe mean the same thing whatever the cast is);
#   - a dataset WITH the column partitions: a row belongs to exactly the genres its
#     pipe list names;
#   - an EMPTY cell in a dataset that HAS the column is an ERROR, never "all
#     genres". Silent-shared-by-omission is how a process row would leak into the
#     system-design corpus the first time somebody forgot the cell.
#
# The partition happens BEFORE the BM25 fit (core.search), not after scoring: a
# post-score filter leaves the other genre's rows in the IDF statistics and can
# empty a `-n 1` result, so "wrong genre" would change the ranking of rows that
# never left the active one.
GENRE_COL = "Genres"
GENRES = ("system-design", "process")
DEFAULT_GENRE = "system-design"


def row_genres(row):
    """The genres a row belongs to, or () when its dataset carries no column."""
    if GENRE_COL not in row:
        return ()
    return tuple(split_list(row.get(GENRE_COL, "")))


def row_in_genre(row, genre):
    """True when `row` is visible under `genre` (shared datasets always are)."""
    if GENRE_COL not in row:
        return True
    return genre in split_list(row.get(GENRE_COL, ""))


def genres_overlap(source_row, target_row):
    """True when an FK between these two rows is legal on the genre axis.

    Vacuously true unless BOTH rows come from partitioning datasets: a reference
    into a shared dataset (a style, a motion recipe) carries no genre claim. When
    both partition, the referenced row must share at least one genre with the
    referring one -- a `system-design` type whose Node Kinds names a `process`
    component describes a cast it cannot draw, and the composer can only skip it
    at runtime with a warning nobody reads.
    """
    source, target = row_genres(source_row), row_genres(target_row)
    if not source or not target:
        return True
    return bool(set(source) & set(target))


def check_genre_cell(cell):
    """Problems with one Genres cell (unprefixed sentences; caller adds context)."""
    values = split_list(cell)
    if not values:
        return [f"empty {GENRE_COL} cell -- a dataset that carries the column must name "
                f"at least one genre; blank is never 'all genres' (V13)"]
    problems = []
    seen = set()
    for value in values:
        if value not in GENRES:
            problems.append(f"{GENRE_COL} '{value}' is not one of {list(GENRES)} (V13)")
        elif value in seen:
            problems.append(f"{GENRE_COL} repeats '{value}' (V13)")
        seen.add(value)
    return problems
