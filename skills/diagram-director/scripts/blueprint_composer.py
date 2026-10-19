#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blueprint composer: joins diagram-type -> style -> layout -> motion set ->
color palette into one diagram spec dict. Rendering (markdown/ascii) lives in
blueprint_render.py so this module stays focused on resolution logic. Every
fallback taken appends a string to spec["warnings"] so a plausible-but-wrong
diagram is never shipped silently.

AUTHORITY SPLIT (2026-08-26). Authoritative here: TYPE, LAYOUT, STYLE, PALETTE.
NOT authoritative: the component list. A type's `Node Kinds` cell is one worked
example (`comparison` freezes a chat-fanout one), so pasting it drew a chat
diagram for an auction prompt with every gate green (observed) -- those rows go
out as a labelled CATALOG, and real component lists come from per-component
`--domain components` queries (references/workflow-phases.md -> Phase 3). Same
reasoning kills the type fallback: no type over the floor means ABSTAIN, never
a default, because a guessed type drags a wrong layout and motion set with it.
"""

import re

from blueprint_style import resolve_catalog_shapes, resolve_style, resolve_template_path
from core import get_row, load_rows, project_row, search
from csv_config import MAX_ANIMATED_EDGES
from csv_schema import split_list, split_ref
from genre_registry import DEFAULT_GENRE, row_genres, row_in_genre
from palette_lookup import resolve_palette


def _sweet_spot_upper(text):
    """Largest upper bound found in a 'Node Count Sweet Spot' cell, e.g.
    '4-8 lanes, 3-12 steps per lane' -> 12. Used only for a soft warning."""
    pairs = re.findall(r"(\d+)-(\d+)", text or "")
    return max((int(hi) for _, hi in pairs), default=None)


def _resolve_type(scenario, type_id, genre=DEFAULT_GENRE):
    """Return (type_row, None), or (None, reason) so compose() abstains.

    There is deliberately no default: a type carries the layout, the edge
    semantics, the motion set and the anti-patterns, so guessing one is not a
    small error -- it is four wrong answers presented as data.

    A named `--type` from ANOTHER genre is not "unknown": the row exists, and
    saying so (with the genre to re-run under) is the difference between a
    typo and a wrong flag.
    """
    if type_id:
        row = get_row("types", type_id)
        if row is not None and row_in_genre(row, genre):
            return row, None
        if row is not None:
            others = [g for g in row_genres(row) if g != genre] or ["another genre"]
            return None, (f"--type '{type_id}' is a {'/'.join(others)} type, not {genre}. "
                          f"Re-run with `--genre {others[0]}`.")
        known = ", ".join(sorted(r["Type ID"] for r in load_rows("types")
                                 if row_in_genre(r, genre)))
        # Wording deliberately unchanged for the default genre: this message is a
        # user-facing error path and Wave A ships zero text drift on it. The
        # genre only surfaces in the branch that cannot fire under system-design.
        return None, (f"unknown --type '{type_id}'. Known Type IDs: "
                      f"{known or f'(none -- genre {genre!r} has no diagram types yet)'}")

    result = search(scenario, domain="types", max_results=1, genre=genre)
    if result.get("count"):
        return result["results"][0], None

    suggestions = result.get("suggestions") or []
    reason = "no diagram type cleared the score floor for this scenario."
    if suggestions:
        reason += " Closest known terms: " + ", ".join(suggestions) + "."
    return None, reason


def _resolve_motions(type_row, style_row, target, warnings):
    type_motions = set(split_list(type_row.get("Recommended Motion", "")))
    style_motions = set(split_list(style_row.get("Motion Affinity", "")))
    common = sorted(type_motions & style_motions)
    rows = [row for row in (get_row("motion", mid) for mid in common) if row]
    if target == "artifact":
        rows = [row for row in rows if row.get("Runtime") == "css-only"]
    if rows:
        return rows, False

    warnings.append("type/style recommended-motion intersection was empty; used style's Motion Affinity fallback (max 3)")
    fallback = []
    for mid in sorted(style_motions):
        row = get_row("motion", mid)
        if row and (target != "artifact" or row.get("Runtime") == "css-only"):
            fallback.append(row)
        if len(fallback) == 3:
            break
    return fallback, True


def _resolve_catalog(type_row, warnings, genre=DEFAULT_GENRE):
    """Expand the type's `Node Kinds` cell into full component rows.

    ILLUSTRATIVE ONLY (see module docstring): never paste these into a solution
    sheet -- they only show what shapes the archetype tends to use.

    A component outside the active genre is skipped LOUDLY rather than drawn:
    a cross-genre Node Kinds reference is a data error the validator should
    grow to catch, and a silent drop would hide it behind a shorter catalog.
    """
    ids = split_list(type_row.get("Node Kinds", ""))
    rows = []
    for cid in ids:
        row = get_row("components", cid)
        if row is None:
            warnings.append(f"Node Kinds referenced unknown component '{cid}'; skipped from the catalog")
        elif not row_in_genre(row, genre):
            warnings.append(f"Node Kinds referenced '{cid}', which is not a {genre} component; "
                            "skipped from the catalog")
        else:
            # Projected to the ANSWER columns here, before the shape resolver adds
            # its own key: the catalog a blueprint prints is the same shape a
            # `--domain components` search returns, meta columns and all excluded.
            rows.append(project_row("components", row))
    return rows


def compose(scenario, style_id=None, target="artifact", type_id=None, genre=DEFAULT_GENRE):
    """Resolve one scenario into a full diagram spec dict (see module docstring).

    On a type miss the returned dict has abstained=True and no diagram fields:
    nothing is composed, and blueprint_render prints the abstain message.

    `genre` reaches the two datasets that partition -- the TYPE and the component
    CATALOG. Style, layout, palette and motion are shared across genres by
    design (a hand-drawn look and a dash-flow recipe mean the same thing whatever
    the cast is), so they take no genre argument at all rather than one that
    would silently do nothing.
    """
    warnings = []
    type_row, abstain_reason = _resolve_type(scenario, type_id, genre)
    if type_row is None:
        # `genre` rides ONLY on the abstain dict: the composed spec's sections are
        # what the re-acceptance protocol diffs, so the composed output stays
        # byte-identical while the recovery advice can still name the active corpus.
        return {"scenario": scenario, "target": target, "abstained": True,
                "genre": genre, "abstain_reason": abstain_reason, "warnings": warnings}

    style_row, style_is_fallback = resolve_style(scenario, style_id, type_row, target, warnings)
    layout_row = get_row("layouts", type_row.get("Default Layout", ""))
    if layout_row is None:
        warnings.append("type's Default Layout did not resolve; used 'layered-lr' fallback")
        layout_row = get_row("layouts", "layered-lr")

    motions, motions_is_fallback = _resolve_motions(type_row, style_row, target, warnings)
    # Shape Hints are collapsed to one token per row for the chosen style here, so
    # nothing downstream ever sees the multi-key cell (see resolve_catalog_shapes).
    catalog = resolve_catalog_shapes(_resolve_catalog(type_row, warnings, genre), style_row, warnings)
    # colors is keyed (Style ID, Palette, Role) since 2026-08-26. The composer emits
    # ONE palette on purpose: a blueprint whose Palette tokens section listed two
    # sets of --color-client-fill would be unusable, and mixing them silently is
    # exactly the drift the Palette column exists to stop. Anyone who wants the
    # alternate palette asks for it by name via --domain colors.
    # EVERY role is emitted, not only the catalog's: the palette is authoritative
    # and the catalog is not, so filtering the one by the other would let an
    # illustrative list decide which tokens the real diagram may have (an auction
    # needs `error` whether or not the chat-fanout catalog mentions it).
    # One function serves this and `--domain colors` (palette_lookup.resolve_palette),
    # so the composer's palette and the CLI's palette answer cannot drift apart.
    palette, _palette_name, palette_warning = resolve_palette(style_row.get("Style ID", ""))
    if palette_warning:
        warnings.append(palette_warning + " -- blueprint palette tokens may be incomplete")
    template_path, template_is_fallback = resolve_template_path(style_row, type_row, warnings)
    catalog_snippet_files = sorted({split_ref(c["Snippet Ref"])[0] for c in catalog if c.get("Snippet Ref")})

    catalog_node_count = len(catalog)
    sweet_spot_upper = _sweet_spot_upper(layout_row.get("Node Count Sweet Spot", ""))
    if sweet_spot_upper and catalog_node_count > sweet_spot_upper:
        warnings.append(
            f"the catalog alone lists {catalog_node_count} components, already over layout "
            f"'{layout_row.get('Layout ID')}' sweet spot ({sweet_spot_upper}); size YOUR component "
            "list against that ceiling and animate only the primary flow path"
        )
    if len(motions) > MAX_ANIMATED_EDGES:
        warnings.append(
            f"{len(motions)} motions assigned exceeds MAX_ANIMATED_EDGES={MAX_ANIMATED_EDGES}; "
            "animate only the primary flow path"
        )

    return {
        "scenario": scenario, "target": target, "abstained": False,
        "type": project_row("types", type_row), "type_was_named": bool(type_id),
        "style": style_row, "style_is_fallback": style_is_fallback,
        "layout": layout_row,
        "motions": motions, "motions_is_fallback": motions_is_fallback,
        # Illustrative, NOT the diagram's component list -- see module docstring.
        "catalog_components": catalog, "catalog_snippet_files": catalog_snippet_files,
        "catalog_node_count": catalog_node_count,
        "palette": palette,
        "template_path": template_path, "template_is_fallback": template_is_fallback,
        "sweet_spot_upper": sweet_spot_upper,
        "warnings": warnings,
    }
