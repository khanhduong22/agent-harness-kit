#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Column-level schema for the eight datasets: cell grammar, closed vocabularies,
cross-file FK rules and cross-reference (`path#anchor`) rules.

Split out of csv_config.py (2026-08-26) on a real concern boundary: csv_config
answers "which datasets exist and how is search tuned", this module answers "what
may a cell contain, and what must it point at". It is also the ONE place a
multi-value cell is parsed -- six call sites across the validators, the composer,
the style resolver and the gallery each re-derived
`[v.strip() for v in cell.split("|") if v.strip()]`, so a change to contract C2
had six places to miss (and `core._exact_id_match` splitting Aliases on `|` while
the data used `;` is exactly the class of bug that produced).
"""

import re

# --- Cell grammar ----------------------------------------------------------
LIST_SEP = "|"          # contract C2: multi-value cells the code SPLITS
_TERM_SEP = re.compile(r"[;,|]")   # Keywords/prose cells; files differ, tokenizer does not care


def split_list(cell, sep=LIST_SEP):
    """Values of a multi-value cell: stripped, blanks dropped (contract C2)."""
    return [value.strip() for value in (cell or "").split(sep) if value.strip()]


def split_terms(cell):
    """Terms of a Keywords/prose cell, which the files separate with `;`, `,` or `|`."""
    return [term.strip() for term in _TERM_SEP.split(cell or "") if term.strip()]


def split_ref(ref):
    """(file_part, anchor) of a `path#anchor` cell; either half may come back empty."""
    file_part, _, anchor = (ref or "").partition("#")
    return file_part.strip(), anchor.strip()


# --- Shape Hint ------------------------------------------------------------
# A Shape Hint cell is a pipe list of `<key>:<shape-token>` pairs, e.g.
#   default:hexagon|blueprint:hexagon-hatched|ascii-terminal:box-hexagon
# `default` is mandatory; every other key is a Style ID that overrides it.
#
# CONVENTIONS BELOW WERE DERIVED FROM THE DATA + templates/snippets/, not assumed
# (2026-08-26 audit of all 79 component rows):
#   - `default` and `blueprint` tokens are geometry NAMES, not snippet anchors:
#     only 33/79 default tokens equal their row's Snippet Ref anchor, so there is
#     no anchor mapping to enforce for them. What anchors them is the row's own
#     Snippet Ref, which REF_RULES checks.
#   - `blueprint` tokens are, in all 58 rows that carry one, `<family>-hatched`
#     -- the hatched-fill tell the blueprint style is built on (references/style-guides.md).
#     The stem is the default token's base FAMILY, not the token itself: blueprint
#     deliberately drops per-component decorations (hexagon-shield -> hexagon-hatched)
#     in 26/58 rows, so "stem == default token" is provably NOT the invariant here.
#   - `ascii-terminal` tokens are, in all 79 rows, `box-<base>` where
#     `snippets/node-shapes.html#shape-<base>` is a real anchor: the terminal style
#     degrades every node to one of the canonical base geometries. That one IS an
#     anchor mapping and is enforced against the file.
DEFAULT_HINT_KEY = "default"
SHAPE_TOKEN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BASE_SHAPE_FILE = "snippets/node-shapes.html"
SHAPE_HINT_RULES = {
    "blueprint": {"suffix": "-hatched"},
    "ascii-terminal": {"prefix": "box-", "anchor_file": BASE_SHAPE_FILE, "anchor_prefix": "shape-"},
}


def parse_shape_hint(cell):
    """Return ({key: shape_token}, [problem strings]) for one Shape Hint cell.

    Problems are unprefixed sentences; the caller adds file/row context.
    """
    hints, problems = {}, []
    raw = (cell or "").strip()
    if not raw:
        return hints, ["empty Shape Hint"]
    for part in split_list(raw):
        if ":" not in part:
            problems.append(f"Shape Hint entry '{part}' is not '<key>:<shape>'")
            continue
        key, token = (piece.strip() for piece in part.split(":", 1))
        if not key or not token:
            problems.append(f"Shape Hint entry '{part}' has an empty key or value")
            continue
        if key in hints:
            problems.append(f"Shape Hint repeats key '{key}'")
            continue
        if not SHAPE_TOKEN.match(token):
            problems.append(f"Shape Hint '{key}:{token}' is not a lowercase kebab-case shape token")
        hints[key] = token
    if DEFAULT_HINT_KEY not in hints:
        problems.append(f"Shape Hint has no mandatory '{DEFAULT_HINT_KEY}:' entry")
    return hints, problems


def resolve_shape_hint(cell, style_id):
    """Return (shape_token, source) -- the ONE shape a style renders for this row.

    source is the Style ID when the row carries an override for it, else 'default'.
    A row with neither returns ("", "") so the caller can say so out loud.
    """
    hints, _ = parse_shape_hint(cell)
    if style_id and style_id in hints:
        return hints[style_id], style_id
    if DEFAULT_HINT_KEY in hints:
        return hints[DEFAULT_HINT_KEY], DEFAULT_HINT_KEY
    return "", ""


# --- Runtime target constraint (--target) -----------------------------------
# SKILL.md STEP 1: `--target artifact` restricts answers to rows needing no JS
# runtime and no CDN asset (an artifact renders under a CSP sandbox). Only a
# dataset declaring a `Runtime` column can be judged, hence the COLUMN test rather
# than a domain allow-list. artifact_safe() is the SINGLE definition of the rule,
# shared by core.search()'s --target filter and the composer's style resolver --
# two copies is how the CLI came to enforce it in one mode and ignore it in the other.
RUNTIME_COL = "Runtime"
CDN_COL = "CDN Deps"


def domain_has_runtime(output_cols):
    """True when this domain's rows can be judged artifact-safe at all."""
    return RUNTIME_COL in output_cols


