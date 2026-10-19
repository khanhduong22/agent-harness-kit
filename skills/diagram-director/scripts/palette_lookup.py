#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Composite lookup for data/color-semantics.csv.

colors is the one domain that is NOT a fuzzy catalog: it is a lookup table keyed
(Style ID, Palette, Role), and the useful answer is never "the three rows that
best match your words". It is ONE logical palette -- every role of one named
palette of one style -- because that is the unit a diagram is built from. BM25
over three short columns happily returned `hand-drawn-sketch/house/client` and
`neon-dark/showcase/client` side by side, which is a palette nobody can use.

This module owns that resolution. blueprint_composer and core.search both call
resolve_palette(), so the composer's "emit every role of the default palette"
rule and the CLI's `--domain colors` answer can never drift apart.
"""

from csv_cache import get_row, load_rows

DEFAULT_PALETTE_FALLBACK = "house"


def palette_names(style_id):
    """Every Palette name defined for one style, in first-seen file order."""
    seen = []
    for row in load_rows("colors"):
        if row.get("Style ID") == style_id and row.get("Palette") not in seen:
            seen.append(row.get("Palette"))
    return seen


def default_palette_for(style_id):
    """The palette a style ships with, from styles.csv `Default Palette`."""
    style_row = get_row("styles", style_id)
    if style_row is None:
        return DEFAULT_PALETTE_FALLBACK
    return style_row.get("Default Palette", "") or DEFAULT_PALETTE_FALLBACK


def resolve_palette(style_id, palette=None, role=None):
    """Return (rows, palette_name, warning).

    rows      every role row of one (style, palette), in file order -- or the
              single role row when `role` is given.
    warning   a string when the request could not be honoured exactly (unknown
              palette name, style with no rows at all), else None. Callers
              surface it; nothing here fails silently, because a blueprint that
              quietly lost half its colour tokens still renders.
    """
    wanted = palette or default_palette_for(style_id)
    rows = [row for row in load_rows("colors")
            if row.get("Style ID") == style_id and row.get("Palette") == wanted]
    warning = None

    if not rows:
        known = palette_names(style_id)
        if not known:
            return [], wanted, (f"style '{style_id}' has no rows in color-semantics.csv")
        # Named palette missing but the style has others: fall back to the
        # style's declared default rather than to whatever sorts first.
        fallback = default_palette_for(style_id)
        if fallback == wanted:
            fallback = known[0]
        rows = [row for row in load_rows("colors")
                if row.get("Style ID") == style_id and row.get("Palette") == fallback]
        warning = (f"style '{style_id}' has no '{wanted}' palette; used '{fallback}'. "
                   f"Known palettes: {', '.join(known)}")
        wanted = fallback

    if role:
        matched = [row for row in rows if row.get("Role") == role]
        if not matched:
            roles = ", ".join(sorted({row.get("Role", "") for row in rows}))
            return rows, wanted, (f"palette '{style_id}/{wanted}' has no role '{role}'; "
                                  f"returned every role. Known roles: {roles}")
        return matched, wanted, warning

    return rows, wanted, warning


def parse_palette_query(query):
    """Best-effort (style_id, palette, role) from a free-text colors query.

    Returns (None, None, None) when the query names no known style -- that is
    the signal for core.search to fall back to ordinary BM25, which is what
    keeps exploratory colour search ("warm palette with high contrast") alive.
    Matching is on whole space-or-punctuation separated tokens so a style whose
    ID contains another ID as a substring cannot be shadowed.
    """
    text = " " + " ".join(str(query).lower().replace(",", " ").split()) + " "
    style_ids = [row.get("Style ID", "") for row in load_rows("styles")]
    # Longest ID first: `isometric-2.5d` must win over a hypothetical `isometric`.
    matched_style = next((sid for sid in sorted(style_ids, key=len, reverse=True)
                          if sid and f" {sid.lower()} " in text), None)
    if not matched_style:
        return None, None, None

    # Match against EVERY palette name in the file, not just this style's. Asking
    # for "bauhaus showcase palette" when bauhaus ships no showcase palette must
    # produce a warning, and it only can if the request was understood first --
    # scoping the vocabulary to the style made the word invisible and returned
    # the default palette as though it were what was asked for.
    palettes = {row.get("Palette", "") for row in load_rows("colors")}
    matched_palette = next((p for p in sorted(palettes, key=len, reverse=True)
                            if p and f" {p.lower()} " in text), None)
    roles = sorted({row.get("Role", "") for row in load_rows("colors")}, key=len, reverse=True)
    matched_role = next((r for r in roles if r and f" {r.lower()} " in text), None)
    return matched_style, matched_palette, matched_role
