#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Colour checks: V8 palette coverage, V9 WCAG text contrast, V11 node colors
versus the page canvas.

V8/V9 moved here from validate_checks.py (2026-08-26): every check that reasons
about colour now lives together, and validate_checks holds structure only.

V11: node colors versus the page canvas (the gap that let an invisible
node ship). styles.csv carries one representative canvas hex per theme
(`Canvas Light` / `Canvas Dark`, read off the base templates; glassmorphic
uses its gradient's dominant base stop, so its numbers are approximate).

Two sub-checks, deliberately different severities:

V11a (ERROR)  stroke vs canvas >= 3:1 (WCAG 1.4.11 non-text). The stroke is
              what guarantees a node has a visible boundary at all; below
              3:1 the node can vanish into the page.

V11b (WARN)   "hole" detection. A fill nearly identical to the canvas is
              NORMAL in outline-first styles (blueprint, ascii-terminal) --
              measurement across all 70 rows found 63 fills within 1.15:1
              luminance of canvas, because pastel tints carry hue, not
              luminance. It is a defect only when the REST of that style's
              palette is clearly tinted, making the one canvas-colored node
              read as a hole (the observed flat-minimal dark external bug).
              `infra` is exempt: it is the substrate and recedes by design.
              Warning, not error: the final judge of aesthetics is a render.
"""

import csv

from color_contrast import contrast_ratio
from csv_config import domain_path
from csv_schema import NODE_ROLES

COLOR_ROLE_ORDER = set(NODE_ROLES)

_HEX = r"^#[0-9a-f]{6}$"

# below this RGB distance two hexes are indistinguishable in practice
_HOLE_DISTANCE = 8.0
# a style-mode whose median fill distance exceeds this is "clearly tinted"
_TINTED_MEDIAN = 40.0


def _rgb_distance(a, b):
    ar, ag, ab_ = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return ((ar - br) ** 2 + (ag - bg) ** 2 + (ab_ - bb) ** 2) ** 0.5


def _median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def check_canvas(errors, warnings):
    styles = {row["Style ID"]: row for row in
              csv.DictReader(open(domain_path("styles"), encoding="utf-8"))}
    color_rows = list(csv.DictReader(open(domain_path("colors"), encoding="utf-8")))

    # Keyed by (style, palette, mode) since 2026-08-26: a style can ship several
    # named palettes and each is a whole colour system, so the "is this style
    # tinted?" median that gates V11b must be measured inside one palette. Mixing
    # a tinted palette with an outline-first one would average both into silence.
    # The canvas hexes stay the STYLE's -- a palette repaints nodes, not the page.
    by_style_mode = {}
    for row in color_rows:
        style = styles.get(row["Style ID"])
        if style is None:
            continue  # V6 already reports the broken FK
        for mode, canvas_col, fill_col, stroke_col in (
                ("light", "Canvas Light", "Fill", "Stroke"),
                ("dark", "Canvas Dark", "Dark Fill", "Dark Stroke")):
            canvas = style.get(canvas_col, "").strip()
            label = f"{row['Style ID']}/{row['Palette']}/{row['Role']} {mode}"
            try:
                ratio = contrast_ratio(row[stroke_col], canvas)
                distance = _rgb_distance(row[fill_col].strip().lower(), canvas.lower())
            except (KeyError, ValueError):
                errors.append(f"styles.csv:{row['Style ID']}: {canvas_col} is not a #rrggbb hex (V11)")
                continue
            if ratio < 3.0:
                errors.append(f"color-semantics.csv:{label}: stroke {row[stroke_col]} vs canvas "
                              f"{canvas} = {ratio:.2f}:1, below 3.0:1 (V11a)")
            by_style_mode.setdefault((row["Style ID"], row["Palette"], mode), []).append(
                (row["Role"], distance, row[fill_col]))

    for (style_id, palette, mode), entries in by_style_mode.items():
        median = _median([d for _, d, _ in entries])
        if median < _TINTED_MEDIAN:
            continue  # outline-first style: canvas-colored fills are its aesthetic
        canvas_col = "Canvas Light" if mode == "light" else "Canvas Dark"
        canvas = styles[style_id][canvas_col]
        for role, distance, fill in entries:
            if role != "infra" and distance < _HOLE_DISTANCE:
                warnings.append(
                    f"color-semantics.csv:{style_id}/{palette}/{role} {mode}: fill {fill} is "
                    f"indistinguishable from canvas {canvas} (distance {distance:.1f}) while the "
                    f"style is clearly tinted (median {median:.0f}) -- node reads as a hole (V11b)")


def check_color_coverage(errors):
    """V8: every (Style ID, Palette) has exactly 7 color rows, one per Role.

    Grouped by palette, not by style, since 2026-08-26: a style may ship several
    named palettes (house = the dataset's own, showcase = the blessed vertical-fork
    tokens). A partial palette is the failure this catches -- half a palette is worse
    than none, because the composer would silently mix two colour systems.
    Also checks styles.csv's Default Palette actually resolves to a group here.
    """
    rows = list(csv.DictReader(open(domain_path("colors"), encoding="utf-8")))
    by_palette = {}
    for row in rows:
        key = (row.get("Style ID", ""), row.get("Palette", ""))
        by_palette.setdefault(key, []).append(row.get("Role", ""))
    for (style_id, palette), roles in by_palette.items():
        if len(roles) != 7 or set(roles) != COLOR_ROLE_ORDER:
            errors.append(f"color-semantics.csv:{style_id}/{palette}: expected exactly 7 rows "
                          f"(one per role), got {sorted(roles)} (V8)")
    for row in csv.DictReader(open(domain_path("styles"), encoding="utf-8")):
        default = row.get("Default Palette", "").strip()
        if (row["Style ID"], default) not in by_palette:
            errors.append(f"styles.csv:{row['Style ID']}: Default Palette='{default}' has no rows "
                          f"in color-semantics.csv (V8)")


def check_contrast(errors):
    """V9: WCAG contrast recomputed from raw hex, not trusted from Contrast Note.

    Every palette is checked independently -- a blessed showcase palette gets no
    grace for being hand-authored elsewhere.
    """
    rows = list(csv.DictReader(open(domain_path("colors"), encoding="utf-8")))
    for row in rows:
        label = f"{row.get('Style ID')}/{row.get('Palette')}/{row.get('Role')}"
        for on_col, fill_col in (("On Color", "Fill"), ("Dark On Color", "Dark Fill")):
            try:
                ratio = contrast_ratio(row[on_col], row[fill_col])
            except (KeyError, ValueError):
                errors.append(f"color-semantics.csv:{label}: invalid hex in {on_col}/{fill_col} (V9)")
                continue
            if ratio < 4.5:
                errors.append(f"color-semantics.csv:{label}: {on_col} vs {fill_col} = {ratio:.2f}:1, below 4.5:1 (V9)")
