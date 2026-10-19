#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct-ID resolution: the path taken when a query NAMES a row.

Split out of core.py (2026-08-26, Wave A) because "the caller typed an ID" and
"the caller described a need" are two different questions with two different
failure modes, and the genre partition made the difference load-bearing: a
described need that lands in the wrong genre is simply a miss, while a NAMED row
in the wrong genre is a row the database has and must say so about.

core.py keeps the ranking orchestration; this module owns only "does this query
name a row, and is that row visible from here".
"""

from csv_schema import split_list
from genre_registry import row_genres, row_in_genre


def exact_id_match(rows, id_field, query):
    """Return a row whose id_field or pipe-listed Aliases exactly equals query."""
    folded = str(query).strip().casefold()
    for row in rows:
        if row.get(id_field, "").strip().casefold() == folded:
            return row
        aliases = row.get("Aliases", "")
        if aliases and folded in {a.casefold() for a in split_list(aliases)}:
            return row
    return None


def cross_genre_pointer(rows, id_field, query, genre):
    """One deterministic line when an exact ID exists but in ANOTHER genre.

    This is the ONLY cross-genre message the engine ever emits. Ranked search
    says nothing about what the other genre holds -- an exclusion notice on
    every miss would be noise, and the caller cannot act on a row they cannot
    name. An exact ID is different: the caller named a row that DOES exist, so
    "no matches" would be a lie about the database, and ranking the ID against
    THIS genre's corpus would answer a question they did not ask with whatever
    row happens to share a word with it.

    Returns None when the query names nothing, or names something already
    visible -- callers treat None as "nothing to say".
    """
    row = exact_id_match(rows, id_field, query)
    if row is None or row_in_genre(row, genre):
        return None
    others = [other for other in row_genres(row) if other != genre]
    row_id = row.get(id_field, "").strip()
    return {
        "id": row_id,
        "genres": others,
        "message": (f"'{row_id}' exists, but in genre {'/'.join(others)} -- not "
                    f"{genre}. Re-run with `--genre {others[0]}` to see it."),
    }