def artifact_safe(row):
    """True when a row needs no JS runtime and ships no CDN dependency."""
    return row.get(RUNTIME_COL) == "css-only" and not (row.get(CDN_COL) or "").strip()


# --- Closed vocabularies (contract C4) --------------------------------------
_STATUS_ENUM = {"active", "supplemental", "deprecated"}
# The seven data-role values every base template's stylesheet maps to
# var(--role-*) (see the "Valid roles" line in templates/snippets/node-shapes.html).
# components.Semantic Role and color-semantics.Role are the SAME vocabulary --
# a typo in either means a node asks for a --color-<role>-* token nothing defines.
NODE_ROLES = {"client", "service", "data", "async", "external", "error", "infra"}
ENUMS = {
    "styles": {
        "Runtime": {"css-only", "needs-js"}, "Status": _STATUS_ENUM,
        "Complexity": {"low", "medium", "high"},
        "Dark Mode": {"native", "supported", "not-recommended"},
        "Template Status": {"shipped", "planned"},
    },
    "types": {
        "Category": {"c4", "flow", "infra", "behavior", "pattern"},
        "Labeling Level": {"minimal", "medium", "rich"}, "Status": _STATUS_ENUM,
    },
    "motion": {
        "Runtime": {"css-only", "needs-js"}, "Status": _STATUS_ENUM,
        "Technique": {"stroke-dashoffset", "offset-path", "opacity-filter", "clip-path",
                      "transform", "animation-delay-stagger", "js-timeline"},
    },
    "components": {
        # Category per docs/code-standards.md C4. It carries the PACK-LOCAL KIND,
        # so the vocabulary is the union over genres and each genre uses its own
        # slice: system-design rows take the first nine, `process` rows take the
        # last three (actor | artifact | decision -- what the cast of a process
        # diagram is made of). Semantic Role stays the fixed 7-slot engine
        # palette for BOTH; the mapping between them is the process guide's
        # Role mapping table, and the LEGEND text derives from Category + Name
        # so a viewer of a process diagram reads "actor", never "client".
        "Category": {"client", "gateway", "compute", "storage", "messaging",
                     "infra", "external", "observability", "ml",
                     "actor", "artifact", "decision"},
        "Semantic Role": NODE_ROLES,
        "Status": _STATUS_ENUM,
    },
    "states": {"Applies To": {"node", "edge"}, "Status": _STATUS_ENUM},
    "payloads": {"Status": _STATUS_ENUM},
    "colors": {"Role": NODE_ROLES},
    "layouts": {"Status": _STATUS_ENUM},
}

# --- Cross-file FK rules (contract C3) --------------------------------------
# (source_domain, source_col, target_domain, is_multi_value)
FK_RULES = [
    ("styles", "Motion Affinity", "motion", True),
    ("types", "Best Styles", "styles", True),
    ("types", "Default Layout", "layouts", False),
    ("types", "Recommended Motion", "motion", True),
    ("types", "Node Kinds", "components", True),
    ("colors", "Style ID", "styles", False),
    # Blank Motion Ref is legal: purely-static states (is-idle, is-frozen, flow-attention)
    # are still whole rows -- stillness is their meaning.
    ("states", "Motion Ref", "motion", True),
]

# --- Cross-reference `path#anchor` rules (contract C3, check V7) -------------
# One declaration per anchor-bearing column, consumed by validate_anchors.check_ref.
#   column   : the cell that names the reference, or None when the row derives it
#   derived  : ref template for rows with no column (formatted with the row's id)
#   base     : directory under the skill root the file part is relative to
#   form     : "md-heading" (`## <anchor>`) or "snippet" (`<!-- snippet: x -->`
#              / `/* snippet: x */`)
REF_RULES = [
    {"domain": "motion", "column": "Recipe Ref", "base": "references", "form": "md-heading"},
    {"domain": "components", "column": "Snippet Ref", "base": "templates", "form": "snippet"},
    {"domain": "payloads", "column": "Glyph Ref", "base": "templates", "form": "snippet"},
    # states.csv names no ref column: the contract is id-derived (code-standards C3).
    {"domain": "states", "column": None, "base": "templates", "form": "snippet",
     "derived": "snippets/state-effects.css#state-{id}"},
]


def anchor_present(text, anchor, form):
    """True when `anchor` exists in `text` in the marker form the rule declares."""
    if form == "md-heading":
        return bool(re.search(rf"^#{{1,6}}\s+{re.escape(anchor)}\s*$", text, re.MULTILINE))
    return f"<!-- snippet: {anchor} -->" in text or f"/* snippet: {anchor} */" in text
