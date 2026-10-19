#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Style and base-template resolution for the blueprint composer.

Split out of blueprint_composer.py (2026-08-26) when that module crossed the
200-line cap in docs/code-standards.md. It is a real concern boundary, not a
line-count trick: everything here answers "which style, and which template file
does it ship", and none of it knows about types, motions, palettes or specs.
Both functions append to a caller-owned `warnings` list, same contract as the
rest of the composer -- a fallback is always visible in the output.
"""

from bm25_engine import BM25
from core import get_row, load_rows
from csv_config import CSV_CONFIG
from csv_schema import artifact_safe, resolve_shape_hint, split_list


def best_by_score(rows, search_cols, query):
    """Rank rows by BM25 relevance to query; return the top row (or None)."""
    if not rows:
        return None
    docs = [" ".join(str(row.get(col, "")) for col in search_cols) for row in rows]
    index = BM25()
    index.fit(docs)
    ranked = index.score(query)
    return rows[ranked[0][0]] if ranked else rows[0]


def is_artifact_safe(style_row):
    """True when the style needs no JS runtime and no CDN dependency.

    Thin alias for csv_schema.artifact_safe, which core.search()'s --target
    filter shares -- the rule has exactly one definition.
    """
    return artifact_safe(style_row)


def resolve_style(scenario, style_id, type_row, target, warnings):
    """Return (style_row, is_fallback) for the scenario, honouring --style."""
    if style_id:
        row = get_row("styles", style_id)
        if row is None:
            warnings.append(f"unknown --style '{style_id}'; falling back to scenario-based selection")
        else:
            if target == "artifact" and not is_artifact_safe(row):
                warnings.append(
                    f"style '{style_id}' is not artifact-safe (Runtime={row.get('Runtime')}, "
                    f"CDN Deps={row.get('CDN Deps') or 'none'}); kept per explicit --style override -- "
                    "see references/style-guides.md for a css-only fallback"
                )
            return row, False

    best_ids = split_list(type_row.get("Best Styles", ""))
    all_styles = {row["Style ID"]: row for row in load_rows("styles") if row.get("Status") == "active"}
    candidates = [all_styles[s] for s in best_ids if s in all_styles]
    if target == "artifact":
        safe = [row for row in candidates if is_artifact_safe(row)]
        if not safe:
            safe = [row for row in all_styles.values() if is_artifact_safe(row)]
            if safe:
                warnings.append("no artifact-safe style among type's Best Styles; broadened to all styles")
        candidates = safe

    if not candidates:
        warnings.append("no style candidates resolved; used 'flat-minimal' fallback")
        return get_row("styles", "flat-minimal"), True

    # Prefer a style that actually has a base template. Several types list both
    # shipped and planned styles as equally good fits, and picking a planned one
    # leaves the caller composing from snippets for no reason -- SKILL.md forbids
    # citing a template path for it. Planned styles stay reachable through an
    # explicit --style override, which is handled above this point.
    shipped = [row for row in candidates if row.get("Template Status") == "shipped"]
    if shipped:
        candidates = shipped
    elif candidates:
        warnings.append(
            "no shipped template among candidate styles; compose from templates/snippets/ "
            "and do not cite a base template path"
        )
    return best_by_score(candidates, CSV_CONFIG["styles"]["search_cols"], scenario), False


def resolve_catalog_shapes(catalog, style_row, warnings):
    """Return catalog rows with Shape Hint collapsed to the ONE shape this style draws.

    A Shape Hint cell carries every style's variant at once
    (`default:hexagon|blueprint:hexagon-hatched|ascii-terminal:box-hexagon`). Emitting
    that raw list in a blueprint hands the reader three shapes for one node and asks
    them to pick -- which is how a blueprint composed for `blueprint` ends up drawn in
    the default geometry. The chosen style's override wins, else `default`.
    """
    style_id = style_row.get("Style ID", "")
    resolved = []
    for row in catalog:
        token, source = resolve_shape_hint(row.get("Shape Hint", ""), style_id)
        if not token:
            warnings.append(f"component '{row.get('Component ID')}' has no usable Shape Hint; "
                            "shape left unresolved in the catalog")
        resolved.append(dict(row, **{"Shape Hint": token,
                                     "Shape Hint Source": source or "(unresolved)"}))
    return resolved


def resolve_template_path(style_row, type_row, warnings):
    """Return (path, is_substituted) for the base template to copy."""
    if style_row.get("Template Status") == "shipped":
        return f"templates/base/{style_row['Style ID']}.html", False
    for sid in split_list(type_row.get("Best Styles", "")):
        candidate = get_row("styles", sid)
        if candidate and candidate.get("Template Status") == "shipped":
            warnings.append(
                f"style '{style_row.get('Style ID')}' has no shipped template yet (planned); "
                f"substituted '{sid}' template from the type's Best Styles -- verify it fits visually"
            )
            return f"templates/base/{sid}.html", True
    warnings.append(
        f"style '{style_row.get('Style ID')}' has no shipped template yet (planned); "
        "substituted 'flat-minimal' as the nearest universally-shipped template"
    )
    return "templates/base/flat-minimal.html", True
